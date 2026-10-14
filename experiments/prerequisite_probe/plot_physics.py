"""Plot physical object positions; these are not model reward curves."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .produce import CASES


root = Path("experiments/prerequisite_probe/artifacts/truth")
fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
for case, stem in CASES.items():
    record = json.loads((root / f"{stem}.json").read_text(encoding="utf-8"))
    t = np.array([row["frame"] / 30 for row in record["positions"]])
    red = np.array([row["red"] for row in record["positions"]])
    blue = np.array([row["blue"] for row in record["positions"]])
    tray = np.array([.12, -.12])
    axes[0].plot(t, np.linalg.norm(red[:, :2] - tray, axis=1), label=case)
    axes[1].plot(t, np.linalg.norm(blue[:, :2] - tray, axis=1), label=case)
for ax, title in zip(axes, ("Red block distance from tray centre", "Blue cube distance from tray centre")):
    ax.axvspan(2, 12, color="0.9", zorder=-1)
    ax.set_title(title)
    ax.set_ylabel("distance (m)")
    ax.grid(alpha=.3)
axes[1].set_xlabel("video time (s); shaded: action interval")
axes[0].legend(ncol=6, loc="upper left", fontsize=8)
fig.suptitle("Simulation state only — no reward model predictions")
fig.tight_layout()
fig.savefig(root / "physical_action_curves.png", dpi=160)
plt.close(fig)
