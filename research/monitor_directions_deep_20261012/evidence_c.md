# 主线 C：预测型 Monitor 的独立核查与研究设计

核查日期：2026-10-12（北京时间）。本稿是调研及实验设计，没有训练、模型下载、租机、机器人操作或复现成绩。读取了讨论起点、2026-10-09 项目诊断及 2026-10-10 ARS 独立核查；旧免训练约束不作为本轮要求。本轮使用 nature-academic-search 的多源检索流程；技能目录的 academic-search `search_papers` 等工具未暴露，实际使用联网检索发现及 arXiv/作者项目页/官方 GitHub 深读。结论来自下面可定位的一手来源。保存的 HTML/官方 README/部分代码、哈希与 GitHub tree 快照在 `c_sources/`；公开材料可读不代表已复现。

## 1. 结论先行

**预测方向存在价值，但当前不宜直接确定为主线。** “未来特征预训练后少量标注训练监测器”已有 RoboMonitor；“冻结世界模型加小头预测风险”已有 FARM；“待执行 action chunk → imagined future latent → 执行前风险/否决”已有 ContactGuard；“长任务前缀与下一动作块预测终局失败”已有 Foresight；“视觉模型给想象轨迹奖励再训练策略”已有 World-Gymnast、GenRL 及更广泛模型式 RL。泛称 world model、轻量预测、提前监测，都不能建立区别。

在资源有限、已有基础只是视觉前缀监测且尚未形成可靠感知的情况下，C 最值得保留的是一个**可降级的诊断问题**：在固定技能和明确时域下，局部环境条件失效与恢复是否要求动作条件预测，还是可靠当前状态/关系判别已经足够？先用独立仿真真值与配对执行回答，再决定是否投资预测模型。即使证明预测有净收益，也仍需与 ContactGuard、Foresight、CaM、STRIPS-WM、RAFAIL 比较监督、泛化和下游行为，不能把“可逆前提”写成已确认空白。

## 2. 五种“预测”必须拆开

| 设置 | 部署输入权限 | 输出义务 | 监督来源与更新参数 | 下游接口 | 与当前项目的关系 |
|---|---|---|---|---|---|
| C1 未来特征用于预训练 | 目标＋因果图像窗口；部署可不读动作 | 当前阶段、失败、完成 | 无监测标签的视觉－状态－动作轨迹训练表征，再小量监测 SFT；可更新 LoRA/编码器/小头 | 执行中恢复或离线标注 | 输入合同可以保持；RoboMonitor 已很接近；属于 A 的表征学习路线 |
| C2 动作/技能条件后果预测 | 目标＋prefix＋**待执行技能身份/控制器或动作块**＋时域 | 某关系是否保持、技能失败概率、后果分布 | 真实/仿真转移、局部结果标签；冻结表征、小预测器或 readout | 执行前 veto、技能候选选择 | 明确增加权限；不能用仅视频目标方法的性能直接对比 |
| C3 视频生成世界模型 | 当前图像/短史＋待执行动作序列 | 未来像素轨迹 | 大量动作条件视频及基础预训练；训练/适配 dynamics | 造数据、模拟政策、规划 | 本身不是 Monitor；生成未来不自动给任务评价真值 |
| C4 评价想象轨迹 | 目标＋**模型生成的未来轨迹** | 想象中的完成/约束/奖励 | VLM、任务奖励、少量人类评价；预测器和评价器可能独立 | 规划/模型内 RL | 不是“真未来可见”；只可评价模型假设，需独立真环境验证 |
| C5 后续成功概率/风险价值 | 目标＋prefix；可另给策略身份、动作/技能；必须限定后续策略、预算和扰动分布 | P(success by H\|history, policy)，或 Q(history, action) | 多次 rollout 终局、TD/蒙特卡洛；更新 critic/readout | 干预、采样/数据筛选、RL | 是策略条件量，不能等同物理准备状态或局部变化的正负作用 |

数学上，当前状态事实是 `p_t`；局部变化是 `p_t−p_{t−1}` 或建立/撤销事件；后果是 `P(p_{t+H}|h_t,u)`；后续成功是 `V^π(h_t)`；动作优势是 `Q^π(h_t,u)−V^π(h_t)`。这些量可以相关，但不互相定义。例如入口打开是可执行前提；弱策略仍可能失败。关盖撤销入口准备；最终成功轨迹仍可能包含这一步。预测高终局失败概率也不证明当前变化有害。

没有待执行动作/策略的信息时，同一目标及同一视频前缀可能接上不同未来。能够定义的是某个训练/部署分布下的预测，不能宣称从前缀识别唯一反事实后果。新方法若读技能/动作，主对照也应读相同信息；仅目标＋prefix 方法保留为权限较少的参考臂。

## 3. 最接近研究的正文证据链

以下每篇概述保持简短；后面的实验方案和选择判断是本稿独立分析。Q＝作者量化实验，C＝作者案例，M＝机制/方法定义，H＝本稿假说，不能互相替代。

### C-S1 RoboMonitor：预测表征并不意味着部署预测

[正文 IV-A/IV-B](https://arxiv.org/html/2609.30715v1#S4)：M，动作条件未来特征、逆动力学及 masked-present 学习表征；随后因果 Temporal SFT 学当前 phase/failure/completion。IV-A 明确部署弃用 future predictor。Q，[表 I 与 VI-A](https://arxiv.org/html/2609.30715v1#S6) 的 52 episodes 结果中，failure AP 为45.87，低于 Robometer59.39；优势并非所有输出一致。V-E 报告预训练8 H100，SFT4 GPU。**重合判断：C1高度重合；C2运行时动作条件后果是能力扩展，但已被其他论文覆盖。**

### C-S2 ContactGuard：短期技能风险最直接的竞争者

[§3.4–3.5 与 §4](https://arxiv.org/html/2608.13438v1#S3)：M，黑箱策略给待执行动作块，冻结 latent dynamics rollout 到接触后时刻，小样本 logistic probe 在接触前 veto。Q，current-latent、直接 observation＋action、动作扰乱及同图换动作对照均已有，不能将这些实验本身称为新贡献。[§5](https://arxiv.org/html/2608.13438v1#S5) 限定于下一 chunk 的接触；abort 后恢复和完成留给外部模块。**重合：泛称低成本短期风险/外置冻结策略预测型 Monitor 为高度重合；多技能条件恢复是待验证扩展。**

### C-S3 Foresight：终局弱监督＋下一动作条件预测＋因果监测

[§3–4 与附录12.2](https://arxiv.org/html/2606.23085v1#S4)：M，观察史、下一 action chunk；冻结视觉编码器、训练 action-conditioned predictor，再因果 Transformer 输出未来终局失败分数。所有 timestep 继承轨迹终局标签，非局部变化标签。Q，hidden vs predicted latent 已比较，LIBERO-Long 的 Transformer AUC0.85→0.89；ManiSkill-Long0.81→0.83。§6 指出 WM延迟及校准分布变化限制。**重合：prefix risk、跨策略、终局标签、动作条件未来latent高度重合；不能仅通过改成短技能回避。**

### C-S4 FARM：冻结预测模型读出风险已经存在

[§III-B–F 与表III](https://arxiv.org/html/2609.11445v1#S3)：M，固定 VLA-JEPA predictive states，33,985参数读出；终局标签赋给每step，运行 max 聚合只看过去。Q，严格 unseen 的 pooled AUROC65.67，低于 seen83.70；target readout适应75.78。这是作者实测迁移差异，不能说无泛化。给出的0.2256ms是**已有WM state后的 detector开销**，非整套视觉/预测延迟。官方仓库当日仅 README“Coming Soon”。**重合：冻WM＋小头、前缀风险、readout适应高度重合。**

### C-S5 FoMo-FD：预测训练，但运行时是已观测转移异常

[§III-B/IV/V](https://arxiv.org/html/2607.27511v1#S3.SS2)：M，用成功示范训练 action-conditioned endpoint flow world model；运行时给**已经观察到的endpoint**做 inverse transport nonconformity，不要求采样未来。成功 rollout 校准阈值，固定/腕部各自评估。Q，视觉动作一致性与 prediction-error、observation OOD 有对照。**重合：模型式转移异常检测已有；与未来veto权限/时间点不同。不能把它的高检测率当未来预测率。**

### C-S6 Foundational World Models：异常不总是失败

[§V-D/VI、图7与表I](https://arxiv.org/html/2603.06987v1#S5)：Q，概率latent WM uncertainty优于预测误差；C，未持线缆阶段风险低，抓取尝试及落线缆风险升高。VI 明确良性背景变化会误报；真实线缆评估仅7 nominal＋9 failure，不能将高准确率泛化为通用能力。**剩余入口是任务相关与无关变化分辨，已有问题认识及解法，须实测而非宣称首创。**

### C-S7 RAFAIL：任务相关关系门控不是新概念

[§III 与 IV-C/表III](https://arxiv.org/html/2609.18324v1#S3)：M，离线VLM进度/关系重要性监督，点云关系表示＋关系专属OOD，运行时不调用VLM；预测重要性参与gate。Q，无importance gate时FPR11.6→69.8，balanced accuracy73.4→58.1，支持任务相关性对误报的作用。**重合：关系绑定、相关性抑制异常误报部分/高度重合；增加 RGB关系头不足以区别。**

### C-S8 STRIPS-WM：前提与effects已有学习框架

[§5、§7及附录C](https://arxiv.org/html/2606.06832v1#S5)：M，从image–high-level action–image学latent predicates及稀疏precondition/add/delete，再视觉蒸馏与经典规划。Q，去trusted missing negative pairs时，DinnerTable的谓词退化且planning为0%。§7 明确确定性、隐藏状态、新对象/动作参数泛化限制。**重合：学习可执行前提和撤销effects高度相关；概率、部分可见或新对象场景是能力扩展假说，未确认独立贡献。**

### C-S9 CaM：主动失败预防可以不生成未来

[§3 与 §4.5/表6](https://arxiv.org/html/2412.04455v1#S3)：M，时空约束＋部分/实体几何elements、VLM code＋tracking，检测可预见失败与已发生失败。Q，单视图65%→40%的消融支持遮挡/几何表示的重要性。**重合：前置条件、实体部件绑定、动态环境 proactive prevention已有；能用当下几何规则预防时，不必训练WM。**

### C-S10 RoVer：评分候选动作不是物理成功概率

[§3.2.2](https://arxiv.org/html/2510.10975v1#S3.SS2.SSS2)：M，frozen VLA提候选，PRM reward＋refinement direction选动作；偏好监督由候选离expert action的RMSE构造。current timestep多视图/状态＋候选动作为主要输入。**重合：执行前评分/筛选动作已有；如果研究物理后果，对照要检查专家距离和真实技能成功是否一致，不得将其PRM重命名成oracle action value。**

### C-S11 World-Gymnast 与 GenRL：世界预测与未来评价两模块

[World-Gymnast §3、§6、附录A.4](https://arxiv.org/html/2602.02454v1#S3)：M，action-conditioned video WM rollout VLA；VLM终局奖励训练策略；图像编辑增广、test-frame RL、交替更新WM/政策都已有。作者承认OOD initial frame及VLM hallucination。官方README与执行脚本有实现依赖。**重合：WM造数据＋VLM评价想象＋policy RL高度重合；训练成本包含生成rollout、评分、policy optimization。**

[GenRL §3.2–3.3、附录J](https://arxiv.org/html/2406.18043v2#S3)：M，foundation VLM与latent WM connector/aligner，从文本/视觉目标构造latent target并在想象中学policy。复杂行为仍需训练数据覆盖。官方 `agent/genrl.py` 有connector更新、imaginary ActorCritic及imag reward。**重合：想象轨迹评价/学习成熟；不是少量前缀监测自然增加一头即可完成。**

### C-S12 成熟机制与政策内部表示对照

[Sirius Runtime Monitor 官方方法页](https://ut-austin-rpl.github.io/sirius-runtime-monitor/)：2023已latent cVAE dynamics＋failure classifier，policy和dynamics未来rollout，human intervention状态监督并从部署数据更新。其官方Code目前指向后续 [Sirius-Fleet](https://github.com/UT-Austin-RPL/sirius-fleet)，不能将后续代码当2023精确版本。[SAFE](https://arxiv.org/abs/2506.09937) 以frozen VLA内部features小MLP/LSTM预测跨任务风险；[FAIL-Detect](https://arxiv.org/html/2503.08558v2) 是成功数据OOD＋conformal。[SayCan](https://say-can.github.io/) 使用skill价值函数与任务适用性选择技能；[Farid2022](https://arxiv.org/abs/2202.05894) 从sensor history学blackbox policy失败预测与PAC-Bayes误差界。**技能能否成功及风险校准不是新问题。**

### C-S13 终局风险与恢复的两个交叉近邻

[Self-Evolving Criticality §Method/附录6](https://arxiv.org/html/2607.28251v1)：终局结果学risk指导数据采样和policy routing；LIBERO/RoboTwin主要读取初始仿真state，非仅RGBprefix。**与C5下游筛选、B执行反馈交叉，输入权限显著不同。** 该稿当前[v2](https://arxiv.org/abs/2607.28251)已改题为 Policy-Level Recursive Self-Improvement for Embodied AI with a Criticality World Model；本轮按用户要求不探索RSI，只保留v1中的风险预测/输入权限近邻，不把该整套路线列为推荐。[B2FF表1/附录B、G.2](https://arxiv.org/html/2606.09258v1)：预想milestone＋recoverability selector；受控失败时刻切换与在线trigger分别报告，平均成功74.0与64.5；延迟trigger实测下降。**恢复与触发必须分开验；高恢复成功不自动证明monitor可靠。** 根任务另核查eVTA0/RLER2609.33653，TD式终局→intermediate success probability；C5应纳入，不在本稿复述未独立深读部分。

## 4. 逐项重合矩阵建议行

| 本项目拟议问题 | 最接近工作 | 问题/输出 | 输入/监督 | 机制/训练/下游 | 判定与必须改变的具体义务 |
|---|---|---|---|---|---|
| 预测预训练后可靠当前Monitor | RoboMonitor | phase/fail/complete接近 | g＋多相机prefix；训练额外actions/state | future/inverse/masked pretrain＋TemporalSFT＋orchestrator | 高度重合；需不同且有实测监督效率/泛化失效的研究问题 |
| 冻结WM小头risk | FARM/SAFE | prefix任务failure score接近 | WM/policy features＋trajectory outcome | 小readout、causal max、target适应 | 高度重合；换Qwen/JEPA/小头不够 |
| 预执行短时失败预测 | ContactGuard | 单chunk imminent outcome/veto | planned动作与precontact标签 | latentrollout＋probe；policy固定 | 高度重合；跨技能/可逆条件只能暂列扩展，并含闭环收益义务 |
| 长任务终局风险 | Foresight/eVTA0/RLER | futurefailure/value | prefix＋pending actions；terminal/TD | trainedpredictor＋causalrisk/calibration | 高度/部分重合依最终设置；不能以终局监督本身区分 |
| 成功数据WM异常检测 | FoMo-FD/Foundational WM | 已发生转移nonconformity | 成功示范＋actions/state；未来endpoint在检测时已知 | prediction/uncertainty/flow＋conformal | 高度重合；非任务局部作用判断 |
| 前提维持与撤销effects | CaM/RAFAIL/STRIPS-WM/ARS | 可执行、约束/关系变化、撤销 | geometricelements/pointcloud/predicates或RGB；监督各异 | code/gate/symbolictransition/eventverification | 部分至高度重合；需随机后果、独立局部标签、恢复决策有实证理由 |
| 评价模型想象并训练policy | World-Gymnast/GenRL | imaginedsuccess/reward | imaginedrollout＋goal | WM＋reward＋RL | 高度重合；应暂缓泛化组合提案 |
| 预测风险筛数据/采样 | Criticality/ARS | risk versus realisedprogress不同 | rollout outcome或事件progress；state权限不同 | importance sampling/段筛选→policy训练 | 部分重合；需要区分风险数据收集与坏动作片段去除 |

“完全/高度重合”指当前宽泛候选的机制义务；不是说所有论文与旧Monitor完全相同。最终候选尚无方法定义时不能精确给完全重合，更不能凭检索遗漏证明不存在。

## 5. 可保留的窄问题及最低成本诊断

### C-P1：局部前提变化怎样影响固定技能成功——先判当前，再问是否需要预测

H：任务准备状态与终局成功风险分开监督，有机会降低撤销/恢复场景的误触发。但这是假说，非新颖性结论。限定2–3个冻结技能（例如放入、放上、通行），skill版本及末端控制器固定；输入g、因果RGBprefix、skill ID和执行时域。部署不读sim真state，后者只生成独立真值和oracle诊断。skill标签来自局部执行结果；前提/撤销标签来自独立可见关系与状态事件，不从最终成败回填。

第一阶段只设计/收集可重复reset的3类环境条件（入口、承托、路径），每类准备/破坏/撤销/恢复/无关变化；独立新对象布局和camera split。可从每类20个初始状态开始，2种技能/控制器候选各重复3次，约360次短skillrollout；是最低诊断量而非预设论文统计充分性。后续按episode bootstrap不确定度扩样，按源状态/场景分组防止同状态候选跨train/test。

比较六臂：强VLM直接当下判断；同input learned current-state/关系head；直接`current feature＋action/skill`风险head；RoboMonitor式current readout；ContactGuard式futurelatent probe；简单几何/STRIPS前提oracle及可部署估计版。FARM/Foresight可在有合适公开interface时追加，不应假装已有模型可直接用。与旧4阶段链的比较仅作为历史参考；无模块必须保留。

竞争解释：

1. 固定同一可见状态，只改candidate action/skill；若预测不变或明显违背真实配对后果，它在读静态视觉风险。
2. 固定同一动作，只改任务关系或无关背景；测相关condition effect与无关novelty false alarm，避免把OOD等同失败。要比较RAFAIL/CaM已有相关性机制。
3. 给各臂相同visionencoder/labels/steps/feature维度，future模块与同容量direct头分别控制；action shuffle/zero/reverse检查动作信息；这些是必要实验，ContactGuard已做，不能作为独立创新。
4. 当前latent→futurelatent与**真实未来oracle latent**三者对比。若oracle有价值、预测无价值，瓶颈在dynamics；若oracle也无增益，当前状态足够或readout任务无效。oracle明确不可部署。
5. 同初始state下开→关→再开，真实技能同状态重复；risk应随当下可恢复条件变化；trajectory-max alarm与可撤销风险分别测试。先定义alarm reset规则；不要把FARM持续报警设计的风险聚合错称事实错误。
6. 冻结后续策略，另换技能controller评估policy shift；risk变化可能是policy改变，不是环境事实改变。拿掉skill/control身份一臂检验分布边际预测是否足够。

指标：局部前提/撤销F1、counterfactual action排序、skill outcome Brier/NLL/AUPRC、固定误报警预算下recall、能及时干预的lead time、同state变动作敏感性、OOD背景false alarm、推理总延迟。观察全部当前事实正确但未来head无优势，应将C降为A的可用当前状态监测；只有future head改善校准、排序且闭环提高任务完成/减少无效暂停，才支持预测贡献。

闭环的最低层面：固定策略/skills，不训练policy，只在同一实验预算中比较 continue、pause/retry、两候选skill选择。各臂采用同一个恢复器、干预预算与延迟；加入random/时间表/几何gate，分离“多次尝试自然提升”解释。若只有多次retry提升，预测不是贡献。即使veto可靠，若造成大量假暂停而总完成下降，也必须降级。完整论文还需第二任务套件、物体/关系组合外推、政策变化、遮挡、不确定性与成本，并检验新local监督比terminal标签或dense普通SFT的效率。

### C-P2：从异常预测转向任务相关风险校准——只有明确剩余失效才做

入口是Foundational WM已承认良性视觉变化误报，以及RAFAIL relevance gate的实证。可用成对背景变化/关系变化同时检验泛化和false alarms，保持相同执行结果与视图预算。若RAFAIL式gate或CaM可靠几何已解决，不能将“任务相关risk”独立成题。研究空间也许在观察不足、关系尚未验证时的可校准拒答/再观察成本，但active perception、conformal及selectiveprediction均有先例；必须进一步专题搜索，当前只列备选。

### C-P3：预测可恢复性或选择恢复——工程价值有、前置依赖大

ContactGuard不做恢复，B2FF已做recoverability-aware future-milestone选择且实测trigger误差影响。因此候选不应叫“monitor能恢复”，而应限定：在环境前提撤销后，何时继续原技能、先恢复条件、还是重规划；评价器与同恢复库的真实后果是否匹配。需要condition恢复skill及配对reset，输出选项后果而非只解释失败。没有skill/recovery库时先暂缓；它不是当前视频Monitor单独能支持的实验。

## 6. 数据、标注、计算与下游成本

| 路径 | 首个诊断需要 | 完整论文还需要 | 主要成本/风险 | 条件排序 |
|---|---|---|---|---|
| 当前state/conditionhead vs futurehead | 状态配对视频、冻结2–3skills、仿真reset、少量人工审读；可离线特征、小头 | 跨任务/物体/policy、独立标签、固定恢复闭环 | 感知错误先污染prediction；action接口尚未建立 | C中首选诊断，前提是已有可控skill环境 |
| 直接冻结WM readout | 合适开放backbone和准确actionmapping、terminalrollouts、小readout | strongsameinput对照、域shift及局部监督研究 | FARM未开代码；所有WM feature获取算力不能只算head0.2ms | 可基线，不宜单独创新方向 |
| 新latentdynamics预训练 | 同步RGB/动作/状态、随机后果覆盖及processor | 数据效率曲线、模型容量控制、多seed、closedloop | 冻backbone仍要训predictor；少标注不等于少数据/算力 | 视数据开放和资源定，暂低于小头诊断 |
| 视频生成WM＋VLM evaluator | 开放模型、动作标度、可信生成转移、evaluationgate | imag→real/sim误差、RL优化、rewardhacking、两个模型shift | WMrollout、VLMscore、policy优化都耗GPU；World-Gymnast脚本默认4GPU只是example配置非硬最低 | 资源有限应暂缓 |
| C5策略风险/TDcritic | 固定policy、多次rollout、明确horizon/终止信号 | policyevolution的更新和校准、采样/策略闭环 | eVTA0/RLER、Foresight、SAFE、Criticality接近；策略变化影响label | 与B合并评估，泛称成功预测不保留 |
| 恢复可达性预测 | 实际recoverylibrary与每个动作真实结果 | 多failuretype、recoverabilityrank、总完成和operatorcost | 需要下游技能集成，比仅offlineaccuracy贵 | 有环境/skill库时上升，无则暂缓 |

资源变化：如果只有单卡且无可执行skills，优先A的可靠当前判断及C的离线paired诊断，不能凭视频后缀建立行动后果因果真值。如果有仿真执行和reset、现成actionsdata，C-P1可与B并列小成本试验。如果已有robotfleet、开放可适配WM与较充足GPU，C-P3恢复风险或C4想象评价可信性研究才更具可行性。没有预算/投稿周期信息时不给录用概率，也不预设整条架构必成/必败。

## 7. 首次公开、阅读版本与开放状态（核查日2026-10-12）

日期按本次核实的arXiv v1提交日，阅读版本单列；不把conference年替换首发日期，也不保证没有更早非arXiv公开稿。已另抓取15个arXiv abstract页面核查版本历史，见`c_sources/version_check.json`。正文分析保留明确的阅读版；CaM/RoVer/FAIL-Detect/Criticality有较新版本，不能把以下旧版数字当作未注明版本的最新成绩。未确认表示论文/官方链接和标题定向检索未证实，非领域不存在。

| 来源 | 首次公开 / 本稿阅读版 | 材料开放证据 | 复用限制 |
|---|---|---|---|
| RoboMonitor2609.30715 | 2026-09-25 / v1 | 正文；未在论文/定向检索确认官方代码权重数据链接 | 无法按现成可执行方法估成本 |
| ContactGuard2608.13438 | 2026-08-13 / v1 | 正文与附录；未确认官方代码/权重/数据 | 自写复现需要WM、action对齐及labels |
| Foresight2606.23085 | 2026-06-22 / v1 | 正文全附录；官方项目链接工具不可达，不能确认代码状态 | 整套features延迟与新predictor需计入 |
| FARM2609.11445 | 2026-09-10 / v1 | [官方仓库](https://github.com/HaoranPei-casia/FARM)目前仅ComingSoonREADME；tree SHA4ba74386e8cb85e019baae418bfbf0e55bb42f61 | 不是已开放实现；无复現 |
| FoMo-FD2607.27511 | 2026-07-29 / v1 | 正文；未确认代码模型数据 | window动作信息必需；非future-onlyscore |
| FoundationalWM2603.06987 | 2026-03-07 / v1 | 正文、数据描述 | 数据描述≠下载开放；分布校准限制 |
| RAFAIL2609.18324 | 2026-09-16 / v1 | 正文方法与表III | 点云/segmentation接口明显超当前RGB |
| STRIPS-WM2606.06832 | 2026-06-05 / v1 | 正文/附录；A主线另核查官方材料 | 确定性/groundedoperators，需coverage |
| CaM2412.04455 | 2024-12-05 / 深读v1，当前v3(2025-03-21) | [CVPR2025项目页](https://zhoues.github.io/Code-as-Monitor/)；本次页未含可确认代码/数据下载 | ConSeg训练与多视图3Dtracking不能当纯prompt |
| RoVer2510.10975 | 2025-10-13 / 深读v1，当前v2(2025-10-14) | 正文/附录；未确认官方实现链接 | 以expertdistance为监督，action权限额外 |
| World-Gymnast2602.02454 | 2026-02-02 / v1 | [官方GitHub](https://github.com/world-gymnast/world-gymnast)、README、SETUP和run脚本已审；tree SHA59c83a6e121fc1e099b39a4d6e01421cf1aa55c7 | readcode不代表训练可运行；需要WorldGym/policyckpt/评分 |
| GenRL2406.18043 | 2024-06-26 / v2(2024-10-30)，NeurIPS2024 | [GitHub](https://github.com/mazpie/genrl)、[models](https://huggingface.co/mazpie/genrl_models)、[datasets](https://huggingface.co/datasets/mazpie/genrl_datasets)，README、agent代码已审；tree SHA4cd839470a30fbf23841b6930f900846d213c312 | InternVideo2基础权重需要HFaccess；任务范围非当前视觉约束集 |
| SiriusRuntime2310.17552 | 2023-10-26 / 官方项目方法页及PDF摘要 | 项目Code指向后续Sirius-Fleet；其README有intvlabels/worldmodel/classifier与data链接 | 后续实现不可充当2023精确复现 |
| SAFE2506.09937 | 2025-06-11 / 官方项目页和摘要，NeurIPS2025 | [项目页](https://vla-safe.github.io/)有Code；FARM已matchedbaseline | 需policy内部features，与policyagnostic input有别 |
| FAIL-Detect2503.08558 | 2025-03-11 / 深读v2，当前v3(2025-06-20) | 正文与附录已读 | sequentialOOD不是局部effectlabels |
| Farid2202.05894 | 2022-02-11 / RSS2022论文入口 | arXiv与RSS官方全文 | 表示成熟policyfailurepred问题已存在 |
| B2FF2606.09258 | 2026-06-08 / v1 | 正文全附录与分离onlinevariant结果 | 已有recoverabilityselector；trigger和recovery分开 |
| Criticality2607.28251 | 2026-07-30 / 深读v1，当前v2(2026-10-03)改题含RSI | 正文和完整补充 | 本轮仅列risk近邻，不展开RSI |

GitHub上述SHA是**tree SHA快照**，不是已核对commit SHA；本稿没有运行仓库。`c_sources/repo_trees.json`保存完整文件清单；`c_sources/manifest.json`保存HTML等原件SHA256。额外审代码：World-Gymnast `examples/run_openvla_oft_rl_worldgym.sh`第28–31/92/108行把worldgymBridge、4GPU、WMcheckpoint、rewardgamma接入RL；GenRL `agent/genrl.py`第7–25/39–59/108–123行连接representation、WM及imaginarypolicy。均只下载短文本源文件，未下载weights/datasets。

## 8. 给主报告的有条件推荐

1. **不保留为独立新题**：泛称预测预训练Monitor、frozenWM＋小head、nextchunkrisk、terminalsuccessprobability、WM造视频＋VLM评分＋RL。这些已有高度近同机制。
2. **保留最低诊断**：固定skills和明确H下，当前局部state/条件监督与未来后果监督是否有不同价值；pairedreset、sameimage不同action、current/directhead、actionshuffle、真实未来oracle、恢复后risk读出。仅当有机制增益且闭环优于同成本恢复对照时升级。
3. **C宜作为A/B之后或并行小诊断，而非先承诺完整WM路线**：当前漏变化、结构绑定与事实更新未解决；预测模块可能只是把这些错误传播到未来。若可靠currenthead就解决，收缩为A；若data/label获取因terminal归因受阻，与B研究可信局部监督的交叉更自然。
4. **窄候选仍需撞题**：跨skillpreconditions、可逆effects、relationgate、recoverability已分别有STRIPS-WM/ARS、RAFAIL/CaM、ContactGuard/B2FF先例。所谓区别必须用不同部署义务、输入权限、真实结果、跨对象泛化和成本预算实证，而不是换术语。
