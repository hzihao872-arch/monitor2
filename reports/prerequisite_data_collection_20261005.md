# 隐含前置动作：新增数据采集检查点（2026-10-05）

本文件只记录制样、物理真值、模型运行与输入一致性；新增模型分数尚未分析。旧六段单模板仍只作开发材料。当前编号在每族内固定为 `0001=B+`、`0002=B0`、`0003=U0`、`0004=H-`、`0005=G+`、`0006=N0`。每族六段视频均使用最终目标指令 `Put the blue cube in the green tray.`，15 秒、1 FPS、640×480。

| 场景族 | 机制与位置 | B+ (q_control→q_action, C) | B0 | U0 | H- | G+ / N0 |
| --- | --- | --- | --- | --- | --- | --- |
| `unseen_offset_cell` | 偏置托盘占位 | 0→1, +1 | 0→0, 0 | 1→1, 0 | 1→0, -1 | 成功 / 静止 |
| `unseen_pickup_gate_v2` | 障碍挡蓝块抓取入口 | .15→1, +.85 | .15→.05, -.10 | 1→1, 0 | 1→.15, -.85 | 成功 / 静止 |
| `unseen_mirror_cell` | 镜像托盘占位 | 0→1, +1 | 0→0, 0 | 1→1, 0 | 1→0, -1 | 成功 / 静止 |
| `unseen_left_cell` | 左侧托盘占位 | 0→1, +1 | 0→0, 0 | 1→1, 0 | 1→0, -1 | 成功 / 静止 |
| `unseen_pickup_gate_shifted` | 平移后的抓取入口障碍 | 0→1, +1 | 0→0, 0 | 1→1, 0 | 1→0, -1 | 成功 / 静止 |
| `unseen_rear_cell` | 远端托盘占位 | 0→1, +1 | 0→0, 0 | 1→1, 0 | 1→0, -1 | 成功 / 静止 |

每个物理效应来自同初态分叉、等时长空动作对照与 20 个配对扰动种子。20 个种子是一个场景族内的控制器重复试验，不计作独立场景。`unseen_pickup_gate_v2` 的 B0 另有 40 个配对种子敏感性检查（合计 60）；逐种子记录在该族 `truth` 目录。制样及标签在查看对应模型输出前写入各族 `truth/frozen_test.json`。云端只收到 `model_input` 视频和编号映射，没有收到真值及后续完成视频。

两方法分别使用 TOPReward 官方原版及 Robometer 官方权重加 PR #33 dtype 兼容版，复用现有本地权重和环境。严格未修改 Robometer 原版没有有效推理结果。每段原始逐时输出、完整命令和日志保存在各族 `model_results/topreward` 与 `model_results/robometer_pr33_compat`。`model_results/input_video_sha256.txt` 和各方法的 `decoded_frames.json` 用于跨机器核对输入。所有视频使用预定窗口与未逐视频归一化的原生分数；本检查点不计算事件增量或排序。

预先排除的候选保存在 `experiments/prerequisite_probe/artifacts/unseen_exclusions.json`：初始 offset U0 逆运动学误差超门限；第一版抓取入口场景 B0 失效且准备阶段蓝块位移超门限；反向抓取入口 pilot 亦因蓝块位移及 B0 失效而排除。这些候选均未送入模型评分。后续若分析新增模型输出，应保留所有六族正确、错误及失败结果，不根据分数修改场景、提示或门限。

追加的「搬运通道阻挡」机制经控制器路径检查后未制样：当前固定后续控制器把蓝块提升到 0.20 m 再平移，而红块高度约 0.034–0.048 m，水平通道中的红块不会构成可靠碰撞阻挡。为制造这种效应临时改变后续控制器会改变既有物理真值定义，因此没有把它当作一族有效实验。

数据根目录：`experiments/prerequisite_probe/artifacts/`。共 6 个新场景族、36 段编号视频、72 次方法×视频推理。`python -m experiments.prerequisite_probe.audit_collection` 检查全部六族通过：冻结文件哈希、云端与本地视频哈希、两个方法实际解码的 15 帧哈希、输出文件数量、命令和日志及完整运行标记均一致。机器检查记录：`experiments/prerequisite_probe/artifacts/unseen_collection_status.json`。最后一次查询时服务器仍可 SSH 连接，GPU 无推理进程，数据盘剩余 45 GB；云端结果已回收到本地。
