# 阶段 7：最小工程核验与开发先导状态

日期：2026-10-03（Asia/Shanghai）。依据[正式计划](../docs/plans/2026-10-02-task-progress-research-plan.md)、[S6-draft-4 协议](07_evaluation_protocol.md)及 D017、D024—D039。本报告把**工程运行**、**真实材料诊断**和**H1 开发先导**分别记录。阶段 6 仍是草案；没有因程序运行成功而补出 H1 数据。

## 1. 实际结论与阶段门槛

| 工作 | 本轮结果 | 可作的结论 |
|---|---|---|
| 定向数据补查 | 实际读取 RoboCasa365 的任务/逐集元数据和 RoboFAC 的补充任务 QA 小文件；哈希、来源、许可与纳排见[试标清单](07_source_and_trial_annotations.md)和[机读清单](../experiments/data_manifest.json)。 | 原话与时间结构更明确；仍没有经独立复核的原任务局部成果失效/仍有效正反事件，也没有相应 P0 可判区间。 |
| 本地模型核验 | 精确 Qwen3-VL-2B-Instruct revision `89644892e4d85e24eaac8bacfd4f463576704203`、BF16、同 revision 处理器可在 RTX 4060 Laptop GPU 上加载；单图和四帧都完成推理。 | 只证明所用本机/环境的加载、输入展开及小样例资源可行，不证明大规模吞吐或机器人判断正确。 |
| 最小评测链路 | 在线/参考字段隔离、固定帧包、提示与状态通路、解析、预算、逐钟/整轨日志、BCY/辅助率/延迟与修复截尾已编码；13 项语义测试通过。S0/S1/文本台账 C1 各在同一隔离合成轨迹上完成两个真实模型钟。 | 程序路径和三种输出接口可工作；夹具没有 H1 参考标签，不能形成 C1−S1 效果比较。 |
| H1 开发先导 | **未运行**。没有正反可判开发材料及第二人独立复核。 | 不报 BCY、置信区间、方差、样本规模或 H1 支持/否定。保留测试未解封，阶段 7 未完整完成，不具备阶段 8 条件。 |

## 2. 真实数据诊断与阶段 6 收尾

补查的是上一轮来源中尚未打开、最可能补齐字段的小文件，没有重做文献综述或下载整库。RoboCasa365 镜像的 `tasks.parquet` 实际给出任务级文字 “Open the cabinet, pick up the bread from the cabinet and place it in the basket. Then move the basket to the dining counter.”；**它未证明每集执行时收到的原话及修订**。`info.json` 和 `episodes.parquet` 给 514 集、20 fps、三相机及每集视频块时间段、动作/状态字段。来源是公开 LeRobot 镜像；[镜像卡](https://huggingface.co/datasets/jellyho/robocasa365-ArrangeBreadBasket)标 Apache-2.0，上游 [RoboCasa 仓库](https://github.com/robocasa/robocasa)对数据资产另标 CC BY 4.0，未来再用保守按上游许可及署名核对。元数据没有局部成果先达成后失效的参考谓词或 P0 可判段，成功演示/终态奖励也不能提供全程保持真值。

RoboFAC 官方 `test_qa_sim/annos_per_video_split0.json` 的 168 项中确有任务层句子及子动作视频路径；它不能证明对应执行轨迹收到的逐集原话，也无完整时间轴和对象失效事件。此前 SafeManip 的 `rc_*` 是额外安全规格，监测首次非接受索引未与物理变化/视频同步；BotFails 二元异常、RoboFAC 失败片段和 RoboCasa 终态标签均不补出 H1 历史。所有已看样例列 `screening_only`，永久排除保留测试。试标仍只是一人诊断，没有第二标注者或一致性结果。

**最小材料需求**：同一原任务族下至少一条“已达成局部条件后失效”和一条匹配“仍有效”的完整轨迹；提供执行时原始指令及修订、同步视频/动作或对象状态参考、来源与允许研究再用范围，并能按 P0 固定帧包标 `t_e/t_v` 及多段可判区间。第二名独立标注者须盲标后仲裁根本语义/同步分歧。若只能新采集，可另议在执行**之前**对所有方法公布 “放入篮后搬运期间保持面包在篮中” 的 `C-NEW` 指令并采正反轨迹，独立报告；不能倒写为原 RoboCasa 任务要求，本轮未采集或改题。

## 3. 模型、环境、输入与资源实测

本机 Windows 11、Python 3.12 项目 `.venv`、NVIDIA RTX 4060 Laptop GPU（8188 MiB VRAM，driver 595.97）；预检 D 盘约 95.23 GiB 可用。所需公开权重约 4,255,140,312 字节，选取模型/处理器文件合计约 4,266,648,961 字节；官方 CUDA PyTorch wheel 2,753,189,216 字节，另需解压安装空间。10 个已下载模型/处理器文件的本地 HF metadata 均指向同一 revision；`model.safetensors` 本地 SHA-256 `7de1838c87a5349b016c26a1c3f7d2bc400a3d485f95ef39a7059ffd734977a0` 与 [官方 revision 文件元数据](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct/tree/89644892e4d85e24eaac8bacfd4f463576704203)一致。模型卡为 Apache-2.0；[官方用法](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct)给 Transformers 加载接口。实际环境：`torch 2.11.0+cu128`、`torchvision 0.26.0+cu128`、`transformers 4.57.6`、`Pillow 12.1.1`，完整[环境锁定清单](../experiments/environment-freeze.txt)和[工程配置](../experiments/config_stage7.json)留存。均装在项目 `.venv`，未训练、未租算力、未用付费 API。

最初通过 PyTorch 索引安装 torch 时下载的 wheel SHA-256 与索引要求值不符，安装被拒；随后从官方 wheel URL 本地续传，核得要求的 `7c78215c3af4f62e63f2b2e360f1722fc719b0853c7ac22666483d9810613a4c` 后才安装。第一次烟测因缺 `torchvision` 在 `AutoVideoProcessor` 初始化失败；按 [PyTorch 官方匹配版本](https://pytorch.org/get-started/previous-versions/)补 `0.26.0+cu128` 后原 BF16 配置通过。失败与后续成功均见[运行台账](../experiments/run_ledger.csv)；没有降精度、换权重或扩大资源。

烟测图片是脚本自制普通 256×256 工程图，不是 H1 轨迹。每次至多一次模型调用，实测如下；GPU 峰值为 PyTorch `max_memory_allocated`，不是整机 VRAM 占用。延迟是这几次本机调用的记录，**不外推吞吐**。

| 工程输入 | 处理器输入 token | 生成 token | 适配器内用时 | PyTorch GPU 峰值 |
|---|---:|---:|---:|---:|
| 单图 | 256 | 64（烟测上限） | 3399 ms | 4,322,736,128 B |
| 四图 | 475 | 64（烟测上限） | 2633 ms | 4,392,874,496 B |

初版共享格式提示 `engineering-v1` 的模型输出含代码围栏、布尔/数字/字段名字等非法值；严格解析均保留原文并记 `⊥`，未偷偷转成正确标签。为检查接口而改为共同 `engineering-v2`，强调纯 JSON 和仅单字符 `+/-/?`，对三法相同；隔离夹具的三法两钟输出均可解析。提示改动仅能说明格式接口改进，不能用旧新合成输出作 H1 证据。

## 4. 评测实现和工程运行

[核心链路](../experiments/monitor_eval.py)将在线轨迹清单限制为指令版本、对象 ID、时间与帧路径/哈希；参考与在线可判标签的[独立 schema](../experiments/label_schema_v1.json)尚未填 H1 实例。运行时只把当前生效指令和≤当前钟的固定帧包交给后端；输出 JSON 按对象记录 H/C/P/G 的 `+/-/?/⊥`、原文、证据时间、摘要/台账入出、调用、实际 token、帧与累计开销。S0 不续记忆；S1 使用同源滚动普通摘要；C1 最小实现仅有同源**文本证据台账**与逐项更新提示，不等于已验证结构化状态机或已批准架构。[模型适配器](../experiments/qwen_backend.py)使用相同 checkpoint/处理器、BF16、SDPA、256² RGB，输入 token 为处理器展开后 `input_ids` 长度。S2 暂未加入：没有合法 H1 先导可进行等资源反证，下一步若材料达标须补 S2 与 S1 的合理开发，再比较。CaM/DoReMi 等原法接口、信息权限和数据不同，本轮不强行实现或映射细粒度输出。

[语义测试](../experiments/tests/test_monitor_eval.py)及[图像消息测试](../experiments/tests/test_qwen_backend.py)共 13 项通过，覆盖未来指令/参考泄漏、固定过去帧、未知/非法输出、BCY 分母、在线不可判过度确信、遮挡—重现—修复竞争、修复早于首评分机会、逐钟/整轨预算、失败后不重跑原钟而续接、共同方法证据通路及媒体哈希漂移。合成 FixtureBackend 的 token/显存是**测试值**，不是实测模型成本。

初轮夹具媒体路径与烟测图片共用，后续烟测覆盖了同名图片，使初轮集成记录的帧 SHA 不再与实际文件一致。台账追加 `provenance_audit=invalidated`，旧运行和错误不删除，也**不引用其输出为有效证据**。先以隔离 v2 夹具重跑；最终又按 draft-4 扩大逐钟计时覆盖范围，在[隔离的最终夹具](../experiments/artifacts/fixture_chain_v3/online_track.json)逐帧重算 SHA 后重跑真实 S0/S1/C1。三个方法各 2 次调用、共 3 张送入帧（首钟 1 张、次钟 2 张），均未超 B1，6 个响应可解析：

| 最终真实模型工程运行 | 整轨输入/输出 token | 两钟累计墙钟 | GPU 峰值 | 输出 |
|---|---:|---:|---:|---|
| [S0 记录](../experiments/artifacts/qwen_fixture_final_S0/records.jsonl) | 719 / 74 | 3454 ms | 4,365,048,832 B | 两钟均合法 `C=?` |
| [S1 记录](../experiments/artifacts/qwen_fixture_final_S1/records.jsonl) | 782 / 96 | 4288 ms | 4,376,271,872 B | 两钟均合法 `C=?` |
| [C1 记录](../experiments/artifacts/qwen_fixture_final_C1/records.jsonl) | 838 / 154 | 6457 ms | 4,386,879,488 B | 两钟均合法 `C=?` |

这些数是**六次调用的实测**，只用于检查预算与日志；逐钟累计覆盖选帧、提示、预处理、推理、解析与状态更新，整次调用墙钟另记在各 `summary.json`（含日志写入，分别约 3456/4289/6459 ms）。模型初始化、其他进程占用和长期吞吐不包含在两钟累计墙钟内。三法在这两钟的 token 消耗不同，尚未做等资源 S2 或覆盖匹配；因此不能从 `C=?` 的相同输出推断 H1 无差异，更不能从 token 差解释机制。未来正式比较须按协议固定同源前缀、相同评分机会与 B1，报告逐钟和整轨资源，并核对 S1 摘要质量。

## 5. 仍未完成与反证门槛

没有 H1 `E−/E+` 正反分母、独立标注和 P0 `t_v`，所以**停止 H1 效果比较**。本轮不计算 BCY/错误确认/错误撤销/漏检延迟，不估组级配对方差或正式样本规模；也不把离线监测链路说成闭环成功率改善。强逐项检查 S1 的发展机会、同资源 S2、最近方法合法适配、真实数据预算压力、提示冻结、双人仲裁及保留测试划分均待合格材料后完成。

若以后在同原话/同前缀/同预算/相近覆盖下，C1−S1 的配对 BCY 改善超过协议 δ=5 个百分点且错误撤销、过度确信和成本不恶化，才可能支持 H1 的窄义机制价值；强 S1/S2 同样好、改善只来自更多图像/token/调用或更多弃答、合法修复被锁死，都按协议删减或否定机制。区间跨 0 或 δ 是证据不足，不是等效；没有材料时连该判断都不能做。

## 6. 可重复运行命令

在 `D:\monitor2` 的 PowerShell 内；新运行请给**新的输出目录**，不要改写本报告引用的夹具与日志。以下安装只作用于项目 `.venv`，权重和 HF 缓存留在项目内。索引返回的 wheel 必须通过其 SHA 校验；若下载校验失败，应先按官方文件哈希重新获取，不绕过校验。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch==2.11.0+cu128 torchvision==0.26.0+cu128 --index-url https://download.pytorch.org/whl/cu128
.\.venv\Scripts\python.exe -m pip install transformers==4.57.6 pillow==12.1.1
$env:HF_HOME = 'D:\monitor2\.cache\hf'
.\.venv\Scripts\python.exe -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen3-VL-2B-Instruct', revision='89644892e4d85e24eaac8bacfd4f463576704203', local_dir='.models/qwen3-vl-2b-instruct')"
.\.venv\Scripts\python.exe -m unittest discover -s experiments/tests -v
.\.venv\Scripts\python.exe -m experiments.smoke_model --outdir experiments/artifacts/repro_smoke_001
.\.venv\Scripts\python.exe -m experiments.fixture_run --outdir experiments/artifacts/repro_fixture_001
.\.venv\Scripts\python.exe -m experiments.run_online --track experiments/artifacts/repro_fixture_001/online_track.json --method S0 --outdir experiments/artifacts/repro_S0_001
.\.venv\Scripts\python.exe -m experiments.run_online --track experiments/artifacts/repro_fixture_001/online_track.json --method S1 --outdir experiments/artifacts/repro_S1_001
.\.venv\Scripts\python.exe -m experiments.run_online --track experiments/artifacts/repro_fixture_001/online_track.json --method C1 --outdir experiments/artifacts/repro_C1_001
```

没有 H1 先导复现命令，因为它未运行且数据门槛未满足。当前**不具备进入阶段 8 的条件**。

## 7. R1 重排后的首次材料核查（2026-10-03）

本轮按[新计划](../docs/plans/2026-10-03-task-progress-research-replan.md)先做公开材料与现有标签复用，未重跑本报告的工程检查。取得 4 条作者链接的原始公开视频并做单人抽帧筛查，尚无可用于 H1 的事件正反对、原始许可/时间核定与独立复核。实际来源、纳排和关键初始状态歧义见[首批报告](07_public_material_reuse_audit.md)。没有探索性 S0/S1 模型运行，也没有 H1 运行，因此 run ledger 不新增实验。当前仍不进入阶段 8。

## 8. R-B 下一小批后是否进入探索性强基线诊断

2026-10-03 又完成 putspoon 原始目录元数据和四条预选完整短视频的单人抽帧筛查，并定向核 DoReMi 作者堆叠演示页；详情与全部纳排见[公开材料复用核查 §7](07_public_material_reuse_audit.md)。两条来源失败未核出先入杯后失效，来源成功只有片尾入杯候选，没有匹配的持续保持窗口。原始时钟、正式再用许可和独立复核仍缺。**R-C 材料前提未满足**；本批没有运行冻结模型的 S0/S1，也没有运行 C1、计算 H1 效应/BCY/显著性或修改提示、协议与预算。`experiments/run_ledger.csv` 不追加条目。阶段 7 H1 先导及阶段 8 保留测试继续关闭。

## 9. R-C / ViFailback 原库两条开发材料的探索诊断（D050—D051）

2026-10-03 续行，单执行者。来源追溯和时钟／许可见[补查报告 §8](07_alternative_sources_review.md)。RoboPulse ep618/621 的全部 59 张图像与 ViFailback 原库 `ep1/episode_58`、`ep2/episode_36` 高视角视频帧逐像素一致；LeRobot ID 5060/5197 的完整原标注和逐帧索引／时间也一致。采用原库 MIT 声明及原任务直接研究，RoboPulse 的新增区间不作评分真值或模型输入。时间只使用发布视频／导出的 n/25 坐标，不解释为已经核验的硬件采集时间。

运行前[预注册](sources/recovery_search_20261003/upstream_trace/diagnostic_preregistration.json)固定用户预选两条轨迹、单人标签草案、P0 单相机 1 Hz／256²、逐钟当前/起点/t−1/t−5 包、S0/S1 提示 `r1-upstream-diagnostic-v1`、B1 限制、一次提示迭代、零重复和最多 62 调用。原 `engineering-v2`、协议和工程配置未改；[独立诊断入口](../experiments/trace_diagnostic_20261003.py)只复用现有 harness/backend 并在本进程使用该冻结提示，无网络加载／付费 API。模型仍为原 revision 的 Qwen3-VL-2B-Instruct BF16，确定性解码。本轮不是重跑既有烟测，也不是 H1 先导。

| 运行 | 调用 | 输入 / 输出 token | 严格合法输出 | 达 256 输出 token 上限 | 累计逐钟墙钟 |
|---|---:|---:|---:|---:|---:|
| [ep618 S0 原文](../experiments/artifacts/r1_upstream_diagnostic_v1/ep618_S0/records.jsonl) | 16 | 9,297 / 972 | 0 | 0 | 38.67 s |
| [ep618 S1 原文](../experiments/artifacts/r1_upstream_diagnostic_v1/ep618_S1/records.jsonl) | 16 | 11,665 / 4,096 | 0 | 16 | 146.64 s |
| [ep621 S0 原文](../experiments/artifacts/r1_upstream_diagnostic_v1/ep621_S0/records.jsonl) | 15 | 8,672 / 980 | 0 | 0 | 35.44 s |
| [ep621 S1 原文](../experiments/artifacts/r1_upstream_diagnostic_v1/ep621_S1/records.jsonl) | 15 | 10,892 / 3,840 | 0 | 15 | 139.26 s |

**失败解释**：62 个响应都以代码围栏开始，严格 JSON 解析全部拒绝；31 个 S1 响应又全部达到 token 上限，常含重复叙述和未闭合文本。S1 的合理摘要意图已在冻结提示中明确，但实际所有 `memory_in`／被接受的 `memory_out` 均为空；不能把该运行称为已成功实现合理滚动摘要的强 S1，更不能从这些结果归因“历史推理能力不足”。原文中的可疑画面叙述最多是待查线索，不能替代合法条件判断或可靠错误分型。没有事后清洗围栏恢复分数，没有临时加 token、第二版提示、重复调用或 C1。

合计 62 调用、40,526 输入 token、9,888 输出 token、逐钟累计约 360.02 秒，PyTorch 峰值 4,501,991,424 B。初始化时间另记[初始化日志](sources/recovery_search_20261003/upstream_trace/diagnostic_initialization.json)；不是硬件事件至判断的延迟，也不外推实时吞吐。运行走完不代表输出有效；全部失败已进入实际 run ledger。审计验证同轨两法逐钟帧 SHA／顺序及完整前缀一致、无未来帧、单钟预算合规、预运行冻结文件未变，见[诊断审计](sources/recovery_search_20261003/upstream_trace/diagnostic_audit.json)。

本轮直接发现是**输出格式和摘要执行瓶颈**；尚未取得可用于选择架构的强基线剩余错误。下一批须另行预注册修复这个具体缺陷并确认摘要真的跨钟，再作少量诊断；本次一次迭代到此结束。两例仍是单人开发材料，无独立参考／P0 盲审，因此不计算 H1 效应、BCY、显著性或样本规模，不解封阶段 8。约 15 秒片段不能证明长时程泛化，离线结果也不推出闭环成功率。


## 10. R-C 有界接口修复：S0 格式改善，S1 仍未通过（D052）

2026-10-03，用户授权继续后，先离线复现旧 62 条输出的严格解析失败，保留[逐条失败复现](../experiments/artifacts/r1_interface_repair_20261003/failure_reproduction.json)。既有工程提示和本批提示的差异提供了一个可测假说：明确首字符为 `{`、末字符为 `}` 能否消除围栏；这不等于已找到重复生成的底层原因。新增[隔离执行入口](../experiments/interface_repair_20261003.py)，不修改已冻结的 v1、通用后端、配置或协议。接口门槛测试先复现拒绝失败输出/空摘要传递的测试失败，再实现门槛并通过测试。

[本批预注册](../experiments/artifacts/r1_interface_repair_20261003/preregistration.json)先于全部新调用写入，固定两个候选 A/B 和 42 项输入/代码 SHA。A 只在 v1 语义提示后增加明确 JSON 边界与禁止围栏/重复的指令；B 再将 S1 摘要说明压缩为不超过 35 个英文词。每版只在同一 ep618 的 q=0、1、2 做 S0/S1 各三钟。全六条严格合法、S1 摘要非空且跨钟原样传递才通过；不看 H/C 是否符合草案来选提示。最多两版/12 次探针；只有通过才允许一次完整 62 次诊断，总上限 74 次。两版失败即停止，剩余额度不是继续试提示的授权。

| 探针 | 实际调用 | 严格合法 | 到 256 token 上限 | 输入 / 输出 token | 累计逐钟墙钟 |
|---|---:|---:|---:|---:|---:|
| [A / S0](../experiments/artifacts/r1_interface_repair_20261003/probe_A_S0/records.jsonl) | 3 | 3 | 0 | 1,560 / 114 | 5.11 s |
| [A / S1](../experiments/artifacts/r1_interface_repair_20261003/probe_A_S1/records.jsonl) | 3 | 0 | 3 | 2,004 / 768 | 25.95 s |
| [B / S0](../experiments/artifacts/r1_interface_repair_20261003/probe_B_S0/records.jsonl) | 3 | 3 | 0 | 1,560 / 114 | 4.17 s |
| [B / S1](../experiments/artifacts/r1_interface_repair_20261003/probe_B_S1/records.jsonl) | 3 | 0 | 2 | 1,755 / 607 | 20.84 s |

**实际结论**：这 12 次短前缀探针不再带围栏，S0 六条均可解析，但 H/C/P/G 全为 `?`、evidence_time 全为 0，不能称任务判断改善或全轨格式已修好。A 的三个 S1 响应仍重复至上限；B 的 q=0/1 也截断，q=2 在 95 token 结束但多出一个 `}`，严格解析仍失败。没有删括号、剥围栏、补闭合、重写原文或挽救分数；六条 S1 的摘要仍未被接受，memory_in 一直为空。压短摘要指令并未使滚动摘要执行成功。非法原文中的对象陈述也不作为有效关系判断。

[选择结果](../experiments/artifacts/r1_interface_repair_20261003/selection.json)为 `both_candidates_failed_stop`，没有选中提示，也没有运行完整 62 次。实际新增 **12 调用、6,879 输入 / 1,603 输出 token、56.06 秒累计逐钟墙钟、4,488,696,832 B PyTorch 峰值**；初始化另记，不计硬件事件延迟。实际台账追加四条探针运行；`completed` 仅表示三钟执行结束，不表示接口通过。旧 62 次失败记录全部保留，两批合计 74 次，不把本批上限 74 误作本批实际调用量。

[审计](../experiments/artifacts/r1_interface_repair_20261003/audit.json)重新确认 42 个冻结文件、单人标签草案、旧 v1 八个结果文件未变，266 个来源 SHA 通过，模型逐钟收到的提示/图像与记录一致，无未来帧、跨方法图像一致、B1 合规。本批没有新下载、换模型、训练、付费调用、烟测重跑或 C1。没有独立复核，仍无 H1 效应/BCY/显著性/样本规模，阶段 8 关闭。

**下一步收窄为输出接口的受控定位**：具体复现文件为 B/S1 q=0 的重复摘要和 q=2 的多括号原文；应先区分单独摘要生成与“判断+摘要”组合输出的问题，再决定是否需要前瞻性结构约束，且重新冻结调用预算。不能继续泛换措辞，也不能用后处理让本批变成成功。现在还没有可归因为历史状态机制的强基线剩余错误，R-C 未完成、R-D 候选机制不放行。现有两条源映射和单人失效/保持结论不因接口失败而撤销；最小独立补审包保持可交付，无需标整库。


## 11. R-C 输出任务隔离：发现零历史下的视觉依据错误（D053）

2026-10-03 用户授权续行。此前两版提示没有可靠 S1，故本批不继续围绕标点泛调参，先用[固定隔离诊断](../experiments/summary_isolation_20261003.py)区分摘要生成、JSON 包装和组合判断。运行前[预注册](../experiments/artifacts/r1_summary_isolation_20261003/preregistration.json)冻结 42 项代码/输入：同一 ep618 的 q=0、2、6，三种输出依次为纯文本摘要、仅 memory 的 JSON、memory 加 judgments 的组合 JSON。每格同模型、同实际 P0 包、相同语义上下文与摘要说明，只变输出契约；各格历史摘要均为空，是隔离诊断，不冒充从 q=0 连续运行的强 S1。组合输出额外承担判断输出，因而差异不是纯字符格式。与 D052 比较时还改变了提示组织/模板负担，不能唯一归因于删去某一句话。

预定最多 9 次隔离调用；组合输出三个锚点均满足严格结构、短摘要且人工开发核查内容合理，才允许连续 q=0—8 的 9 次 S1；该链再通过，才允许一次完整 62 次 S0/S1。总上限 80，任一门槛失败即停止后续；零第三版提示、零解码调整、零后处理。仍使用已有冻结 Qwen3-VL-2B-Instruct BF16、greedy 与原 B1 单调用上限。

| 输出契约 | 调用 | 格式合格 | 到 256 token 上限 | 输入 / 输出 token | 推理与输出检查累计 |
|---|---:|---:|---:|---:|---:|
| 纯文本摘要 | 3 | 3 | 0 | 1,343 / 98 | 4.41 s |
| 仅摘要 JSON | 3 | 1 | 2 | 1,385 / 554 | 18.61 s |
| 判断＋摘要 JSON | 3 | 3 | 0 | 1,544 / 271 | 9.34 s |

**格式可解析不等于摘要合理。**q=0 的实际单帧中，绿块在左下、蓝块在中上、红块在右下，三块明显分开；纯文本和合法组合 JSON 却都写绿在蓝上、红在绿上、任务完成，组合 H/C/G 全为 `+`。这时没有历史摘要输入，也没有此前任务执行帧。q=2 绿块受机械臂遮挡，但红块仍分离，不能确认三层完成；两种短输出仍声称完成。q=6 当前绿—蓝关系与原单人草案相容，红块却仍单独在右下；三种契约都错误写红已放在绿上、整体完成。实际画面及逐例核查见[内容门槛记录](../experiments/artifacts/r1_summary_isolation_20261003/isolation_review.json)，完整九条原文见[原始输出](../experiments/artifacts/r1_summary_isolation_20261003/isolation_records.jsonl)。没有通过模型输出来重标或删选轨迹；原参考草案保持原哈希。这是同一执行者的开发核查，不是独立真值或准确率报告。

新的证据排除了两个过强解释：**不能只归因 JSON 解析，也不能归因摘要遗忘**——纯文本同样产生错误完成叙述，且全部九格历史为空。仅摘要 JSON 在 q=0/2 重复截断，而组合 JSON 在三个锚点都正常结束，也不支持“只有组合输出才引发重复”或“任务越多必然越重复”。尚不能分清基础视觉识别不足、任务目标文字诱导或其他提示/模型交互；当前可确认的是目标状态被输出为缺少画面支持的已完成事实，不能据此推出历史台账机制必要。

[输入边界审计](../experiments/artifacts/r1_summary_isolation_20261003/input_boundary_audit.json)用原本地处理器和原图重建九次输入，逐格 token 数与实际调用完全一致；q=0/2/6 分别包含 1/3/4 张图，每图 grid `[1,16,16]`、64 个视觉占位 token，模式间图像 tensor SHA 一致，时序和媒体 SHA 无漂移。这排除空图包、缺少图像占位和明显记录/处理器不一致；**不证明模型真正利用了视觉特征**。

组合输出的结构门槛通过、内容门槛失败，因此实际仅 **9 次调用**，未运行连续摘要九钟和完整 62 次。新增 4,272 输入 / 923 输出 token，推理加输出检查累计 **32.37 秒**，PyTorch 峰值 **4,443,588,608 B**，台账追加九条真实隔离记录。计时从选好帧/指令后开始，含后端推理与输出检查，不含模型初始化、选帧、CPU 审计和人工查看，不能当完整在线逐钟耗时或硬件延迟。三批 R-C 总计 83 次；本批未用的 71 次条件额度作废，不继续换提示。详见[审计](../experiments/artifacts/r1_summary_isolation_20261003/audit.json)。既有 266 来源、42 冻结文件和旧结果哈希通过；无新数据/权重下载、训练或付费调用。

**后续入口改变**：先在清晰 q=0 的同一张图上，将中性“只描述画面”与原任务条件描述作有界对照，区分视觉能力与目标文字诱导。这个测试只用于定位，不能把删除任务条件的描述器冒充原任务强 S1。若底层视觉依据仍不可靠，应收窄/暂停当前模型上的历史机制路线，而不是加 C1。只有视觉依据和合理摘要都通过后才恢复全轨强基线诊断。R-C 未完成、R-D 机制选择/H1/阶段8仍关闭；独立关系与 P0 前缀复核包仍待真实独立回答。


## 12. 本地已下载的 8B 试跑：有改善，但未通过完整诊断门槛（D054）

用户明确指出本机还有更强模型并授权检查试用。此前只沿用项目 `.models/qwen3-vl-2b-instruct`，未完整盘点 Ollama，这是本项目模型可用性核查的遗漏。实际 [Ollama 清单](../experiments/artifacts/r1_local_stronger_20261003/tags.json)已有 `qwen3-vl:8b-instruct`（6.1 GB）、`qwen3-vl:4b-instruct`（3.3 GB），另有 MiniCPM 系列、Qwen2.5VL 和文本模型。本批只运行 **8B**；4B 仅核元数据，其他模型未调用，不按多模型试错挑有利输出。

8B 是 Q4_K_M GGUF，Ollama 0.35.0，清单 digest `0533d74300e4f9bc367d675d4e64ffd073d50ff16a2b4096cc2e8a1cf8c96319`；本地清单及全部 blob 引用的大小/SHA 均验证，权重 blob 为 6,140,392,672 B，无下载或复制权重。它不是 ViFailback-8B 微调权重，也不是 RoboMeter/Robo-Dopamine，因此本轮仍是本项目探索，不是作者方法复现。原 BF16 工程配置保持不变。

[运行前预注册](../experiments/artifacts/r1_local_stronger_20261003/preregistration.json)固定一版提示、唯一8B模型、最多75调用：先 q=0中性描述及q=0/2/6组合判断四次；内容/格式通过才进行连续九钟，再通过才进行完整62次。沿用 D053 的组合提示，因 Ollama 图像数组接口增加明确的图像顺序/时刻列表；所有 PNG 均复用原256² P0，不加入腕部或未来画面。不启用结构化解码、不清洗JSON，温度0、repeat_penalty1、输出256、上下文4096。状态文本保守限制为512 UTF-8字节，不冒充已测得的同处理器512 token；Ollama 原生 token 与 HF 图像展开不可直接等同。

| 实际尝试 | 结果与单人开发观察 |
|---|---|
| [q0 中性描述](../experiments/artifacts/r1_local_stronger_20261003/probe_neutral_q0/records.jsonl) | 正确描述蓝块居中、绿块左侧、红块右侧，均在台面上。没有凭空描述三层堆叠。 |
| [q0 原任务组合判断](../experiments/artifacts/r1_local_stronger_20261003/probe_joint_q0/records.jsonl) | JSON合法；摘要明确绿块未堆上蓝块、红块未放置、三层尚未形成。H/C/G均未知，文字更贴近画面不等于结构化判断已准确。 |
| [q2 原任务组合判断](../experiments/artifacts/r1_local_stronger_20261003/probe_joint_q2/records.jsonl) | JSON合法，但H/C为正，称绿块已经放到蓝块上。实际q2/q0/q1包没有支持释放后绿在蓝上的证据，绿块附近受左夹爪遮挡、蓝块可见分离，属于过早确认；红块未放置的描述可支持。 |
| [q6 四帧请求](../experiments/artifacts/r1_local_stronger_20261003/probe_joint_q6/records.jsonl) | HTTP400，未生成判断。服务端报告请求4457 token超过4096上下文，明确拒绝而非静默截断，不是OOM。 |

[服务端摘录](../experiments/artifacts/r1_local_stronger_20261003/server_context_excerpt.txt)确认本次启动含 `--image-min-tokens 1024`；三图请求为354文本+3072视觉=3426 token，四图请求总4457。这与先前HF路径每图64视觉token有明显差异。当前Ollama路径的四张图本身即占4096，无法原样满足B1“图像＋文字≤4096”的预算；要继续必须单列并说明后端/预算变体，不能静默加上下文后称同预算。此设置是本次安装版的实际日志事实，不从它推断所有Qwen实现都必须如此。多图时间绑定也应在任何完整运行前核验。

实际 **4次请求、3次返回生成、1次运行失败**，新增四条真实ledger。成功返回部分为5,889输入/167输出token，四请求客户端墙钟约18.93秒，首请求内含模型加载约7.31秒。失败记录内零token字段是缺少原生响应的占位，不是测得零输入成本；服务端另记4457输入token的被拒请求，未生成输出，不能当成功推理计入。Ollama报告模型显存驻留5,534,897,929 B，CLI约11%/89% CPU/GPU；这是驻留量而非峰值。运行后仅卸载本批加载的8B，保留Ollama服务及所有本地权重。

[内容门槛](../experiments/artifacts/r1_local_stronger_20261003/probe_review.json)与运行门槛均未通过，未启动九钟链或完整62次，也未借剩余额度调用4B、扩大上下文或改提示。详见[审计](../experiments/artifacts/r1_local_stronger_20261003/audit.json)。四批R-C累计87次请求尝试，其中本批一次在上下文检查时被拒。没有独立复核、H1效应、BCY、显著性、C1或阶段8。

**能推进的部分**：本地确有可运行的8B，不能再把可用范围限制为2B；q0的基础文字描述也不再出现此前的三层完成幻觉。**还不能推进的部分**：更大模型并未自动消除遮挡下的过度确认，合理滚动强S1尚未验证。模型权重/规模、量化、后端、视觉token展开和图像消息组织都改变，不能把q0差异单独归因为规模，更不能作为机制收益。

下一入口是保留8B为候选，先对齐作者或模型官方的图像/时刻输入流程，并显式登记适用于该后端的独立探索预算；不要继续将2B失败当研究出发点，也不要把通用8B称作作者方法。任何预算变体须保留原S6-draft-4及2B历史，独立记账，先验证遮挡判断和实际历史传递，再考虑完整诊断。当前不自动放行该预算变体。
