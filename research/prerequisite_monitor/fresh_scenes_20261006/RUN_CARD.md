# 本地运行卡（2026-10-06，上海时间）

工作目录 `D:/monitor2`。根目录执行 `git status --short --branch` 返回 1：`fatal: not a git repository`。版本身份以 `manifest.json`、`design.json.sha256`、文件 SHA-256、运行日志与两个来源仓库提交记录表示。未连接服务器，未下载权重，未调用模型推理。

## 环境

- Python：`D:/monitor2/.venv/Scripts/python.exe` 3.12.3。
- ManiSkill 3.0.1；SAPIEN 3.0.3；PyTorch 2.11.0+cu128。
- ffmpeg / ffprobe 7.1.1。
- 开始盘点时 D 盘可用空间 66,634,153,984 字节。
- TOPReward 来源仓库提交 `4877a0ee5098cbec18485125466631b1dcc4a573`；Robometer 来源仓库提交 `352d160389daa964788de1ec933d1925f3a6de4f`。这里只用于接口和解码预检，没有加载模型。
- 仿真初态种子 `20261006`；匿名映射固定种子：A `20261007`，B `20261008`；成对扰动种子 `20261006`、`20261007`、`20261008`；承托面静态搜索种子 `20261006`。

## 实际命令、退出码和原始日志

| 命令（均从 `D:/monitor2` 执行） | 退出码 | 输出 |
| --- | ---: | --- |
| `& '.\.venv\Scripts\python.exe' -m unittest discover -s experiments/prerequisite_probe/tests -p 'test_fresh_prerequisite_*.py' -v` | 0 | [tests_final.txt](run_logs/tests_final.txt)：21 tests，OK |
| `& '.\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.fresh_prerequisite.generate --mechanism access_gate --output research/prerequisite_monitor/fresh_scenes_20261006/access_gate/dev_v1` | 0 | [access_generate_dev_v1.txt](run_logs/access_generate_dev_v1.txt)，但 `R` 只在一帧完全开放，整版排除 |
| `& '.\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.fresh_prerequisite.generate --mechanism support_surface --output research/prerequisite_monitor/fresh_scenes_20261006/support_surface/dev_v1` | 0 | [support_generate_dev_v1.txt](run_logs/support_generate_dev_v1.txt)，同样排除 |
| `& '.\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.fresh_prerequisite.generate --mechanism access_gate --output research/prerequisite_monitor/fresh_scenes_20261006/access_gate/dev_v2` | 0 | [access_generate_dev_v2.txt](run_logs/access_generate_dev_v2.txt) |
| `& '.\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.fresh_prerequisite.generate --mechanism support_surface --output research/prerequisite_monitor/fresh_scenes_20261006/support_surface/dev_v2` | 0 | [support_generate_dev_v2.txt](run_logs/support_generate_dev_v2.txt) |
| `& '.\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.fresh_prerequisite.audit --root research/prerequisite_monitor/fresh_scenes_20261006`（首次） | 1 | [audit_dev_v2.txt](run_logs/audit_dev_v2.txt)：审计器误读本地解码附加字段，且亮度阈值漏掉半透明墙后的深蓝块；修正审计器，没有改视频 |
| 相同审计命令（重跑） | 0 | [audit_dev_v2_recheck.txt](run_logs/audit_dev_v2_recheck.txt)：`status=pass`、`issues=[]` |
| 相同审计命令（封存前最终复核） | 0 | [audit_final.txt](run_logs/audit_final.txt)：`status=pass`、`issues=[]` |
| `& '.\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.fresh_prerequisite.support_surface --output research/prerequisite_monitor/fresh_scenes_20261006/support_surface/dev_v2/physics/static_candidate_search.json` | 0 | [support_static_search.txt](run_logs/support_static_search.txt)：50,000 次，阻挡态合格承托候选 0 |
| `& '.\.venv-robometer\Scripts\python.exe' -m tmp.fresh_robometer_decode` | 0 | [robometer_native_decode.txt](run_logs/robometer_native_decode.txt)：18 段 × 15 帧与清单哈希一致；没有加载权重 |
| `& '.\.venv\Scripts\python.exe' -m tmp.fresh_full_frame_sheets` | 0 | [full_frame_sheets.txt](run_logs/full_frame_sheets.txt)：每段 15 帧全帧接触图 |
| `& '.\.venv\Scripts\python.exe' -m tmp.fresh_confounds` | 0 | [confounds.txt](run_logs/confounds.txt)：从 30 FPS 状态流提取九段蓝块/机器人轨迹与遮挡代理量 |
| `& '.\.venv\Scripts\python.exe' -c "import zipfile; from pathlib import Path; r=Path('research/prerequisite_monitor/fresh_scenes_20261006'); [(lambda z,m: print(m,len(z.namelist()),sorted(z.namelist())))(zipfile.ZipFile(r/m/'dev_v2/reviewer_only.zip'),m) for m in ('access_gate','support_surface')]"` | 0 | [reviewer_zip_check.txt](run_logs/reviewer_zip_check.txt)：每包仅 9 个数字视频与 3 个空白审读文件 |

以下四次都使用 `-m experiments.prerequisite_probe.run_native_single_scene_pilot --dry-run`，`--model-path .models` 仅作为参数被记录，未读取配置或权重。各日志为空表示命令成功无标准输出；各 `native_calls.jsonl` 含 1 条配置和 9 条视频输入、0 条模型结果。

| `--method`、`--input-dir`、`--repo`、`--output-dir` | 退出码 | 日志 |
| --- | ---: | --- |
| `TOPReward`, `research/prerequisite_monitor/fresh_scenes_20261006/access_gate/dev_v2/model_input`, `research/sources/TOPReward`, `research/prerequisite_monitor/fresh_scenes_20261006/access_gate/dev_v2/validation/dry_run_topreward` | 0 | [access_gate_dry_run_topreward.txt](run_logs/access_gate_dry_run_topreward.txt) |
| `Robometer`, `research/prerequisite_monitor/fresh_scenes_20261006/access_gate/dev_v2/model_input`, `research/sources/robometer`, `research/prerequisite_monitor/fresh_scenes_20261006/access_gate/dev_v2/validation/dry_run_robometer` | 0 | [access_gate_dry_run_robometer.txt](run_logs/access_gate_dry_run_robometer.txt) |
| `TOPReward`, `research/prerequisite_monitor/fresh_scenes_20261006/support_surface/dev_v2/model_input`, `research/sources/TOPReward`, `research/prerequisite_monitor/fresh_scenes_20261006/support_surface/dev_v2/validation/dry_run_topreward` | 0 | [support_surface_dry_run_topreward.txt](run_logs/support_surface_dry_run_topreward.txt) |
| `Robometer`, `research/prerequisite_monitor/fresh_scenes_20261006/support_surface/dev_v2/model_input`, `research/sources/robometer`, `research/prerequisite_monitor/fresh_scenes_20261006/support_surface/dev_v2/validation/dry_run_robometer` | 0 | [support_surface_dry_run_robometer.txt](run_logs/support_surface_dry_run_robometer.txt) |

实际 dry-run 命令形式为：

```powershell
& '.\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.run_native_single_scene_pilot --method <TOPReward|Robometer> --input-dir <上表路径> --repo <上表路径> --model-path .models --output-dir <上表路径> --dry-run
```

所有生成文件是在模型输出之前制成。`dev_v1` 连同失败原因、原始视频和源码快照保留；`dev_v2` 用独立非空目录整套重录。`support_surface/dev_v2/physics/necessity_report.json` 的一个派生字段把导轨中心 70 mm 误标为内缘；[necessity_erratum.md](support_surface/dev_v2/physics/necessity_erratum.md) 与修正报告保留原值并纠正为 62 mm，几何与视频没有变化。

## A 组盲审后纠错

读者首次原答和三段未揭盲补充已分别封存于 [A 审读记录](access_gate/dev_v2/reviews/first_answer_assessment.md)。执行者把读者的“不能判断可以通过”误读为视觉上无法判断，曾启动 `access_gate/dev_v3` 的本地生成命令；用户澄清读者意为“移动后开口仍不足以让蓝块通过”后，命令在 E、S 两段完成、第三段录制中被人工中断（退出码 1）。[命令原始输出](run_logs/access_gate_dev_v3.txt)和[中止目录说明](access_gate/aborted_dev_v3_due_to_misread/README.md)保留。没有生成完整九段、模型 ZIP、审读包或模型结果。生成代码与 `design.json` 已恢复到 A `dev_v2`，四个关键源码文件与中止前快照逐字节哈希相同，设计文件与原 `design.json.sha256` 相符。

恢复后重新运行上述 21 项本地测试，退出码 0、`OK`；重新运行 `fresh_prerequisite.audit --root research/prerequisite_monitor/fresh_scenes_20261006`，退出码 0、`status=pass`、`issues=[]`，A/B 各九段。中止目录不是候选场景；A `dev_v2` 维持 G1 候选，B 盲审仍待回传。

B 组随后由用户在本对话转录读者的[首次九行回答](support_surface/dev_v2/reviews/reader1_first_answer_chat_transcription_20261006.txt)，用户确认读者未接触场景真值、代码、模型分数或执行者对黄色板面的解释。[揭盲比对](support_surface/dev_v2/reviews/first_answer_assessment.md)显示九段主要分类与记录一致。用户又发送[三条补充文字](support_surface/dev_v2/reviews/reader1_supplement_user_transcription_20261006.txt)：认为均无替代路线、S 的黄板未到目标区、R 在第 9/12 秒可见改变/恢复。补充与首次回答分开封存，用户确认其为读者未揭盲原话；A、B 两组均作为 G1 候选移交原对话审查。

最终复验：上述 21 项单元测试退出码 0、`OK`，原始输出见 [tests_after_blind_review.txt](run_logs/tests_after_blind_review.txt)；`fresh_prerequisite.audit --root research/prerequisite_monitor/fresh_scenes_20261006` 退出码 0、`status=pass`、`issues=[]`，A/B 各九段，原始输出见 [audit_after_blind_review.txt](run_logs/audit_after_blind_review.txt)。随后重新执行 `freeze --write` 与 `freeze --verify`，以最终 `manifest.json` 和 `manifest.sha256` 为准。

封存命令：`& '.\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.fresh_prerequisite.freeze --root research/prerequisite_monitor/fresh_scenes_20261006 --write`，退出码 0；随后把 `--write` 改为 `--verify`，退出码 0。两条命令只遍历和哈希本地文件，不调用模型或服务器。
