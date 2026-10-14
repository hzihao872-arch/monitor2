"""Small offline monitor harness. No training or reference labels enter model inputs."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ("H", "C", "P", "G")
VALUES = {"+", "-", "?"}
INVALID = "⊥"
PROMPT_VERSION = "engineering-v2"
FORBIDDEN_ONLINE_KEYS = {"reference", "reference_labels", "ground_truth", "labels", "events", "online_judgment", "success"}


def _contains_forbidden(value):
    if isinstance(value, dict):
        if FORBIDDEN_ONLINE_KEYS.intersection(value):
            return True
        return any(_contains_forbidden(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden(v) for v in value)
    return False


def load_online_track(path):
    track = json.loads(Path(path).read_text(encoding="utf-8"))
    if _contains_forbidden(track):
        raise ValueError("reference/label fields are forbidden in online input")
    if not track.get("trajectory_id") or not track.get("frames") or not track.get("instruction_versions"):
        raise ValueError("track requires trajectory_id, frames, and instruction_versions")
    times = [float(f["time"]) for f in track["frames"]]
    if times != sorted(times) or times[0] < 0:
        raise ValueError("frame times must be sorted and nonnegative")
    versions = [float(v["effective_at"]) for v in track["instruction_versions"]]
    if versions != sorted(versions) or versions[0] != 0:
        raise ValueError("instruction versions must start at zero and be ordered")
    ids = track.get("objects", [])
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("declared object IDs must be nonempty and unique")
    return track


def instruction_at(track, tick):
    return max((v for v in track["instruction_versions"] if float(v["effective_at"]) <= tick), key=lambda v: v["effective_at"])


def frame_packet(track, tick):
    """Nearest-past 1 Hz pool, fixed current/start/t-1/t-5 frame packet."""
    frames = track["frames"]
    pool = []
    for second in range(tick + 1):
        available = [f for f in frames if float(f["time"]) <= second]
        if available:
            pool.append(available[-1])
    if not pool:
        return []
    picked = []
    seen = set()
    for target in (tick, 0, max(0, tick - 1), max(0, tick - 5)):
        available = [f for f in pool if float(f["time"]) <= target]
        if not available:
            continue
        frame = available[-1]
        key = (float(frame["time"]), frame["path"])
        if key not in seen:
            picked.append(frame)
            seen.add(key)
    return picked


def build_prompt(method, instruction, object_ids, memory, tick):
    if method not in {"S0", "S1", "C1"}:
        raise ValueError("unknown method")
    base = (
        f"Current trajectory time: {tick} s. Instruction version {instruction['version']} "
        f"(effective {instruction['effective_at']} s). Original instruction: {instruction['text']}\n"
        f"Declared object IDs: {', '.join(object_ids)}. Use only this instruction and the supplied past/current frames. "
        "Do not invent requirements, treat a prediction as an observed event, or infer continuous compliance from a later final state. "
        "For each object give H (historical event occurred), C (current requirement valid), "
        "P (required process interval compliant), G (overall task complete). "
        "Use + for supported true, - for supported false, ? for insufficient evidence. "
        "The H/C/P/G values must be EXACTLY one of the single-character strings '+', '-', '?' (never true/false, 0/1, field names, or explanations). "
        "Write explanations only inside memory. Output must begin with { and end with }; do not use markdown or code fences. "
        "Exact format example: {\"judgments\":[{\"object_id\":\"...\",\"H\":\"?\",\"C\":\"?\",\"P\":\"?\",\"G\":\"?\",\"evidence_time\":0}],\"memory\":\"...\"}. "
        "Replace ... and 0 as appropriate. Evidence times must not exceed current time."
    )
    if method == "S0":
        return base + "\nMake a direct assessment. Set memory to an empty string."
    if method == "S1":
        return base + ("\nGeneric rolling summary from the same earlier frame packets: " + memory if memory else "") + "\nCheck each condition in the original instruction separately. Keep H, C, P, and G distinct. Record a short generic visual history summary in memory, including uncertainty."
    return base + ("\nPrior evidence ledger from the same earlier frame packets: " + memory if memory else "") + "\nUpdate only conditions affected by new evidence, but let old current evidence expire under occlusion. Preserve confirmed past events, correct prior mistaken judgments when new evidence permits, and allow repair only when the instruction permits it. Record a short source-timed evidence ledger in memory."


def _invalid_judgment():
    return {key: INVALID for key in FIELDS}


def parse_output(raw, object_ids, tick):
    judgments = {oid: _invalid_judgment() for oid in object_ids}
    result = {"judgments": judgments, "memory": "", "parse_status": "invalid_json"}
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return result
    if not isinstance(data, dict) or not isinstance(data.get("judgments"), list):
        result["parse_status"] = "invalid_structure"
        return result
    duplicates = set()
    seen = set()
    for item in data["judgments"]:
        if not isinstance(item, dict):
            continue
        oid = item.get("object_id")
        if oid not in judgments:
            continue
        if oid in seen:
            duplicates.add(oid)
            continue
        seen.add(oid)
        evidence_time = item.get("evidence_time")
        valid_time = evidence_time is None or (isinstance(evidence_time, (int, float)) and not isinstance(evidence_time, bool) and 0 <= evidence_time <= tick)
        if valid_time and all(item.get(field) in VALUES for field in FIELDS):
            judgments[oid] = {field: item[field] for field in FIELDS}
            judgments[oid]["evidence_time"] = evidence_time
    for oid in duplicates:
        judgments[oid] = _invalid_judgment()
    memory = data.get("memory", "")
    result["memory"] = memory if isinstance(memory, str) else ""
    result["parse_status"] = "valid" if all(j["C"] != INVALID for j in judgments.values()) else "partial_invalid"
    return result


def _first_eligible(event):
    tv = float(event["tv_upper"])
    repair = float(event.get("repair_time", math.inf)) if event["side"] == "negative" else math.inf
    for start, end in event["visible_intervals"]:
        q = math.ceil(max(tv, float(start)))
        if q < min(float(end), repair):
            return q, (float(start), float(end))
    return None, None


def _record_lookup(records):
    return {(r["trajectory_id"], int(r["tick"])): r for r in records}


def _value(lookup, trajectory_id, tick, object_id, field="C"):
    return lookup.get((trajectory_id, tick), {}).get("judgments", {}).get(object_id, {}).get(field, INVALID)


def score_bcy(events, records):
    lookup = _record_lookup(records)
    counts = {"negative": {"total": 0, "correct": 0, "false": 0, "unknown": 0, "invalid": 0}, "positive": {"total": 0, "correct": 0, "false": 0, "unknown": 0, "invalid": 0}}
    for event in events:
        q, _ = _first_eligible(event)
        if q is None:
            continue
        side = event["side"]
        if side not in counts:
            raise ValueError("side must be negative or positive")
        value = _value(lookup, event["trajectory_id"], q, event["object_id"])
        c = counts[side]
        c["total"] += 1
        if value == ("-" if side == "negative" else "+"):
            c["correct"] += 1
        elif value == ("+" if side == "negative" else "-"):
            c["false"] += 1
        elif value == "?":
            c["unknown"] += 1
        else:
            c["invalid"] += 1
    neg, pos = counts["negative"], counts["positive"]
    cy_neg = neg["correct"] / neg["total"] if neg["total"] else None
    cy_pos = pos["correct"] / pos["total"] if pos["total"] else None
    return {
        "E_negative": neg["total"], "E_positive": pos["total"],
        "CY_negative": cy_neg, "CY_positive": cy_pos,
        "BCY": (cy_neg + cy_pos) / 2 if cy_neg is not None and cy_pos is not None else None,
        "FC_negative": neg["false"] / neg["total"] if neg["total"] else None,
        "FR_positive": pos["false"] / pos["total"] if pos["total"] else None,
        "Miss0_negative": 1 - cy_neg if cy_neg is not None else None,
        "breakdown": counts,
    }


def score_tick_metrics(labels, records):
    lookup = _record_lookup(records)
    out = {k: 0 for k in ("decidable_denominator", "coverage_numerator", "correct_coverage_numerator", "selective_error_numerator", "online_unknown_denominator", "overconfidence_numerator", "reference_unknown_count", "reference_unknown_hard_claims", "invalid_count")}
    for label in labels:
        val = _value(lookup, label["trajectory_id"], int(label["tick"]), label["object_id"])
        ref, online = label["reference"], label["online"]
        if val == INVALID:
            out["invalid_count"] += 1
        if ref == "?":
            out["reference_unknown_count"] += 1
            out["reference_unknown_hard_claims"] += val in {"+", "-"}
        elif online in {"+", "-"}:
            out["decidable_denominator"] += 1
            out["coverage_numerator"] += val in {"+", "-"}
            out["correct_coverage_numerator"] += val == online
            out["selective_error_numerator"] += val in {"+", "-"} and val != online
        elif online == "?":
            out["online_unknown_denominator"] += 1
            out["overconfidence_numerator"] += val in {"+", "-"}
        else:
            raise ValueError("online label must be +, -, or ?")
    decidable = out["decidable_denominator"]
    selected = out["coverage_numerator"]
    unknown = out["online_unknown_denominator"]
    out["coverage"] = selected / decidable if decidable else None
    out["correct_coverage"] = out["correct_coverage_numerator"] / decidable if decidable else None
    out["selective_error"] = out["selective_error_numerator"] / selected if selected else None
    out["overconfidence"] = out["overconfidence_numerator"] / unknown if unknown else None
    return out


def score_event_delay(event, records):
    q, interval = _first_eligible(event)
    if q is None:
        return {"status": "not_evaluable", "delay_seconds": None, "q_u": None,
                "observation_end_seconds": None, "elapsed_to_end_seconds": None}
    lookup = _record_lookup(records)
    repair = float(event.get("repair_time", math.inf))
    stop = min(interval[1], repair)
    for tick in range(q, math.ceil(stop)):
        if tick >= stop:
            break
        if _value(lookup, event["trajectory_id"], tick, event["object_id"]) == "-":
            return {"status": "detected", "delay_seconds": tick - float(event["tv_upper"]),
                    "q_u": q, "observation_end_seconds": tick,
                    "elapsed_to_end_seconds": tick - float(event["tv_upper"])}
    return {"status": "repair_competing" if repair < interval[1] else "right_censored",
            "delay_seconds": None, "q_u": q, "observation_end_seconds": stop,
            "elapsed_to_end_seconds": stop - float(event["tv_upper"])}


class Budget:
    def __init__(self, total_ticks, calls=1, frames=4, input_tokens=4096, output_tokens=256, memory_tokens=512):
        self.total_ticks = total_ticks
        self.limits = {"calls": calls, "frames": frames, "input_tokens": input_tokens, "output_tokens": output_tokens, "memory_tokens": memory_tokens}
        self.totals = {k: 0 for k in ("calls", "frames", "input_tokens", "output_tokens")}
        self.per_tick = {}

    def add(self, tick, calls, frames, input_tokens, output_tokens, memory_tokens):
        values = {"calls": calls, "frames": frames, "input_tokens": input_tokens, "output_tokens": output_tokens, "memory_tokens": memory_tokens}
        row = self.per_tick.setdefault(tick, {key: 0 for key in values})
        for key, value in values.items():
            row[key] += value
            if key in self.totals:
                self.totals[key] += value
        for key, limit in self.limits.items():
            if row[key] > limit:
                return key
        if self.totals["calls"] > self.total_ticks * self.limits["calls"]:
            return "cumulative_calls"
        if self.totals["input_tokens"] + self.totals["output_tokens"] > self.total_ticks * (self.limits["input_tokens"] + self.limits["output_tokens"]):
            return "cumulative_tokens"
        return None


def _append_jsonl(path, row):
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()


def _append_ledger(path, row):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["run_id", "utc", "kind", "track", "method", "backend", "status", "ticks_recorded", "call_attempts", "input_tokens_known", "output_tokens_known", "elapsed_ms_known", "peak_vram_bytes", "error"]
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fields})


def run_track(track_path, backend, method, outdir, ledger_path, resume=False):
    invocation_start = time.perf_counter()
    if method not in {"S0", "S1", "C1"}:
        raise ValueError("unknown method")
    track_path = Path(track_path)
    track = load_online_track(track_path)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    records_path = outdir / "records.jsonl"
    if records_path.exists() and not resume:
        raise FileExistsError("records already exist; use resume")
    prior = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()] if records_path.exists() else []
    if any(r.get("trajectory_id") != track["trajectory_id"] or r.get("method") != method for r in prior):
        raise ValueError("resume track/method mismatch")
    ticks = list(range(math.floor(float(track["frames"][-1]["time"])) + 1))
    if [r["tick"] for r in prior] != ticks[: len(prior)]:
        raise ValueError("resume records are not a contiguous prefix")
    budget = Budget(len(ticks))
    memory = ""
    for r in prior:
        cost = r["cost"]
        budget.add(r["tick"], cost["calls"], cost["frames"], cost["input_tokens_known"], cost["output_tokens_known"], cost["memory_tokens"])
        if r.get("memory_out") is not None and method != "S0":
            memory = r["memory_out"]
    status, error = "completed", ""
    for tick in ticks[len(prior) :]:
        start = time.perf_counter()
        instruction = instruction_at(track, tick)
        frames = frame_packet(track, tick)
        call_memory = memory if method != "S0" else ""
        prompt = build_prompt(method, instruction, track["objects"], call_memory, tick)
        prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        try:
            result = backend.infer(method, instruction, track["objects"], frames, call_memory, tick)
            parse = parse_output(result["raw"], track["objects"], tick)
            cost = {"calls": 1, "frames": len(frames), "input_tokens_known": int(result["input_tokens"]), "output_tokens_known": int(result["output_tokens"]), "memory_tokens": int(result.get("memory_tokens", 0)), "elapsed_ms_known": 0, "backend_elapsed_ms": result.get("elapsed_ms"), "peak_vram_bytes": result.get("peak_vram_bytes")}
            budget_reason = budget.add(tick, 1, len(frames), cost["input_tokens_known"], cost["output_tokens_known"], cost["memory_tokens"])
            if budget_reason:
                parse["judgments"] = {oid: _invalid_judgment() for oid in track["objects"]}
                parse["parse_status"] = "budget_failure"
            else:
                if method != "S0" and parse["parse_status"] in {"valid", "partial_invalid"}:
                    memory = parse["memory"]
            cost["elapsed_ms_known"] = (time.perf_counter() - start) * 1000
            row = {"trajectory_id": track["trajectory_id"], "method": method, "tick": tick, "instruction_version": instruction["version"], "frame_times": [f["time"] for f in frames], "frame_sha256": [f["sha256"] for f in frames], "prompt_version": PROMPT_VERSION, "prompt": prompt, "prompt_sha256": prompt_sha256, "raw": result["raw"], "judgments": parse["judgments"], "parse_status": parse["parse_status"], "budget_reason": budget_reason, "memory_in": call_memory, "memory_out": memory if method != "S0" else None, "cost": cost}
            _append_jsonl(records_path, row)
        except Exception as exc:
            budget.add(tick, 1, len(frames), 0, 0, 0)
            cost = {"calls": 1, "frames": len(frames), "input_tokens_known": 0, "output_tokens_known": 0, "memory_tokens": 0, "elapsed_ms_known": (time.perf_counter() - start) * 1000, "peak_vram_bytes": None, "telemetry_missing": True}
            row = {"trajectory_id": track["trajectory_id"], "method": method, "tick": tick, "instruction_version": instruction["version"], "frame_times": [f["time"] for f in frames], "frame_sha256": [f["sha256"] for f in frames], "prompt_version": PROMPT_VERSION, "prompt": prompt, "prompt_sha256": prompt_sha256, "raw": None, "judgments": {oid: _invalid_judgment() for oid in track["objects"]}, "parse_status": "runtime_failure", "budget_reason": None, "memory_in": call_memory, "memory_out": memory if method != "S0" else None, "cost": cost, "error": f"{type(exc).__name__}: {exc}"}
            _append_jsonl(records_path, row)
            status, error = "failed", row["error"]
            break
    all_records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
    summary = {"status": status, "error": error, "records": len(all_records), "failed_or_invalid_ticks": sum(r["parse_status"] not in {"valid", "partial_invalid"} for r in all_records), "this_invocation_wall_ms": (time.perf_counter() - invocation_start) * 1000, "cost": {**budget.totals, "elapsed_ms_known": sum(r["cost"]["elapsed_ms_known"] for r in all_records), "peak_vram_bytes": max((r["cost"].get("peak_vram_bytes") or 0 for r in all_records), default=0)}, "records_path": str(records_path)}
    (outdir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _append_ledger(ledger_path, {"run_id": str(uuid.uuid4()), "utc": datetime.now(timezone.utc).isoformat(), "kind": "track_run", "track": str(track_path), "method": method, "backend": type(backend).__name__, "status": status, "ticks_recorded": len(all_records), "call_attempts": budget.totals["calls"], "input_tokens_known": budget.totals["input_tokens"], "output_tokens_known": budget.totals["output_tokens"], "elapsed_ms_known": summary["cost"]["elapsed_ms_known"], "peak_vram_bytes": summary["cost"]["peak_vram_bytes"], "error": error})
    return summary
