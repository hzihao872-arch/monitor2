# 本地五帧 Qwen3-VL-2B D/P/F/H 开发烟测

日期：2026-10-05。**诊断失败，不构成方法效果比较或新方法验证。**使用已看过分数的 `unseen_offset_cell` 六段，全部是开发材料。模型提示只包含 `Put the blue cube in the green tray.` 和当前编号视频的 t=0/3/6/9/14 五帧（256×256）；没有仿真、类别映射、后续视频或旧模型分数。脚本独立读取 `model_input`，先逐条保存原始输出，然后此文才打开编号映射解释。

运行命令（PowerShell，目录 `D:\monitor2`）：

```powershell
.venv\Scripts\python.exe -m experiments.prerequisite_probe.local_candidate_diagnostic --videos experiments/prerequisite_probe/artifacts/unseen_offset_cell/model_input/0001.mp4 --output research/prerequisite_monitor/development/local_2b_smoke.jsonl
.venv\Scripts\python.exe -m experiments.prerequisite_probe.local_candidate_diagnostic --videos experiments/prerequisite_probe/artifacts/unseen_offset_cell/model_input/0002.mp4 experiments/prerequisite_probe/artifacts/unseen_offset_cell/model_input/0003.mp4 experiments/prerequisite_probe/artifacts/unseen_offset_cell/model_input/0004.mp4 experiments/prerequisite_probe/artifacts/unseen_offset_cell/model_input/0005.mp4 experiments/prerequisite_probe/artifacts/unseen_offset_cell/model_input/0006.mp4 --output research/prerequisite_monitor/development/local_2b_smoke_rest.jsonl
```

脚本：`experiments/prerequisite_probe/local_candidate_diagnostic.py`。环境 torch 2.11.0+cu128、transformers 4.57.6、本机 RTX 4060 Laptop 8 GB，BF16、SDPA、贪心、每次最多 360 新 token。配置行保存模型权重 SHA-256、完整 prompt、每段视频 SHA-256、实际五帧像素 SHA-256；代码只解码到 15 帧后固定取五帧。第一次原始 JSONL SHA-256 `1c89d25dbcbd5e309057293233a55cc02b60c4842ff7e391f6dd1e7b1127f9b5`，第二次 `16b37341ea1d1a2d618cc557a91c973297b9310b9fae9aa1a04134e9e56fed84`。运行时仅有 transformers 关于配置中 `temperature/top_p/top_k` 被贪心模式忽略的警告，进程退出码均为 0。

## 全六段原始解析摘要

编号只在本分析使用：0001=B+、0002=B0、0003=U0、0004=H−、0005=G+、0006=N0。表中 `+ / 0 / −` 是模型的 `status`；括号是由其 15 点进度 `median(12:14)-median(0:2)` 算的数值。`invalid` 表示保留原始回答但严格 schema 解析失败，不当成零或弃答。

| 编号 | D 单问 | P 关系 | F 续行 | H=P/F 一致规则 | D2 直接复核 |
| --- | --- | --- | --- | --- | --- |
| 0001 B+ | + (0) | + (+12) | + (+12) | + | invalid：16 点进度 |
| 0002 B0 | + (0) | + (0) | + (0) | + | invalid：16 点进度 |
| 0003 U0 | + (0) | + (+12) | + (+12) | + | invalid：16 点进度 |
| 0004 H− | + (0) | + (+12) | + (+12) | + | invalid：16 点进度 |
| 0005 G+ | + (0) | invalid：引用未给帧 | + (+12) | invalid | invalid：16 点进度 |
| 0006 N0 | 0 (0) | − (0) | + (0) | uncertain | invalid：16 点进度 |

P、F、D 各一次调用；H 复用独立 P/F 两次调用并以一致规则合成；D2 是 D 后同视频复核，最多两次调用。六段合计：D 6/6 解析，3378 输入/1064 输出 token、43.03 秒；P 5/6，3450/1101、41.88 秒；F 6/6，3534/1160、43.83 秒；D2 第二次 0/6，4424/1082、40.86 秒。H 没有额外模型调用；两次调用的实际预算与 D+D2 同数量级，但 token 分配并非完全相等。单次峰值显存 4.12–4.18 GiB。

预处理复核（`0001` 的 D 请求）：processor 返回 `input_ids(1,563)`、`pixel_values(1280,1536)`、`image_grid_thw(5,3)`；五个解码帧像素哈希各异，视觉张量并未被遗漏。这只能排除“完全没送图”，不能证明 256×256 已保留足够几何信息。

**单因素抽帧密度复核**：仅把采样由五帧改为全部 t=0..14 共15帧，仍保持 256×256、模型、提示结构、解码和输出上限；运行 `--frame-ids 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14` 于同一开发族的 `0001/0002/0005`。原始结果 `local_2b_fullframes_pilot.jsonl` SHA-256 `a58d6e49fab095efa693aaaf8392654681caf9673c25562e16ab5ec820996b93`。D/P/F 在 0001 与 0002 仍全报正向，但数值增量全为 0；0005 D/F 正向且数值仍为 0，P 解析失败；D2 仍 3/3 解析失败。单次输入 token 约1269–1502、峰值显存 4.44–4.57 GiB。**增加到全部15帧未修复这一组错误**；不能排除 256 像素、2B 骨干或提示格式的问题。

## 视觉与逻辑错误定位

- `0001` 接触表显示红块从绿托盘内移到外面；P/F 却写 `before=true, after=true`，并误写“绿托盘原本为空”或“红块被移到托盘”。`status=positive` 与自己的前后布尔量矛盾。F 未提出真实替代路线，只复制了类似进度模板。
- `0002` 红块动作后仍占托盘，D/P/F 却全给 positive 状态；即使其数值曲线保持 0，也不能把文字判断当正确。
- `0003` 红块本就在托盘外，P/F 给正向且机械地输出 `[0,1,...,14]`；`0004` 红块从外进入托盘，P/F 仍同样正向。它们没有读出关系变化的符号。
- `0005` 蓝块被放入托盘，D 的 status 正向而 15 点进度全 0，P 引用了非采样帧导致解析失败；`0006` 静止，P 反判负向，F 反判正向。G+/N0 锚点不稳定。
- D2 六段都输出 16 个数值而非要求的 15 个，不能作为同预算有效基线。原始回答均保留，不能通过静默截断让它“通过”。

**阶段决定**：停止扩大到剩余五族或旧六段，不因单家族的输出去调 prompt/阈值。此 2B 五帧及15帧烟测均未通过“可解析中间记录、G+/N0 锚点、同预算 D2 可比”的本地退出条件。因此目前没有 P/F/H 效果结论，也不能冻结新盲测或开始租机验证。更强同骨干比较仍需先解决视觉关系读取、输出自洽和 D2 schema；若提高分辨率或更换骨干，另升版并完整重跑全部开发例，不选择性补跑。

下一步唯一入口：在不读取开发标签作提示的前提下，检查采样图像实际送入 VLM 的预处理是否保留托盘和蓝块；再预先登记一版通用格式修正/预算，重做 G+/N0 和 B0/H− 烟测。未解决反例：2B 失败可能是小骨干或低分辨率导致，不能据此否证强模型 P/F/H 或 ARS。

## 预登记 v2 视觉输入审计（结果未查看时写定）

原始视频解码均为 640×480；v1 把每帧压成 256×256，改变了物体宽高比例。v2 仅把相同五帧改为 **512×384**，保持 4:3 比例；模型、D/P/F/D2/H 提示、贪心解码、360 输出 token、真值隔离、严格解析及六个编号视频均不变。完整跑六段，不挑选先前错误例。主判定仍为状态/前后关系/证据/15点进度自洽、D2 可解析、B+/B0/U0/H− 排序及 G+/N0 锚点；失败照样保留。如果显存错误，记为运行失败，不降低分辨率择优重试。本检查只定位 v1 的视觉预处理限制，仍属开发诊断，不是新方法盲测。

运行命令：`.venv/Scripts/python -m experiments.prerequisite_probe.local_candidate_diagnostic --videos experiments/prerequisite_probe/artifacts/unseen_offset_cell/model_input/0001.mp4 .../0006.mp4 --output research/prerequisite_monitor/development/local_2b_512x384.jsonl --image-size 512x384`（中间四个为同目录 0002–0005）。脚本 `py_compile` 通过，六段全写入，进程退出码0；JSONL SHA-256 `3a7e5f03cfe57591bac2a449b115e4041bdacc8f2b5e96c9f1a0c4f1849fe860`。输出峰值 VRAM 4.51 GiB。P/F/H 与 D/D2 用同模型、同五帧；token 实耗仍不完全相等，不能称严格等预算有效性比较。

| 条件 | D | P | F | H | D2 |
| --- | --- | --- | --- | --- | --- |
| B+ 0001 | 负，曲线Δ0 | invalid：引了未提供帧 | 正，Δ0 | invalid | invalid：进度长度错 |
| B0 0002 | 零，Δ0 | 负，Δ0 | 正，Δ0 | uncertain | 零，Δ0 |
| U0 0003 | 正，Δ0 | 正，Δ0 | invalid：进度长度错 | invalid | invalid |
| H− 0004 | 正，Δ0 | invalid：引了未提供帧 | 正，Δ12 | invalid | invalid |
| G+ 0005 | 正，Δ0 | 正，Δ0 | 正，Δ12 | 正，Δ6 | invalid |
| N0 0006 | 零，Δ0 | 负，Δ0 | 正，Δ0 | uncertain | invalid |

所有 D 均为 `before=true, after=true`，包括 B+ 和 G+；这是模型自己输出的关系字段，不能被正负状态覆盖。P 在 B+ 与 H− 两段列出 `[0,...,14]` 作为证据，尽管只送入五帧；保留为**无效证据引用**，不静默截取。F 在 H− 仍给正向且曲线 `0..14`，在 N0 也给正向；D2 仅 1/6 格式有效。较清晰的 G+ 判断与托盘/红块的错认并存。此分辨率实验未使本地阶段门槛通过，也没有证明更大骨干必然失败。后续不在这些输出上逐例调提示或阈值；应先确立一个能自洽描述前后关系、并与同预算直接提示共同可解析的强骨干，再考虑冻结新集。
