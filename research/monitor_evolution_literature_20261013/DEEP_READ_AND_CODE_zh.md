# 五篇最接近工作精读与只读代码核查

2026-10-13。证据标记：P=论文方法/实验明确描述；C=当前作者源码实际看见；S=论文建议但未实现；H=本项目的推测/拟议适配。P不等于本机复现，C不等于已验证完整运行。这里只检查方法链条与少量源码，没有导入或执行下载代码。

## 1. Model-Based Runtime Monitoring with Interactive Imitation Learning

Huihan Liu、Shivin Dass、Roberto Martín-Martín、Yuke Zhu；ICRA 2024。预印本2023，DOI 10.1109/ICRA57147.2024.10611038。[正文](https://arxiv.org/html/2310.17552v1)，[作者页](https://ut-austin-rpl.github.io/sirius-runtime-monitor/)。

**P，实现链条。** §III-B：图像/本体状态编码为潜空间；BC策略和cVAE动力学联合训练，然后在冻结潜空间上训练LSTM失败分类器。接管前状态表示人的不理想/风险判断，三类区分正常rollout、失败、接管。§III-C：用模型与策略预测多个未来，检测OOD与失败概率，并以历史重复预警过滤瞬时噪声。§III-D：收集状态、动作、下一状态、接管标记，累积各轮数据重训。§IV-A首轮全程人工监控；后续策略也变。§IV-B另外用预测区域IoU和到接管的时刻距离单测错误预测器。

**能借：** 累积数据→下轮监控器，且整体策略成功与Monitor单测分开。**须改：** 接管标签只能解释人的风险，不能直接监督指定入口/平台真值；主比较固定策略/记录流，避免策略同步改善掩盖Monitor作用。历史重复过滤可减少误报，也可能抹掉短暂失效，应测撤销延迟。

**C，代码边界。** 本轮再次点击原项目Code，实际到[UT-Austin-RPL/sirius-fleet](https://github.com/UT-Austin-RPL/sirius-fleet)。不能称已经检查ICRA原版逐模块一致代码，更不能称已复现原版。

### 后续 Sirius-Fleet 是更直接的工程借鉴

[正文 §3.1、3.2.1/3.2.2](https://arxiv.org/html/2410.22689v1)，[CoRL2024/PMLR2025正式记录](https://proceedings.mlr.press/v270/liu25g.html)。P：共享视觉世界模型；任务特定的失败分类器训练于冻结表征。最新部署轮的接管前片段微调失败分类器；累积部署表征经PCA/k-means更新OOD边界，门限随干预比率适应。策略也按轮更新。该边界适应不是LTT式证书传播风险检验。

C：仓库快照commit `f972859882a292becc2ba4dba7c71916a1b6d671`：

- [README](https://github.com/UT-Austin-RPL/sirius-fleet/blob/f972859882a292becc2ba4dba7c71916a1b6d671/README.md)：失败分类器训练需已有 `intv_labels`；明确有 `--classifier_ckpt` 续训入口。文档并没有替我们解决新条件标签的独立核验。
- [error_detectors.py](https://github.com/UT-Austin-RPL/sirius-fleet/blob/f972859882a292becc2ba4dba7c71916a1b6d671/robomimic/scripts/ed/error_detectors.py)：`SiriusFleet_OOD`、`SiriusFleet_Failure`、`SiriusFleetCombined`，分别预警与组合；组合可共享embedding。
- [failure_classifier.json](https://github.com/UT-Austin-RPL/sirius-fleet/blob/f972859882a292becc2ba4dba7c71916a1b6d671/robomimic/exps/templates/failure_classifier.json)：分类训练配置确实存在。

H：可借数据版本/分类器续训接口；换成本项目masked多条件标签时，还需实现对象绑定、义务状态、证据质量及因果数据接口。现有Linux/机器人栈依赖不是本机现成实验能力。

## 2. Hierarchical Task Decomposition for Execution Monitoring and Error Recovery

Christoph Willibald、Dongheui Lee；2025在线，IJRR 2026，45(3):369–396；DOI 10.1177/02783649251352112。[正文](https://arxiv.org/html/2505.04565v1)，[DLR公开记录](https://elib.dlr.de/215291/)。这是本轮新增、直接符合部署反馈更新监控组件的研究。

**P，实现链条。** §3.1初始示范，经BNG-IRL分段形成技能与Task Graph。§3.2自主执行时人可施力帮助，合并纠正与执行数据修正技能运动和异常模型。§6.1以末端相对位姿为输入，GMM/GMR预测速度/力及协方差；在熟悉输入处检测测量与预期的Mahalanobis距离异常，低输入似然另作知识不足处理。§6.2子目标区域监测另负责技能正常结束。§3.3未知恢复情形请求示范，分段后加进任务图。§7.3.5展示人增加力后下次执行模型改变。

**能借：** （1）不确定需要更多知识，异常需要处理，两者不等价；（2）技能约束、子目标达到、任务选择各有接口。**须改：** 本项目训练输入是视觉前缀，不能把论文的实时力/位姿偷偷给学生；预期力分布不是独立几何条件证书，更新技能也不是我们的固定策略实验。

代码检索检查正文、出版页面和作者机构入口；**未核实官方完整可下载实现仓库**。论文含实现与机器人实验不等于本轮核查了源码。不要用第三方笔记补成“官方代码可直接复用”。

H：借语义组织，不首版引入整套BNG-IRL/运动学习。固定少量合同即可测试条件、当前成果和剩余义务是否必须分开；若未来要学任意任务图，需要另列监督与成本。

## 3. ConditionNET: Learning Preconditions and Effects for Execution Monitoring

Daniel Sliwowski、Dongheui Lee；RA-L2025，10(2):1337–1344，DOI 10.1109/LRA.2024.3520916。[正文](https://arxiv.org/html/2502.01167v1)，[作者页](https://dsliwowski1.github.io/ConditionNET_page/)。它直接否定“以往Monitor不检查行动条件”的宽泛主张。

**P，实现链条。** §III-A监督来自动作描述、成败与人工pre/core/post分段；用准备与结果段构造pre/post对。§III-B借动作关系增广，例如pick的pre可对应place的post。§III-C/D冻结DINOv2/CLIP，训练State/Condition Transformer及一致性目标。输出当前观察为动作的precondition、effect或unsatisfied。§III-F用行为树提供当前预期状态，预测与预期不匹配才报告异常；core阶段暂停异常判断，连续8帧过滤误报。

**能借：** 小条件模型，以及“物理/动作状态”和“当前预期”比较。**须改：** 三类是动作条件表示，不是多个条件独立真假与需求头；阶段人工标签不能冒充实际通行/指定承载证书。我们须覆盖中间条件反复失效，并独立判断成果仍有效还是仅历史曾完成。

重要适用前提：§IV-A数据假设机器人是影响场景的唯一代理、异常视觉可区分；虽有实际干扰展示，不能推出对任意环境条件变化均验证充分。core暂停可能降低难例覆盖，比较时不能只算有预测帧的准确率。

代码状态：作者页有数据/视频与出版引文，本轮未核到模型官方仓库；页面底部网站模板源码链接是网页模板，不能当ConditionNET模型代码。

H：在相同冻结特征上，加多条件truth头、效果valid-now头与任务义务接口；对照方法都需相同接口。若固定特征无法识别入口/支撑几何，小头更新可能无效，需先验证表征可用性，再决定适配器是否值得。

## 4. ARS: Agentic Reward System for Robot Learning

2026-09预印本。[正文 §3.1–3.7](https://arxiv.org/html/2609.34484v1)，[作者仓库](https://github.com/midea-ai/ars)。这是与已有变化先行、事件提议/核验、进度回退架构最重合的一篇。

**P，实现链条。** 输入离线全录像与任务指令，按需视觉检查；子agent提议事件及区间，主agent另取证据核验。事件证据须覆盖区间，修改会撤销确认、要求重核。基于确认事件编辑逐帧进度；允许局部退步并保留部分成果。终局标签只约束完成，不抹平中间差异。下游策略学习已实现；用审计痕迹训练奖励模型是§3.6提出的可能用途，未展示我们的条件学生闭环。

**能借：** 证据覆盖检查、证据与事件版本关联；将改事件后的旧确认作废。**须改：** 两个agent可共用一个VLM，所以独立推理上下文不构成独立物理真值；本项目真实交互/日志/人工标准必须另设来源。在线前缀学生不能调用全录像的后续检查工具。

C：当前官方仓库commit `0911830e6f4ced948b9df0435308812905cd7a98`：

- [session.py](https://github.com/midea-ai/ars/blob/0911830e6f4ced948b9df0435308812905cd7a98/agent/session.py)：`add_observations` 的 `_observation_asset_coverage_blocker`；`confirm_observations`；`read_observations`在progress阶段只读confirmed项；存在区间/证据要求的执行逻辑。
- [trajectory_outcome_ground_truth.md](https://github.com/midea-ai/ars/blob/0911830e6f4ced948b9df0435308812905cd7a98/agent/prompts/trajectory_outcome_ground_truth.md)：终局成败不指定发生时刻或可见原因，要求证据不足时表达不确定。
- [progress提示](https://github.com/midea-ai/ars/blob/0911830e6f4ced948b9df0435308812905cd7a98/agent/prompts/stages/progress.md)、[challenge提示](https://github.com/midea-ai/ars/blob/0911830e6f4ced948b9df0435308812905cd7a98/agent/prompts/stages/challenge_observations.md)：读取后作为可复用设计参考，未运行。

H：ARS做三种不同对照：完整录像离线教师；只给前缀的接口适配（必须命名ARS-prefix，不能称原版结果）；同一学生吃ARS教师标签。三者检验问题不同。原始开放式VLM教师也可能正确理解入口，所以不能预设其一定失败。

## 5. Wild Visual Navigation（WVN）

原RSS2023系统及2024扩展；[扩展正文](https://arxiv.org/html/2404.07110v1)，[官方代码](https://github.com/leggedrobotics/wild_visual_navigation)。它是辅助通行预测/导航系统，不是任务进度Monitor，但物理后效监督历史视觉与小头更新的重合非常实质。

**P，实现链条。** §3.3.1把实际/期望速度差经平滑与sigmoid转成平台相关通行评分。§3.4通过短期Supervision Graph保存足迹与分数，重投影到历史Mission Graph图像，关联区域特征。§3.5冻结预训练视觉表征，在线学习小通行网络与重建置信模型，供局部规划。未走区域用0目标与置信权重作保守学习，而不是可靠物理负事实。

**能借：** 时空对应与带版本的历史监督；异步学习/部署快照。**须改：** 速度误差受控制器、平台与地形共同影响，不直接等价于任意物体的几何可通行性；本项目未观察区域须unknown/mask，不能移植其保守0损失后声称取得可靠负例。

C：代码commit `3d6d9d95d3b322956de4e9294e04639cfe30b3cd`：

- [SupervisionGenerator.update_velocity_tracking](https://github.com/leggedrobotics/wild_visual_navigation/blob/3d6d9d95d3b322956de4e9294e04639cfe30b3cd/wild_visual_navigation/supervision_generator/supervision_generator.py)：实现速度误差、滤波、通行评分与阈值。
- [TraversabilityEstimator.add_supervision_node](https://github.com/leggedrobotics/wild_visual_navigation/blob/3d6d9d95d3b322956de4e9294e04639cfe30b3cd/wild_visual_navigation/traversability_estimator/traversability_estimator.py)：加入体验节点、寻找历史视点、更新投影mask及监督。
- [TraversabilityLoss.forward](https://github.com/leggedrobotics/wild_visual_navigation/blob/3d6d9d95d3b322956de4e9294e04639cfe30b3cd/wild_visual_navigation/utils/loss.py)：已标区域和未标区域分开，未标损失乘 `1-confidence`。源码支持上述保守学习解释。

H：本项目不需要搬入整套ROS/导航图；先借“事件日志关联观测”数据结构。若没有相机标定/物体追踪，对应本身就是未解决成本，不能说直接可用。

## 新补充的 GCR：比泛化奖励先例更贴近监督者反馈更新

[GCR §V-A、V-D、VI，v2](https://arxiv.org/html/2410.19989v2)，[作者页](https://gcr-robot.github.io/)。P：离线成功视频训练时序目标和成功目标表征；在线失败尾部占比β的图像进小replay buffer，形成goal-contrastive负目标，不断微调未冻结的LIV/ResNet-50。五进程包括RL actor/learner、内在奖励learner/predictor和外在成功predictor。真实成功由分割启发式/GPT-4V等估计，不能当绝对真值；没有核实官方实现仓库。

能借：专门保存“模型高分、实际不成”的错配案例，和冻结奖励/在线奖励更新对照。须改：失败尾段是控制奖励学习数据，不能搬来标物理条件false。它说明“策略找出评价器漏洞，再用执行结果修正评价器”不是新闭环。

## 更早的 ThriftyDAgger 源码补核

[正式论文 §4.2–4.5](https://proceedings.mlr.press/v164/hoque22a/hoque22a.pdf)。P：Q估计当前策略的折扣目标到达概率，机器人/人转移给TD目标；每回合更新策略和Q，门控预算来自历史风险/新颖性分位数。不是失败轨迹每帧硬标签。

C：[thriftydagger.py](https://github.com/ryanhoque/thriftydagger/blob/5f4aec2db6b6860620fb8cd9c486bbaef878c07a/thrifty/algos/thriftydagger.py)，commit `5f4aec2db6b6860620fb8cd9c486bbaef878c07a`：`compute_loss_q`/`update_q`存在；qbuffer储存观测、动作、下一观测、成功指示、终止标记。检测器与策略共同更新已有实代码，不只摘要声称。

## 可复用程度结论

可立刻用于**设计借鉴**：反馈记录/版本、因果窗口、未知mask、成果/约束语义、回放与快照。已有官方源码可进一步适配：Sirius-Fleet、WVN、ThriftyDAgger、ARS。它们都需要数据接口和依赖转换；不支持“复制即可完成新Monitor”的承诺。其余“论文实现”与“本轮没有找到官方代码”始终分别记录。
