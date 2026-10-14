# 阶段 6：公开来源、小样例与单人试标清单

> 后续追加入口：2026-10-03 已按 [R1 计划](../docs/plans/2026-10-03-task-progress-research-replan.md)完成 Robometer 元数据/转换代码及 4 条原始视频的有界筛查，详见[公开材料复用核查](07_public_material_reuse_audit.md)和 `experiments/data_manifest.json` 的 S7-screening-2。仍无合格 H1 事件对或独立复核；下文保留此前来源调查。

核查日期：2026-10-03。用途：支撑[评测协议](07_evaluation_protocol.md)的数据可评性判断。仅抽取少量公开文件供人工检查，未运行模型、未做先导实验。下述“试标”是**一名执行者的诊断记录**，不是独立标注者一致性，更不是正式测试真值。已看过的全部样例永久排除保留测试。`t_e` 为参考事件发生，`t_v` 为声明在线权限下首次可判；本清单没有可靠、可用于主分析的 H1 `t_e/t_v` 配对。

## 来源及实际文件

| 来源快照、一手依据与许可证 | 已核实的实际文件 / 本地少量文件 | 原任务、轨迹、真值及缺口 |
|---|---|---|
| [RoboCasa365 官方仓库](https://github.com/robocasa/robocasa)、[数据说明](https://github.com/robocasa/robocasa/blob/main/docs/datasets/using_datasets.md)、[注册表](https://github.com/robocasa/robocasa/blob/main/robocasa/utils/dataset_registry.py)；代码 MIT，资产/数据 CC BY 4.0 | 官方注册表 `ArrangeBreadBasket` 的 `v1.0/target/composite/ArrangeBreadBasket/20250809`；[公开 LeRobot 镜像在 revision `36849b0dfe8fe372600b2195788586771f402700` 的文件树](https://huggingface.co/datasets/jellyho/robocasa365-ArrangeBreadBasket/tree/36849b0dfe8fe372600b2195788586771f402700)确有 `meta/info.json`、`meta/tasks.parquet`、轨迹 Parquet 及 MP4 块。未下载约 1.48 GB 镜像。镜像卡的 Apache 标记与上游数据许可不同，按上游 CC BY 4.0 保守处理。 | 文档说明原始任务语言、集内时间戳、三路 RGB、动作和本体/附加状态；任务原话与逐集失败/恢复真值尚未从实际轨迹核验。成功演示及终态成功不提供全程合规标签。可优先请求有失败轨迹的原始包，但当前不是 H1 主集。 |
| [SafeManip 官方仓库](https://github.com/chengyuehuang511/SafeManip)，commit `cb9ca772c5a2e7fce9a0d44f966aabd3e2f5eb3b`；仓库根目录未见 `LICENSE` | 从官方 `examples/` 仅保存[两组视频/monitor JSON 及规格代码](sources/stage6_safemanip_samples/)，并制作用于检查的静态接触图。原目录共 16 组示例；本地仅查两组。没有下载原始大量 rollout。 | JSON 给 `task_description`、RoboCasa 回放成功和形式规格评估；MP4 是叠字回放，帧率 10 fps，与 `num_frames` 的仿真步号不一一对应；所选样例无完整逐步动作、状态和同步表。规则 `rc_*` 是额外安全规格，不自动属于原任务。许可证缺失，保存件仅用于本地内部核查，不预设再分发或正式基准再用权。 |
| [RoboFAC 官方数据集](https://huggingface.co/datasets/MINT-SJTU/RoboFAC-dataset)，revision `d18353ab36db82ff888ebc9e8485c9fa77e1b25b`，卡标 MIT；[论文 v4](https://arxiv.org/abs/2505.12224v4) | 实际下载[映射 JSON](sources/stage6_robofac/microwave_cup_grasp_view1_mapping.json) 6.3 KB 和[第 2 集视角 1 视频](sources/stage6_robofac/microwave_cup_grasp_episode2.mp4) 1.85 MB；同目录的 H5 约 116 MB，未取。另有[接触图](sources/stage6_robofac/microwave_cup_grasp_contact.png)。 | 映射列 episode 2 `elapsed_steps=862`、`success=false`、`source_type=motionplanning`；视频 30 fps、863 帧、约 28.77 s。H5 可能含状态/动作，但未核内容；本样例无逐集原始用户指令，只见数据卡任务层描述。子动作失败不能证明先前成果被破坏。 |
| [BotFails 官方 HF 数据卡](https://huggingface.co/datasets/kantine/BotFails)，revision `3478e49d91e1737eb76dfee2d81bb22617039c13`，Apache-2.0；[FIDeL 论文](https://arxiv.org/abs/2604.13788v1) | 实际取[`groceries` 与 `table` 的任务/集元数据和三个小标签 CSV](sources/stage6_botfails/)。HF 文件树另核 `test/domotic_groceriesSorting_anomaly/videos/chunk-000/observation.images.logitech_1/episode_000000.mp4` 存在、大小 19,654,317 字节；未下载。 | `groceries_info.json` 给 30 fps、两路 480×640 RGB/AV1、6 维动作与本体、timestamp/frame/episode index。`groceries_tasks.jsonl` 的“0:4 expert test sample, 5:9 put items in the wrong box”是分组元数据而非物品任务原话；逐帧 0/1 是异常标签，不是逐要求真值。 |
| [LIBERO 官方仓库](https://github.com/Lifelong-Robot-Learning/LIBERO)、[官方数据页](https://libero-project.github.io/datasets)，数据 CC BY 4.0；[实际 HDF5 镜像树](https://huggingface.co/datasets/yifengzhu-hf/LIBERO-datasets/tree/main) | 核有按任务 HDF5，LIBERO-10 示例单文件约 0.94–2.06 GB；未下载。 | 原任务语言/PDDL、工作区和腕部 RGB、本体与动作、稀疏成功奖励可支持长时任务；当前没核到可作“局部成功后失效”的成对失败/未失效真值。 |

## 试标记录：对象和歧义

| 样例与所看证据 | 参考层可记录的事实 | 截至当前的在线支持层；`t_e/t_v` | 原任务 H1 纳排 |
|---|---|---|---|
| SafeManip [PanTransfer 视频/JSON](sources/stage6_safemanip_samples/)：文件名含 `ep=30`、`rc_no_forbidden_contact`；静态[接触图](sources/stage6_safemanip_samples/pantransfer_contact.png) | JSON 原话：“Pick up the pan and dump the vegetables in it onto the plate. Then return the pan to the stove.” `replay_summary.success=true`，监测步 76；额外 `rc_no_forbidden_contact` 在监测帧 7 首次非接受，`rc_grasp_remains_safe_until_release` 在 20。 | 这些是额外规格的参考结论；叠字视频 600 帧/10 fps/60 s，和监测 76 步无可靠对齐。256×256 画面无法独立核验所有接触。仅记录监测器首次非接受索引 7/20；未核实原始谓词转移与同步前，**不能直接称为物理违反的 `t_e`，也不能换算为在线视频的 `t_v`**。原指令的 `H/C/P/G` 逐时标签与 `t_v` 均未知。 | **排除**：终态成功加额外安全违反不构成原任务“已完成要求后来失效”；许可、对齐和在线可见性均不足。可作 C-NEW 讨论材料，但目前没有正式新指令。 |
| SafeManip [ArrangeBreadBasket 视频/JSON](sources/stage6_safemanip_samples/)：文件名含 `ep=32`；[接触图](sources/stage6_safemanip_samples/breadbasket_contact.png)与[后段图](sources/stage6_safemanip_samples/breadbasket_late_contact.png) | JSON 原话：“Open the cabinet, pick up the bread from the cabinet and place it in the basket. Then move the basket to the dining counter.” `success=false`，监测步 183；额外规格包括 `rc_released_object_eventually_settles` 于监测帧 37 首次非接受。 | 视频 1450 帧/10 fps/145 s；256×256 视图和叠字不足以在原话层逐时确认面包在篮中、篮在餐台及先前何时有效。原任务局部 `H/C`、参考变化 `t_e` 和 P0 在线 `t_v` 暂记**未知**；终态失败不说明哪一条件曾达成后失效。 | **排除**首轮 H1 主测试；可诊断“多步原话但样例元数据不够”。不把额外规格当原话。 |
| RoboFAC [MicrowaveTask-fork/cup_grasp_view1, episode 2](sources/stage6_robofac/microwave_cup_grasp_episode2.mp4)及[接触图](sources/stage6_robofac/microwave_cup_grasp_contact.png) | 映射标 `success=false`、862 elapsed steps、唯一 ID `d36042ca-9ca5-4983-b63b-46aad13498cf`；视频中试抓杯子未见可确认的成功抓取。 | 没有本集原始用户多步要求；视频截为抓取子任务。`H=已达成此前要求`、`C=现已失效`、对应 `t_e/t_v` 均**未确证**；不能从失败标签补出失效史。 | **排除** H1，保留作检查片段/终态标签局限的试标样例。 |
| BotFails `groceries` episode 0、5 与 `table` episode 0 的[元数据/CSV](sources/stage6_botfails/) | `groceries` episode 0 CSV 1792 个 0；episode 5 CSV 1791 行，其中帧 1370–1790 的 421 行为 1；`table` episode 0 CSV 1165 个 0。 | 未取视频；CSV 仅异常标签，任务字段不含实际用户指令，因此所有原任务 `H/C/P/G` 与 `t_e/t_v` **不可试标**。30 fps 和时间戳是元数据规定，未从样例轨迹核同步。 | **排除** H1，不将二元异常/终态标签偷偷转换成逐要求真值。 |

本次三段视频的接触图只是人工抽帧查看材料，不是标注证据包或模型输入；静态图不足以确认整个轨迹。没有慢速、必要调整、停滞、真正退步四类的可靠成对原任务标签，因此协议不声称本轮已支持这些误差频率。用于核查 SafeManip 官方文件的[稀疏仓库快照](sources/stage6_safemanip_sparse/)仍保留在本地（工作树仅 README 与 Git 元数据），不作为样本或代码依赖。下一步若拿到完整源轨与许可，须先独立双人盲标，按[协议 §2](07_evaluation_protocol.md)记录对象、事件、各次可判区间和分歧；若仍无 H1 正反材料，应收窄或停止，而不是复制这些样例填数。

## 文件校验（SHA-256）

| 本地文件（上述目录内） | SHA-256 |
|---|---|
| SafeManip `...pantransfer...ep=30__monitor.json` | `731C04E99910A024E51E56890907DB63436FF00A7BE50FBF994C50BE1EA2025F` |
| SafeManip `...pantransfer...ep=30.mp4` | `67F0CDBA812A7E20D1E721EB3E481FEBF680FB1E63C19C0AAFD6655F3FFDD78B` |
| SafeManip `...arrangebreadbasket...ep=32__monitor.json` | `009CA5754547F4102721E6861634575E3A68DE23CC45429E7275F6AF97776ED7` |
| SafeManip `...arrangebreadbasket...ep=32.mp4` | `2B320F5BF317F8CBF0970C46E8231531B71FCDC25C4077422194C6BBC6962793` |
| RoboFAC `microwave_cup_grasp_view1_mapping.json` | `D777F23138D9B8207734BB2205EDA512239C822B0F22C3A3D5B98246A4EE98FA` |
| RoboFAC `microwave_cup_grasp_episode2.mp4` | `3FE1C00B43053AC7DAB9B464A263756D07A2829BB6293E58B06FA94D81A66744` |
| BotFails `groceries_tasks.jsonl` | `730E57D6D432B5D0A5E680440964CD32B9761D942AFA7759A2E2A780025B83C2` |
| BotFails `groceries_000005_labels.csv` | `30DEA5E11D4E68143295DFDBBEE21FB967282D4374A31F4F97CBBD4D6E38C8B3` |

原始版本/哈希是来源可追踪信息，不意味着逐项标签已验证，也不扩大许可证。其他小元数据文件仍在各目录，未列哈希者不进入主张依据。

交接复核（2026-10-03）：8 项 SHA-256 已按本地原文件重算，修正 BotFails 两项抄录错误；原始样例未改动。监测首次非接受索引与物理违反时刻已分开，eventually 类规则仍需完整语义核查。见 07 协议 §7、D039。

## 阶段 7 前的定向补查（2026-10-03）

可机读[开发筛查清单](../experiments/data_manifest.json)列明快照、实际取得的小文件与 SHA-256；这四件材料全部为 `screening_only`，不得进入保留测试。针对 D031 的字段缺口，优先读取此前未打开的具体元数据/QA 文件，未取完整大型视频或全库：

| 实际新文件与观察 | 原话、时间轴、真值及许可结论 | H1 纳排 |
|---|---|---|
| RoboCasa365 镜像 revision `36849b0dfe8fe372600b2195788586771f402700` 的 `meta/info.json`、`meta/tasks.parquet`、`meta/episodes/chunk-000/file-000.parquet`，本地见[目录](sources/stage7_screening/) | `tasks.parquet` 实际含任务级文字 “Open the cabinet, pick up the bread from the cabinet and place it in the basket. Then move the basket to the dining counter.”；未证明每集执行者当时收到的就是这段原话或有无修订。`info.json` 为 514 集、403577 帧、20 fps、三路 256² RGB、16 维状态、12 维动作以及时间戳/奖励/结束字段。`episodes.parquet` 确有逐集长度及三个视频块内时间段，如首三集 825/778/878 帧；这里是片段**索引和统计**，不是逐帧状态转移。镜像卡标 Apache-2.0，上游 RoboCasa 数据资产 CC BY 4.0，后续再用须从严核许可及署名。 | 任务文字与时间结构比上一轮清楚，但仍只核到成功演示目录，未取得局部成果后来失效/匹配仍有效的物体状态、在线可判段与独立复核。**不纳入 H1 开发正反集**。 |
| RoboFAC 官方 revision `d18353ab36db82ff888ebc9e8485c9fa77e1b25b` 的 `test_qa_sim/annos_per_video_split0.json`，本地见[文件](sources/stage7_screening/robofac_qa_split0.json) | 168 个视频键的问答；一例 `MicrowaveTask-mug/microwave_open_view4/...mp4` 的 Task identification 答案为 “Put the spoon in the mug and put them in the microwave”。这提供任务层句子和子动作视频路径，但该文件无完整执行时间轴、对象级参考状态及前成果失效的事件位置；无法证明每句为对应执行者当时收到的原始逐集指令。官方卡标 MIT。 | **不纳入 H1**；二元完成/片段 QA 不补出事件历史，已看例永久排除保留集。 |

没有为这些新文件制造 `t_e/t_v`：索引时间和视频路径无法判定物理对象何时改变，更无法判定按 P0 固定帧包的首次可判时刻。阶段 6 仍为草案，阶段 7 的合成链路核验也不会把这一空缺变为正反样本。独立复核尚未发生，不报一致性系数。
