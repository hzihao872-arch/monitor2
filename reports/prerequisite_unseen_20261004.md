# 隐含前置动作：未见几何模板的受控测试

日期：2026-10-04。状态：两个新的完整六类场景族已制样、物理核验、冻结，并在现有 SeetaCloud RTX 5090 上完成 TOPReward 官方原版与 Robometer 官方权重加 PR #33 dtype 兼容版推理。Robometer 严格未修改原版仍只有先前的 dtype 运行失败，不能把兼容版结果写成原版结果。

## 场景、视频与预先冻结

| 场景族 | 机制与编号视频 | 物理结果（20 个配对种子：`q_control → q_action`; `C`） |
|---|---|---|
| `unseen_offset_cell` | 新的蓝块/托盘相对位置；红块占据放置区。`0001` B+、`0002` B0、`0003` U0、`0004` H−、`0005` G+、`0006` N0。 | B+ `0/20→20/20; +1.00`；B0 `0→0; 0`；U0 `20→20; 0`；H− `20→0; −1.00`；G+ 视频内成功，N0 静止。 |
| `unseen_pickup_gate_v2` | 托盘本来空着；红块紧邻蓝块抓取侧，妨碍冻结控制器夹取。相同六个编号/条件。 | B+ `3/20→20/20; +0.85`；B0 `3/20→1/20; −0.10`；U0 `20→20; 0`；H− `20→3/20; −0.85`；G+ 视频内成功，N0 静止。B0 在无效门槛边缘；额外 40 个配对种子为 `0→2`，合并 60 种子为 `3→3; C=0`，仅作物理敏感性检查。 |

每个场景族各六段 640×480、15 秒视频：30 FPS 母版 450 帧，模型只收固定抽出的 1 FPS、15 帧。B+/B0 共用动作前仿真快照；H−/U0 与各自等时长空动作对照配对。后续控制器只操作蓝块，15 秒准备加 15 秒继续，20 个种子共享一个几何场景，**不是 20 个独立场景**。两族各 11 项自动验证通过；主视角逐帧接触表显示目标、障碍、托盘及终态。没有第二名独立视觉复核者；Codex 的视觉检查知道条件映射，不称盲审。

两族的[冻结记录](../experiments/prerequisite_probe/artifacts/unseen_offset_cell/truth/frozen_test.json)与[抓取入口冻结记录](../experiments/prerequisite_probe/artifacts/unseen_pickup_gate_v2/truth/frozen_test.json)均早于任何新视频模型评分，包含指令、窗口、阈值、排除规则、代码和视频哈希、物理标签。Windows 换行转换曾使两个 `.sha256` 旁注与文件字节不符；评分后只把旁注改为实际冻结文件字节的 SHA-256，**没有改冻结 JSON、视频或标签**。旧六段仅作开发材料。模型入口没有读取 `truth/`、后续成功视频或条件代号。

## 原生分数与成对判断

主数值是原生 1 FPS 点上 `median(t=12,13,14)−median(t=0,1,2)`；未逐视频归一化。TOPReward 数值是原生前缀 log score，Robometer 是原生 progress，两者量纲不同。括号内的 B+ 对 B0/U0、H− 对 N0 是**同一方法内增量差**；H− 越低越合乎物理方向。

| 方法 | 场景族 | B+ | B0 | U0 | H− | G+ | N0 | B+−B0 / B+−U0 | H−−N0 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TOPReward 原版 | offset cell | −3.500 | −0.750 | −2.125 | −2.500 | +8.625 | −1.250 | −2.750 / −1.375 | −1.250 |
| TOPReward 原版 | pickup gate | −2.250 | +1.625 | −1.750 | +2.000 | +10.125 | −1.125 | −3.875 / −0.500 | +3.125 |
| Robometer PR #33 dtype 兼容版 | offset cell | +0.0883 | +0.4971 | +0.5682 | +0.5556 | +0.7329 | +0.1793 | −0.4088 / −0.4800 | +0.3763 |
| Robometer PR #33 dtype 兼容版 | pickup gate | +0.2402 | +0.0536 | +0.1479 | +0.1642 | +0.7468 | +0.1954 | +0.1866 / +0.0924 | −0.0313 |

TOPReward 在**两种未见几何/机制**都把有效 B+ 排在 B0 和 U0 后；G+ 两族明确正向。它在 offset cell 给 H− 比 N0 更低的增量，在 pickup gate 却给 H− 更高增量。Robometer 兼容版在 offset cell 重复开发集的 B+ 逆向排序及 H− 误升；但在 pickup gate **正确**把 B+ 排在 B0/U0 之前，不能筛掉这个相反结果。其 pickup gate H− 比 N0 低 `0.0313`，方向正确但幅度很小。

把后窗口移到 11–13 秒或 13–14 秒、前窗口改为 0–1 秒或 1–3 秒，TOPReward 两族 B+ 逆向排序、Robometer offset cell 的逆向排序、Robometer pickup gate 的 B+ 正向排序均不翻转。Robometer pickup gate 的 H− 对 N0 在 11–13 秒后窗口**翻成错误方向**，因此不能称它稳定识别妨碍动作。完整逐点、success head、成对差值和四种边界窗口见[机器可读分析](../experiments/prerequisite_probe/artifacts/unseen_analysis_native.json)。开发集只有一个 N0，不足以固定自然噪声阈值；不报告阈值化漏判率或误奖率。

## 与旧六段及排除样本的关系

旧开发模板中，TOPReward B+ `−5.875` 低于 B0 `−2.500`/U0 `−1.750`，H− 对 N0 方向正确；Robometer 兼容版 B+ `+0.1022` 低于 B0 `+0.2693`/U0 `+0.1479`，H− 错误升高；两者 G+ 都正向。新 offset cell 与这组方向一致，但它仍是相近的“红块占托盘”机制。新的 pickup gate 提供关键反例：Robometer B+ 排序恢复正确，TOPReward 的 B+ 逆向排序继续出现。由此能说 TOPReward 在本次两个受控场景族中重复出现错例，不能据此推断所有场景的普遍能力缺陷；对 Robometer 更不能说跨机制稳定漏判。

[排除登记](../experiments/prerequisite_probe/artifacts/unseen_exclusions.json)保留了两种未送分候选：offset cell 初版 U0 终点 IK 误差 0.028 m，超过 0.025 m 门槛；pickup gate 初版虽录完六段，但 B0 `C=+1` 且 B+/B0/H− 准备时蓝块位移超过 5 mm，故在评分前排除。后者视频、真值和日志留在 `artifacts/unseen_pickup_gate/`。没有从新模型输出倒推改场景、提示或门槛。旧的窄口方案因主视角不可见蓝块而排除，仍只属开发历史。

## 复现材料、版本与运行状态

- [offset cell 原始文件](../experiments/prerequisite_probe/artifacts/unseen_offset_cell/)和[grab gate 原始文件](../experiments/prerequisite_probe/artifacts/unseen_pickup_gate_v2/)：`raw/`、`model_input/`、`truth/oracle_checks.jsonl`、`truth/actual_frames.json`、`truth/contact_sheet.png`、`model_results/`。两方法各族六份原生输出；Robometer 每段另有 success head `.npy`、命令和日志。远端输入视频 SHA-256 与冻结视频一致，两入口各族 6×15 张实际解码 RGB 帧哈希逐帧相同。
- [云端批脚本](../experiments/prerequisite_probe/cloud_run_unseen_family.sh)和各族 `model_results/cloud_run.log` 记录完整命令、环境版本、PR #33 改动与起止时间。TOPReward 官方提交 `4877a0ee5098cbec18485125466631b1dcc4a573`、Qwen3-VL-8B-Instruct revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`；Robometer 原仓库提交 `352d160389daa964788de1ec933d1925f3a6de4f`、官方权重 revision `beef63bc914c5c189329d49c6d712d96d632aa34`、单列 PR #33 dtype 补丁。权重沿用旧[官方哈希清单](../experiments/prerequisite_probe/artifacts/model_results/official_weight_hashes.json)，没有重下载。
- 本次 24/24 段推理有原始数组，未出现新模型前向失败。此前 Robometer **严格未修改原版**的 BF16/FP32 dtype 错误仍见[旧失败日志](../experiments/prerequisite_probe/artifacts/model_results/robometer/0001.official_dtype_fail.log)，其状态仍是“尚无该模型结果”。
- 云端为用户既有 SeetaCloud RTX 5090 32 GB 实例，未新租或购买。起初默认 KEX 握手超时，强制 `curve25519-sha256` 后可达；新公钥虽在当前容器且指纹匹配仍被 SSH 拒绝，最终使用用户提供的现有密码认证。取回归档后于 23:25（上海时间）核实实例在线、GPU 0 MiB/0% 占用、无推理进程；本次临时公钥已从 `authorized_keys` 移除。[本地运行状态](../experiments/prerequisite_probe/artifacts/unseen_run_status.json)保留核查时间与归档 SHA-256。实例计费是否停止以平台页面为准。

## 尚未排除的解释

这些分数也可能受训练分布、固定主视角遮挡、目标动作比准备动作显眼、1 FPS 抽帧、事件窗口和原生分数漂移影响。物理“必要”只相对于冻结蓝块续行控制器与预算；pickup gate 的空动作仍有 `3/20` 成功，说明并非几何上绝对不可抓。每族只有一套视频，缺第二名独立视觉复核者、多姿态可达性证明和更多独立场景，不能外推总体错误率或断言模型机制。公开机器人视频若无同初态反事实仍只能作定性材料，本次没有混入主表。
