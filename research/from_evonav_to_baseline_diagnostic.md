# 从 EvoNav 到本项目基线诊断：任务、材料与可否定入口

日期：2026-10-03（Asia/Shanghai）。承接 D017、D024—D059；单执行者。本轮新增一条 ProgressCompass 作者基准的**原生任务—标签—具体 episode—视频**绑定，固定三条开发案例的诊断口径；没有专用模型运行或逐例预测。S6-draft-4、S7-screening-4、C1/C2/C3 与阶段 8 边界不变。

**续查入口（D066）**：针对“先看作者自己的试卷和成绩”新增 §7。§1—6 保留当时的证据与下一步记录；当前行动顺序以 §7.4 为准。

## 1. EvoNav 实际怎样建立证据

仅复核本地 [正文 §5／Tables 1—4](sources/evonav_main.pdf)及[补充 A—B](sources/evonav_supp.pdf)，不把论文叙事推作作者研发时间表。作者在 Habitat 连续导航版 R2R-CE 按既有零样本协议评 100 episodes；从更复杂的 NavRAG-CE 另随机抽 100 组轨迹—指令，其指令模拟不同用户角色的一日需求。实机用全向轮机器人，在实验室、走廊、电梯厅、书房各标 20 条语言指令，共 80 条；补充 B 展示导航指令与关键决策案例。模拟输入包括指令、全景 RGB-D 与候选 waypoint；不是机器人操作监测材料。[正文 §5.1](https://openaccess.thecvf.com/content/CVPR2026/papers/Dai_History_to_Future_Evolving_Agent_with_Experience_and_Thought_for_CVPR_2026_paper.pdf#page=5)、[补充 A—B](sources/evonav_supp.pdf)

| 证据层 | 作者实际给出 | 可支持的结论与界限 |
|---|---|---|
| 主比较 Tables 1—2 | R2R-CE 同 Gemini-2.5-pro：Open-Nav SR 23、OSR 30、SPL 19.90；EvoNav 43、51、37.77。NavRAG-CE 同模型：SR 24→30、SPL 13.39→17.60。还列 GPT-4o 与监督/额外预训练方法。 | 是**整体导航成功、路径和终距**，不是进度估计、地标预测或局部选择准确率。Open-Nav 的同模型比较较有解释力；除 SmartWay-GPT4o、MapGPT-CE-GPT4o 外作者说共享 waypoint predictor。Table 1 带 † 的 DiscussNav、NavGPT-CE、MapGPT-CE 数字引用前人，不能当同次重跑。 |
| 实机 Table 3 | 四场景各 20 条，同 Gemini 的 Open-Nav 与 EvoNav SR 分别为 35→40、15→35、25→35、15→40。 | 是作者报告的实机**终局成功率**，未提供每次局部误判的分母。 |
| 消融 Table 4 | 同一 R2R-CE 配置从 Base SR 9、A3 27、B2 31、C3 40、Full 43；同时列 NE、nDTW、OSR、SPL。 | 支持这些配置的整体表现差异；输入信息与调用也随组件改变，不能单由 Full 最好推出每项必要、纯机制因果或正交互。 |
| Fig.3—4、补充 B | 挑选的轨迹、关键视点和生成 thought。 | 能解释作者提出的问题与一次决策差异；不是按特定错误类型抽样的准确率或真实因果解释。 |

在已核的正文与补充中，**没有 EvoNav 对“局部进度判断错、地标错、历史误导”等特定错误类型的发生率统计**。我们额外要求逐条件真值、正常调整反例、未知/遮挡、同信息与资源、episode 级分母和反向错误，这些是**本项目补充**，不是 EvoNav 已完成的实验。[既有论证图](02_evonav_argument_map.md)、[流程边界](03_research_workflow_lessons.md)

**23% 的测试卷来源与口径（D063 复核）**：R2R-CE 是先于 EvoNav 存在的 Habitat/Matterport3D 连续导航基准，给任务指令、场景、起点及目标位置；[VLN-CE 官方库](https://github.com/jacobkrantz/VLN-CE)提供环境和评测。Open-Nav [官方库](https://github.com/YanyuanQiao/Open-Nav)发布 `OpenNav_R2R-CE_100_bertidx.json.gz`，在 `val_unseen` 配置中指定这个 100 条子集。EvoNav 补充 A.1 写明按前人零样本协议评 100 episodes。其 Table 1 报 Open-Nav-Gemini-2.5-pro SR 23、OSR 30，EvoNav 同模型 SR 43、OSR 51；这里 SR 是模拟执行**最终停止时**的任务成功比例，VLN-CE [官方配置](https://github.com/jacobkrantz/VLN-CE/blob/master/habitat_extensions/config/vlnce_task.yaml)设成功距离 3 米，OSR 则看沿途是否曾抵达目标附近。Table 1 的 `†` 仅标其他从前人文献取的行，Open-Nav 两行没有 `†`；结合换用 Gemini-2.5-pro 和共享 waypoint predictor，**推断**这两行是作者在其比较设置下评出的结果，而非原 Open-Nav 论文直接给出的 Gemini 成绩。EvoNav 没有给逐例轨迹/ID 列表及原始评测日志，不能独立核对是否与 Open-Nav 发布包逐条完全相同，也不能由 23% 定位到历史/未来推理组件的错误率。真机 80 条属于另一组 Table 3 实验。

**同任务还是新任务（D067 澄清）**：[Open-Nav 原文 §III—IV](https://arxiv.org/html/2409.18794)与 EvoNav 正文 §3—5 都以零样本连续环境视觉语言导航为大任务，目标仍是按语言指令到达目的地；EvoNav 并未另开一个 Open-Nav 原本不承担的导航任务。Open-Nav 已有指令分解、基于本次轨迹历史的进度估计和候选视点决策，所以不能说它“没有进度监测”或“完全没有历史”。EvoNav 的更窄**解释性假说**是这类决策对既往错误反馈和未来动作／地标预想利用不足；其新组织包含已结束 episode 的经验总结及当前任务的未来推演。Fig.3/补充 B 给说明案例，Tables 1—3 在同一导航任务家族给整体结果，Table 4 给配置消融；论文**没有**先按“初错后持续失败”划出子集并报告 Open-Nav 在该子集上的错误率。因此“在同一大任务内提出较窄弱点”是对的；“作者已测得那个窄类是 Open-Nav 的主要失败来源”则未获证实。SR=23% 是整条导航任务的终局成功率，并非这项窄弱点的准确率。

## 2. 把专用系统放回其原生任务

| 系统与角色 | 原生输入 → 输出；是否承诺旧条件当前有效 | 已有覆盖与公开性 | 当前可验证性；适配性质 |
|---|---|---|---|
| **RoboMeter-4B：主基底** | 任务文字＋轨迹帧；原生逐时**整体进展、成功概率**，两轨可给偏好。因果 `use_frame_steps=True` 在已核固定服务端逐前缀取四帧；没有指定关系真假/未知字段。 | [官方推理说明](sources/system_refresh_20261003/robometer_readme.md)、[固定服务端](sources/direction_selection_20261003/eval_server.py)与公开权重入口；作者 OOD 失败检测 TPR 0.77/TNR 0.70 是原任务汇总误报/漏报。ProgressCompass 作者在 ContextProgress-Bench 用它作冻结骨干，并报告无上下文 MAE 25.42。未核到这些结果的 episode 级预测。 | 代码路径与本轮一条**作者原生基准材料**已绑定；本机所查缓存无精确权重，禁止新权重下载，故未运行。将整体分数直接判作 `green_on_blue` 是不合法映射；显式逐条件问句则是新增能力测试。 |
| **R²VLM：关键强比较** | ALFRED/Ego4D 的任务文字＋当前视频 snippet＋上一轮 CoT → 更新的任务分解/完成状态和 0–100 进展；论文明确允许合并、拆分、重排步骤并更新完成状态。[§3.2](https://arxiv.org/html/2603.17312v1) | [官方库](https://github.com/GLAD-RUC/R2VLM)有 ALFRED SFT/RL 权重及训练入口；[ALFRED test 基准](https://huggingface.co/datasets/zhangyuelin/alfred_progress_bench)有 669 行、任务/分步时间与原 ALFRED 图像路径，视频须从 ALFRED 取得。论文报 ALFRED 进展 MAE 2.19、bin 0.917、完成 acc 0.988，Ego4D 进展 MAE 19.25；均非旧条件有效性率。仓库 README 未给现成逐例预测/简明推理命令。 | 强于“只能固定完成状态”的假设；但主要是专家演示与室内 ALFRED/Ego4D，迁到 ViFailback 机器人臂是域/任务适配。本机所查缓存无精确作者权重，本轮不运行。 |
| **ProgressCompass：优先架构审查，不充作本轮可运行主法** | 指令＋按前缀的画面，经 Orienter、冻结 RoboMeter、Verifier、文本 Navigator → 整体进展曲线、步骤接受与记忆。附录 B 说已满足步骤固定，亦明确区分 lasting state/brief interaction；尚不承诺每个旧条件的当前真假。[附录 B](https://arxiv.org/html/2609.36684v1) | [ContextProgress-Bench](https://huggingface.co/datasets/Sterzhang/ContextProgress-Bench) 24 任务/120 clean episodes/552 subtask 区间，含合法来回搬运；另 15 个 Early stop/Extra steps/Mismatch 负例。MAE 9.3 是原生进展，不是逐条件有效性。数据集 README 明示**无 baseline predictions 或 model outputs**，项目页仍为 Code coming soon。 | 任务/视频/标签可核；原法代码、逐例输出与模型组合未发布，不能用本地通用 Qwen 代跑。把旧关系被破坏的失败执行加入评测属于新能力要求 C。 |
| RoboMonitor、Robo-Dopamine 2.0 | 前者有监督多视角阶段/完成/失败；后者有前缀历史与扰动保持/失败/恢复的 pairwise 进展。 | 前者所查无可用发布包且四任务监督结果不能当零样本；后者 preview 与论文精确 checkpoint 对应未核。 | 保留直接相关背景；当前不扩大为全部复现前提。[筛选依据](current_systems_refresh.md) |

ProgressCompass 对比五种 PRM 的“无/有上下文”在每种模型内保持**输入格式**，有上下文由人工提供当前子任务及边界；它不是自主获得上下文的纯消融。附录 C 对部分模型还改变采样频率/帧数。其 RoboMeter 论文实验写 `prefix_sample_frames=8`，而已核 RoboMeter 固定官方服务端 `use_frame_steps` 分支硬编码四帧；没有 ProgressCompass runner 时不能把这份服务端默认路径直接宣称为论文精确复现。[ProgressCompass §3、附录 C](https://arxiv.org/html/2609.36684v1)、[服务端 L211—234](sources/direction_selection_20261003/eval_server.py)

**A/B/C 界线**：A 是作者原任务中的进展/失败判断误差（例如 RoboMeter OOD 汇总误报、ProgressCompass Figure 3(a) 中红块离开绿垫后原 RoboMeter 曲线回落）；B 是同任务中未独立报告的“合法回撤/旧成果保持”等子类误差率；C 是本项目增加的“给定旧条件当前成立/失效/未知”。Figure 3(a) 未标 episode ID，不能把该曲线认作下述 episode1 的逐例输出。C 不输出本身不算原方法判断错。[ProgressCompass §3.2](https://arxiv.org/html/2609.36684v1)、[PRM 核读](prm_robopulse_scope_review.md)

## 3. 已拿到的原材料与具体绑定

本轮从已登记的 [ContextProgress-Bench 固定 revision](sources/system_refresh_20261003/contextprogress_api.json) `0eb2e2e61f89c499de94a31264c704735b52900c` 中，先 HEAD 核大小，再只取 10 个小型索引/说明/指令/manifest 与**一条 568,568 B 完整视频**，合计 1,071,166 B；逐文件 URL、大小、SHA-256 在[新增来源清单](sources/baseline_diagnostic_20261003/fetch_manifest.json)。未取整库或新权重。[case registry](sources/baseline_diagnostic_20261003/case_registry.json)在候选模型输出前冻结。

| 材料及对象绑定 | 媒体/时间、原标签与可复用字段 | 缺项、许可及划分 |
|---|---|---|
| **ContextProgress `RMBench/place_block_mat/episode1` → RMBench 原 `episode4`**。[原指令和 manifest](sources/baseline_diagnostic_20261003/contextprogress/RMBench/place_block_mat/demo_clean/episodes/episode1/manifest.json)要求三个红块逐个先上绿垫再回各自蓝垫，左至右；六段半开边界 `[0,174),[174,349),[349,525),[525,701),[701,878),[878,1056)`，可逐项绑定。[作者 episodes 索引](sources/baseline_diagnostic_20261003/contextprogress/episodes.jsonl)、[subtasks 索引](sources/baseline_diagnostic_20261003/contextprogress/subtasks.jsonl)、[ID 映射](sources/baseline_diagnostic_20261003/contextprogress/episode_id_mapping.json)三重一致。 | [完整视频](sources/baseline_diagnostic_20261003/contextprogress/RMBench/place_block_mat/demo_clean/episodes/episode1/full_video.mp4) 320×240、30 FPS、1056 帧、35.2 s。抽查 f160/f180：左红块在绿垫；f330/f360：返回左蓝垫。[抽帧 160](sources/baseline_diagnostic_20261003/inspection_frames/place_mat_01.png)、[330](sources/baseline_diagnostic_20261003/inspection_frames/place_mat_03.png)。按作者公式，f160/f330 原生进展为 15.414/31.609（0–100），**继续增加**，见[复算](sources/baseline_diagnostic_20261003/validation.json)；这不是 red-on-green 当前关系标签。对象/阶段/视频帧可复用为“任务要求的合法撤回”对照；该变化不能判退步。 | 作者明确此库是 test；本项目已经阅读，故仅开发，连同原 RMBench episode4/相同物理 rollout 排除未来保留测试。作者注释 CC BY 4.0；视频继承 RMBench 源许可并标研究用途，[混合许可文件](sources/baseline_diagnostic_20261003/contextprogress/LICENSE.md)与[上游 RMBench MIT 仓库](https://github.com/robotwin-Platform/rmbench)已核，后续外部分发仍需逐层检查。没有方法在此 episode 的原始预测，无法声称任一方法判错。 |
| **ViFailback ep2/episode_36 → RoboPulse++ ep621 → LeRobot 5197**。原任务为左臂绿上蓝、随后右臂红上绿；对象 `green_on_blue`，无任务修订证据。[映射](sources/recovery_search_20261003/upstream_trace/source_mapping.json) | 原高视角 361 帧、25 FPS 编码播放时钟；59 张发布帧整体像素匹配。单人草案：f200—290 已成立，f290—310 失效区间，P0 q12—13 暂不可判、q14 暂定失效。[原标注](sources/recovery_search_20261003/upstream_trace/ep621_source_annotation.json)为 task planning/第 5 子任务失败；RoboPulse++ 整体下降 22—28。 | 原整体负标签不能替代此关系真值，也没有作者 judge 输出；机器人物理时钟、独立 P0 复核仍缺。原 ViFailback 视频 MIT；RoboPulse++ 新标注 `other` 单列，不混许可证。开发/重复/其他视角均排除保留。 |
| **ViFailback ep1/episode_58 → RoboPulse++ ep618 → LeRobot 5060**。任务文字同上，仍为不同场景/错误原因，并非严格配对。[映射](sources/recovery_search_20261003/upstream_trace/source_mapping.json) | 376 帧、25 FPS；单人草案：f150 后绿上蓝成立，后续红块操作失败而可见保持，P0 q14 作保持锚。[原标注](sources/recovery_search_20261003/upstream_trace/ep618_source_annotation.json)为 gripper 6d-pose/第 5 子任务失败；整体下降 18—29。 | 与 ep621 同样缺作者输出和独立真值。两条约 15 s 短片都不能证明长时程能力；ep621 后续红块子任务没有成功，不能包装成“后续成功的附带破坏”。 |

R²VLM [ALFRED 基准元数据](sources/baseline_diagnostic_20261003/r2vlm_alfred_bench_api.json)固定 revision `055291beea223800dd507cc139d08da16dee33e8`，Apache-2.0，`test.jsonl` 7,209,744 B 与 README 150 B 已核 HEAD；本轮未取大文件。官方数据页显示任务、narrations、分段 `turns` 和原 ALFRED 图像路径，但未取得逐例模型预测或失败后旧条件标签。与 ContextProgress 作者公开的 clean 演示不是同一物理 rollout，不混作配对。前轮 RoboMeter OOD 元数据/putspoon、DoReMi/SafeManip/BotFails 排除结论继续有效，不重取。[既有数据清单](../experiments/data_manifest.json)

## 4. 证据账：哪些已证实，哪些仍待检

| 判断 | 证据级别 | 当前结论 |
|---|---|---|
| 进展 PRM 在上下文依赖任务上有原生误差；RoboMeter OOD 整轨失败检测有误报/漏报 | **作者汇总成绩与展示案例**：ContextProgress Table 1/Fig.3(a)、RoboMeter Table IV | 属 A；合法状态回撤被原生进展误读已有作者案例，但不是我们取得了 PC/R²VLM 在旧条件有效性上的错判。 |
| PRM-as-a-Judge 1.5 C.5.2 已研究已完成子目标撤销；RoboMeter 历史依赖 Falling accuracy 0.901，Forward 0.408 | **作者汇总成绩**；跨模型，非同模型历史消融 | 是强反证与已有研究。Table 8 无本轮可绑定 episode/逐例输出；C.5.1 的 155 Falling 是机器人执行失败类型，不能叫 judge 错误类型。[核读](prm_robopulse_scope_review.md) |
| ProgressCompass“已满足步骤固定”会把后续真正失效误当仍有效 | **设计边界提出的假设** | 附录 B 也允许描述 lasting state/brief interaction；暂无代码或逐例预测，不能宣布错误。合法送回原位本就应保留历史完成。 |
| R²VLM 不能修正旧步骤 | **已有反证** | 论文明确更新完成状态；不能保留这个预设。它是否正确识别我们指定的旧关系仍未知。 |
| ep621 失效、ep618 保持、ContextProgress 合法返回 | **执行现象／任务语义材料** | PC 合法返回由作者原话与本轮视频帧支持；两条 ViFailback 关系仍单人。三者都没有专用模型本次实测。 |

### 4.1 对宽泛 H1 的收窄（D062）

“模型需要历史才能发现子目标撤销”已由 PRM-as-a-Judge 1.5 C.5.2 直接研究；“状态回到原处也可能是合法推进”已由 ProgressCompass 的 `place_block_mat` 任务及其展示案例处理。它们不应再作为本项目的待发现不足或新机制理由。PRM 的 Falling 汇总准确率 0.901 表明其原任务仍有错误，但没有把错误绑定到“先前成果仍需保持却被后续操作破坏”的具体 episode。ProgressCompass 的非零整体 MAE 同样不能定位到此子类。

**下一步只立诊断假设 H-D，不立改进机制假设**：优先寻找一种更窄的任务，即后续子任务**本身成功**，却附带破坏了原指令在最终时刻仍要求保持的先前成果。预测是：在视觉和任务语义均可判时，至少一个可合法测试的强进展／执行监测方法可能因新步骤的正向证据而沿用“旧步骤已完成”，未识别当前旧条件已失效。后续失败且旧成果保持、任务明确要求撤回、遮挡不可判分别作反向控制。这个“正向新里程碑掩盖旧成果损坏”的子类区别于目前 ep621 的后续子任务失败；但 PRM-as-a-Judge 已研究一般子目标撤销，不能声称此子类未被任何强法处理。H-D 只是待证伪的搜索与诊断预测，不是已证实的领域不足。若原生输出无法表示指定条件，则只能报告新增能力测试不可评价，不能计原任务错判。R²VLM 明确可更新完成状态，是直接反证候选；ProgressCompass 的固定步骤是待检实现边界，不能据此判错。

检验顺序是先找原始任务文字、成功的后续子任务证据与旧条件可见失效均可核的完整 episode，且不由待评输出选例；再取得强方法**原任务、原输出**的逐例预测，如其原生输出无合法映射，则将逐条件问答明确标为新增能力。给同指令、同因果前缀、同观察权限的失效／保持／合法撤回控制。若强法正确区分，或差异只来自物体识别、遮挡、输出适配，H-D 在该范围被否定，应停止以此作为新架构动机。现有三个已看开发 episode **都不满足 H-D 的正向后续里程碑条件**，只能检查较宽问题的可行性，不能估计该子类的发生率或错误率。EvoNav 中相应位置是动机案例之后、§5 主比较与消融之前的**基线缺口确认**：EvoNav Tables 1—3 证明整体导航收益，Table 4 支持组件配置差异；它没有统计局部错误类型。本项目的 H-D 若声称特定判断不足，需要比这些整体指标更直接的逐例或有分母子类证据。

## 5. 先固定的最小诊断与运行门槛

原生通道先用**作者原任务、原输出**：对 `place_block_mat/episode1` 输入全任务文字和因果视频前缀，保留 RoboMeter 逐时进展/成功原值，以作者六段进展公式评原生误差、检查合法返回段是否误降；若获得 ProgressCompass 官方实现，用同一 episode 核其原生进展曲线。`f160` 与 `f330` 是一个 episode 的两个审查点，不算两条样本。不能把 Figure 3(a) 的未标 ID 曲线当本条预测。作者 README 明说没有逐例输出，当前也无精确可运行权重，因此本轮**未做模型运行**。

新增能力通道固定上述三条 episode，不按输出筛选：ep621 旧关系失效、ep618 后续失败但旧关系保持、ContextProgress 按任务要求合法送回。ep621 q12—13 先列“当前证据不足”，q14 暂定可判；另核修复样例时只有真实可追溯修复才加入，不强凑。每个目标分记历史事件 H、当前最终状态 C、确有文字要求才设全程约束 P、整体任务 G；任务要求的送回使 red-on-green 变假，却不撤销已做过的放置事件，也不违反持续保持要求。无独立盲审时只作单人逐例可行性，不报子类分母错误率、H1、BCY 或显著性。

若日后原法及资源到位，**运行前**另冻结 checkpoint hash、代码 revision、任务原话/有无改写、前缀帧包与视角、采样及候选确认时刻、提示/温度、调用/token/迭代上限和停止条件。保留每次原始进展曲线、成功概率、CoT/状态文本、未知/拒绝、失败与成本。原生标量没有已证的逐条件阈值，故本版**不设伪阈值**；显式问 `green_on_blue` 的输出记为 C 类任务适配，不能回填作 A 类原生错判。若问句改变训练语义、只用当前清晰帧/简单逐项检查或同权限滚动摘要已经答对，先按普通提示、感知或输入解释；R²VLM/ProgressCompass 等相关强法不能由这些简单对照替代。

优先核的混杂是：对象/颜色识别本来就错；旧画面被当当前画面；合法返回误报下降；遮挡过度确认；完整轨迹真值泄入在线前缀；PC 候选峰值/三帧 Verifier 产生的确认延迟；RoboMeter 四帧官方服务端与 PC 论文八帧设置不一致。若专用法在同权限下正确区分失效、保持、合法返回并在不可见处保留不确定，本项目“强方法仍缺这种判断”的直觉即被本次案例**局部否定**。若只有一条错误或错误来自遮挡/普通视觉/接口，也不足以推动新架构。

## 6. 下一件具体动作

**D062 更新优先级**：先在已有官方来源中定向找一条“后续子任务可核成功、同时旧最终条件可核失效”的完整原始轨迹，记录任务文字、两项对象绑定、成功/失效时刻、参考标签与重复关系；若无合格原材料，明确列缺项后停止 H-D，不用 ep621 冒充。找到后在看模型输出前固定该条及保持/合法撤回控制，并先问目标方法的原生任务是否允许把这次失效计入其进展/成功判断。下段的 `place_block_mat/episode1` 原法输出仍是已有材料的原生复核入口，但它只检验合法撤回，不检验 H-D。

**已有材料的原生复核入口**：定向核 ProgressCompass 后续官方代码/输出目录是否给出 `RMBench/place_block_mat/episode1` 的曲线及论文八帧采样 runner；若发布，按上节原生通道复算同一条合法返回，并保存逐例文件/版本。若仍无文件，转向已定位的 RoboMeter 官方 `eval_server.py` 原生推理入口；当前本机无其精确 checkpoint，且本轮禁止新权重下载，所以停止在[冻结案例](sources/baseline_diagnostic_20261003/case_registry.json)与输入清单，不以通用本地 Qwen 代替。待合法精确权重可用，先只跑这一条原生任务（报告服务端四帧与论文八帧的区别），再考虑 ep621/ep618 的**明示适配**。取得正常调整、遮挡和修复的更多可核材料后，才谈有分母的诊断。

当前**不适合设计改进架构**：已有作者汇总错误和任务现象，但还缺“一个强方法在可判、任务语义明确的指定旧条件上实际怎样回答”的逐例诊断，以及独立复核。没有此证据，不能把输出形式差异或执行失败写成强方法不足。

## 7. 作者自己的试卷先告诉了我们什么（D066）

### 7.1 本项目在 progress monitoring 中的位置

本项目属于**机器人操作执行过程的任务条件化进展监测**，更窄的可检验问题是：给定截至当前的观察前缀和原任务，先前有证据达成的子目标，其**当前仍须满足的结果**是否还成立、已被后续操作破坏，或暂不可判。历史事件发生过、最终状态要求、全程保持义务和合法撤回分开裁定。这是过程判断／状态有效性问题；机器人最终任务成功率、策略本身的失败率、一般阶段分类、轨迹偏好分数及未来失败预测与它相关，但不是同一输出。H-D“后续子任务成功却附带破坏旧最终条件”是其中一个待检子类，不定义整个领域。本文的现有报告只能证明原生进展判断仍有误差，不能自动证明 H-D 或逐条件有效性错误。

### 7.2 作者已公布的低分和强反证

下表逐项复核本地固定正文，保持原评价单位。F1、AP、MAE、准确率不可互换；尤其不要把它们统称为“任务成功率”。

| 作者试卷与原生输出 | 作者报告的数值 | 能支持什么；不能支持什么 |
|---|---|---|
| [PRM-as-a-Judge 1.5 附录 C，RoboPulse++ Table 6](https://arxiv.org/html/2608.14284v1#A3.T6)：700 个机器人操作 episode 的区间上升／下降方向；作者对有效采样点汇总评分，区间边界各去两点。 | 专用 Robo-Dopamine Forward：Rising F1 **0.92**，Falling F1 **0.61**、召回 **0.50**，总体 Macro-F1 **0.77**、accuracy **0.84**。Backward 的 Falling F1 **0.63**（表中最佳）；RoboMeter Falling F1 **0.50**、总体 Macro-F1 **0.69**。 | **A：已证实的原生进展方向判断不足**，特别是下降方向漏判；并非“700 次任务仅 63% 成功”，更非旧条件失效率。发表前人已指出，不能当本项目新发现。发布 JSONL 的 `0` 停滞区间与论文二分类计算的完整处理仍未核定，不自行复算。 |
| [同论文 C.5.2 Table 8](https://arxiv.org/html/2608.14284v1#A3.T8)：作者定义的历史依赖子集，含已完成子目标后来被撤销的情况。 | Falling 条件准确率：Robo-Dopamine Forward **0.408**，RoboMeter **0.901**；总体分别 **0.746/0.940**。 | 这是**强反证**：序列式 RoboMeter 在作者这类历史依赖下降上已相当强，不能声称现有方法普遍不会修正旧进展。跨模型、输入和输出组织不同，不是纯历史消融；论文未给子集 ID／逐例预测，不能认定 ep621/ep618 属于此子集或定位剩余 9.9% 的错因。 |
| [RoboMeter 附录 E-5 Table XXVII](https://arxiv.org/html/2603.02115v2#A5.SS5)：OOD 整轨失败检测，原生进展曲线配窗口阈值。 | 平均 TPR **0.77**、TNR **0.70**、F1 **0.81**。 | 存在原生漏报和误报；没有给出“先前成果当前有效性”子类的分母或逐例判断，且轨迹失败不等于旧条件失效。 |
| [ProgressCompass §3／§5](https://arxiv.org/html/2609.36684v1)：ContextProgress-Bench 的整体 0–100 进展估计；同一冻结 RoboMeter 有无作者提供的正确子任务上下文。 | 无上下文 MAE **25.42**；完整 ProgressCompass MAE **9.3**。Early stop 负例中，RoboMeter 偏差 **32.7**、ProgressCompass **7.3**。 | 作者已展示上下文缺失时原生进展明显偏离，且自己的方法改善很多；9.3 仍是误差而非 9.3% 成功率。作者 Fig.3(a) 展示合法送回时原 PRM 曲线回落，但未给该图对应 episode ID；不能冒充本地 `place_block_mat/episode1` 的逐例模型输出。 |
| [R²VLM Table 1](https://arxiv.org/html/2603.17312v1#S4.T1)：ALFRED／Ego4D 视频进展、分箱与完成判断。 | ALFRED 进展 MAE **2.19**、bin **0.917**、completion acc **0.988**；Ego4D 分别 **19.25/0.318/0.761**。 | 在 ALFRED 原生演示上很强，Ego4D 的进展分箱仍难；两个基准/领域不可横向混算。它明确可更新步骤完成状态；现有数值没有单列机器人操作中旧成果失效。 |
| [RoboMonitor Table I](https://arxiv.org/html/2609.30715v1#S4.T1)：四任务有监督多视角运行时阶段、完成、失败监测。 | 52 条监督轨迹时 failure AP **45.87%**，对照 RoboMeter + Temporal SFT 为 **59.39%**；100 条时 RoboMonitor failure AP **72.01%**。 | 失败检测的作者报告仍有余地，但成绩随监督预算变化；不能把 45.87% 当零样本失败率、旧条件错判率，或断言其在本项目任务弱于冻结 RoboMeter。 |

[PRM 附录 C.5.1/Table 7](https://arxiv.org/html/2608.14284v1#A3.SS5.SSS1)的 155 个 Falling 片段按**机器人执行失败类型**分组，121 个交互关系、34 个任务顺序；它没有统计 judge 的 155 个错误。此处若把 78.1% 写成监测器关系推理错误占比，会把被观察对象和测量工具混淆。

### 7.3 现成试卷与本项目问题的距离

RoboPulse++ 最接近“现有专用进展 judge 自己在什么地方低分”：任务文字、区间方向和作者 Table 6 同卷比较已存在；本地固定 JSONL 有 **700 episode、2244 区间**，其中 `+1/0/-1` 为 **1130/537/577**，见[标签审计](sources/recovery_search_20261003/robopulse_annotation_audit.json)和[原始发布文件](sources/recovery_search_20261003/RoboPulsePlusPlus.jsonl)。但 Table 6 的点级方向判断不能直接转成“指定旧条件现在是否成立”；`-1` 不蕴含某个已达成关系失效。Table 8 正好说明作者已经研究一般子目标撤销，且其子集准确率与 Table 6 全卷 F1 不能直接作升降比较。我们从 Table 6 可以立“下降方向仍有原生错误”的**已有领域问题**，尚不能立“强方法在 H-D 上失败”的**本项目方法缺口**。Robo-Dopamine Forward 是这张原生试卷的同卷强比较；R²VLM 仍是会动态更新步骤状态的关键反证候选，但把它迁入 RoboPulse++ 属于另行标明的域与接口适配。

在同卷上也有一条更直接的**方法—任务—输出—材料**绑定：PRM 论文实际把 RoboMeter 的逐时整体进展曲线按附录 C.4 的方向规则与 RoboPulse++ 的人标 Rising/Falling 比较；本地原始 `ep621` 的任务文字、`[22,28)` Falling 区间、发布帧及 ViFailback 原视频映射都已落盘，[`ep618` 对照](prm_robopulse_scope_review.md#4-ep621-与-ep618-能说明什么)也同样可查。可复用的是**原生区间方向真值与任务/媒体绑定**，尚无这两个 episode 的 RoboMeter 原始曲线或作者逐例对错。ContextProgress-Bench 则可按原生进展检验合法撤回的语义：已绑定的 `RMBench/place_block_mat/episode1` 的任务明说先把红块送绿垫，再送回蓝垫，六段标签与 1056 帧视频可追溯；送回后 red-on-green 变假，却是正确推进。这条绑定也是具体任务—输出—材料入口，不是模型错误。R²VLM 的 ALFRED/Ego4D 与 RoboMonitor 四监督任务有不同输入／输出；用这些汇总数字给 RoboPulse++ 的同一逐条件“考题”排位会改变原生任务。

证据等级因此固定为：**A** 作者原生任务已报告的进展方向、整轨失败或进展数值误差；**B** 同一原生任务中未单独报告的“旧成果失效／保持／合法撤回”子类；**C** 本项目新增的逐条件成立／失效／未知输出。A 可直接引用为领域困难，B 要先绑定逐例预测和任务语义，C 须预先声明适配，不能以原法没有该字段记错。ep621/ep618 只提供执行现象和单人关系观察，没有任何强法在其上的预测。ProgressCompass 已完成步骤固定仅是待检实现边界，R²VLM 可更新状态是反证。

### 7.4 已固定的最小下一步

先在**同一原生 RoboPulse++ 方向试卷**取得 RoboMeter 与 Robo-Dopamine Forward 至少同一小批 episode/区间的逐例原始预测，连同正确对照、拒答和失败一并保存；纳排只依作者任务/标签/来源，在看输出前固定，按 episode 计独立单位。已查 [PRM 官方固定仓库的 `eval/results/`](sources/prm_scope_review_20261003/official_repo_tree.json)仅有 `.gitkeep`，论文 Table 8 未给逐例文件；所以本轮只能完成**作者汇总成绩诊断**，不能构造共同错题矩阵。精确权重未在本机确认且本轮禁止新权重下载，不以通用 Qwen 代跑。下一件可独立执行的材料动作是按[同任务原始索引](benchmark_first_gap_screen_20261003.md#2-与-h-d-相关的具体可核查线索)，有界核 `ep513` 及 `ep510/514` 的原媒体和指令，先判其能否实例化 H-D；即使合格，也仍需原法逐例预测才算方法证据。若不合格按预定规则排除，不从上升后下降的标签强造旧成果失效。

否定本项目直觉的最直接结果是：同权限前缀、可辨对象和已核任务要求下，相关强法的原生输出／**明示适配**能把真正失效、后续失败但旧成果保持、合法撤回和遮挡未知区分好；或所谓错例全由图像识别、不可见性、输出映射引起。此时不设计新架构。当前仍未取得“强方法在目标问题上的不足”证据；只有作者原生汇总错误及设计疑问。单人开发不报正式准确率、H1/BCY/显著性，S6-draft-4、S7-screening-4 与阶段 8 状态不变。

### 7.5 哪个对象最像 EvoNav 论证中的 Open-Nav（D068）

这是**研究角色**而非系统功能一一对应。Open-Nav 是同一导航大任务上的完整零样本代理，已有指令分解、轨迹历史进度估计和动作决策；其主要贡献是把开源 LLM、空间感知、候选航点与时空推理组织成可运行架构，**不是首创使用轨迹历史**。[Open-Nav 原文 §I、IV](https://arxiv.org/html/2409.18794)自己引用了更早的历史建模和进度估计工作。EvoNav 的后续切入是在相同导航任务中提出较窄的反馈／前瞻决策问题，但并未量出该错误子类的发生率。

在机器人操作进展监测中，**RoboMeter 是最接近的宽任务基底**：跨机器人与任务训练，单轨原生逐帧输出整体进展和成功，两轨还给偏好；作者将它用于奖励评估、失败检测和机器人学习。[RoboMeter §III—IV](https://arxiv.org/html/2603.02115v2)；[固定源码](sources/direction_selection_20261003/eval_server.py)。它是专用奖励／进展模型，**不是** Open-Nav 那样包含导航决策的完整代理，因此类比只在“较宽原生任务上的已发布基底”成立。[PRM-as-a-Judge 1.5](https://arxiv.org/html/2608.14284v1)更像可比较多种进展 judge 的宽评测框架／试卷，不是单个待改监测器。

**ProgressCompass 已是针对 RoboMeter 等 PRM 的一个现成窄问题解法**：论文直接量化缺任务上下文时的进展误差并在冻结 RoboMeter 外加组织过程；其“上下文缺失”不能被我们重新包装成未解决空缺。[ProgressCompass §3—5](https://arxiv.org/html/2609.36684v1)。R²VLM 则是以递归推理解决长时程进展估计的另一种强架构，不能被假设为只记录完成而不会更新。[R²VLM §3](https://arxiv.org/html/2603.17312v1)。

若要使我们的故事真正对应“EvoNav 相对 Open-Nav”，应在 RoboMeter/RoboPulse++ 的**原生进展判断任务**里确认一个后续操作改变旧成果的**同任务错误子类**（B），并比较强方法的逐例预测。若最后需要监测器额外回答“指定旧条件当前真假／未知”，那是有价值但**新增的输出任务**（C）；原生整体曲线不能合法映射时，不能用它宣称 RoboMeter 原任务失败。选择宽基底让可检验的情形更多，却不自动让发现缺口或证明改进更容易；证据仍须落到同任务、同输入、同输出的错例与正确对照。
