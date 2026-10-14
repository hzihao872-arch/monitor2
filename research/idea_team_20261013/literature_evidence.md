# 文献机制与监督资源核查

2026-10-13，Asia/Shanghai。只读文献、作者网页及仓库；未训练、未评测、未运行仿真、未下载数据包或模型。旧快照复用自 `../idea_exploration_20261013/sources/`。以下区分论文声明、公开字段和本轮科研判断；并未穷尽文献或证明新颖性。

## 最影响推荐的判断

大规模配对续行不是唯一监督来源，但没有一种公开资源能直接免费提供“目标、入口、载荷、路径、条件有效期、撤销”的全部真值。最值得继续的机制是：实际局部后效提供有范围的条件证据，少量审核确定可回溯的有效区间，再训练未来只读前缀的条件监测者。它的研究价值须落实到稀疏证据何时可以安全扩展、跨场景适应、同人工时间下收益；普通规则传播加分类器尚不足以保证独立方法贡献。

## 强近邻矩阵

| 一手来源与阅读位置 | 输入和监督从哪里来 | 更新模块、依赖 | 对本轮候选的实质约束 |
|---|---|---|---|
| [ARS v1](https://arxiv.org/html/2609.34484v1#S3)，3.1–3.7；[作者实现](https://github.com/midea-ai/ars) | 整条离线轨迹+指令；可选终局标签/参考。事件由VLM提出，另一上下文核验；后来的画面可核实先前抓取。 | 无奖励模型训练；可编辑事件/进度曲线；代码已有agent/configs/scripts，当前读LeRobot v2.1 image字段。 | 回溯核验、撤销、事件表本身已有；3.6还提出audit traces作训练监督。新工作应使用独立物理事件与有范围证据，检验因果前缀学生和标签预算；ARS输出不能自动当物理真值。 |
| [Aff-Grasp / Learning Precise Affordances v2](https://arxiv.org/html/2408.10123v2#S3)，3.1；[ICCV正式论文](https://openaccess.thecvf.com/content/ICCV2025/papers/Li_Learning_Precise_Affordances_from_Egocentric_Videos_for_Robotic_Manipulation_ICCV_2025_paper.pdf)；[代码](https://github.com/Reagan1311/Aff-Grasp) | EPIC-Kitchens/Ego4D时间戳叙述；hand-object contact detector定位接触；homography/视觉对应投到pre-contact帧；SAM产生part masks。 | 训练视觉affordance模型；依赖已有叙述、接触检测、分割/对应及几何先验；代码区分ego2aff与affordance-learning。 | “后续交互给前接触状态提供自动监督”已有直接先例。其标签是抓取/功能部位，不是入口/载荷/时间有效期/任务撤销；检测误差仍是伪标签噪声。 |
| [ConditionNET v1](https://arxiv.org/html/2502.01167v1#S3)，III-A/B、IV-A；[作者项目](https://dsliwowski1.github.io/ConditionNET_page/) | 图像+action文字；每段skill有success标签和人工pre/core/post分段/anomaly。把pre与post帧组合为triplets，并借pick/place逆关系扩充。 | 冻结DINOv2与CLIP，训练状态/条件模块；执行需要skill phase和BT；core期暂停anomaly判定。 | 少量前后状态一致性、条件输出已有。pre阶段标签是阶段代理，不能直接解释为充分readiness；现成标注没有给每个入口/支撑条件的因果真值。 |
| [Relational Learning for Skill Preconditions v1](https://arxiv.org/html/2012.01693v1#S3)，III与附录 | 约100,000 pair-object仿真场景，施加局部扰动，记录位移、旋转、接触点/法向；真实任务少量前提标签。 | 物体体素/已知分解；先学关系表征，再冻结并训练前提头；真实数据需多相机3D。部分unstacking标签人工判关键支撑块。 | 后效监督学物理关系、少样本技能前提已经很早存在。不能把“交互→前提”作首次贡献；它的100k交互也不是现成免费标签。 |
| [CoINS v1](https://arxiv.org/html/2601.03956v1#S4.SS3)，IV-C/D、V | RGB/深度与skill能力参数；物体点云移除后重建traversability map，比较路径长度，生成约20k VQA。 | Qwen3-VL SFT；低层导航/交互技能另用PPO训练。 | 便宜教师来自几何地图和规划，并非大量实际counterfactual skill成功。搬到操作时接触/承载及机器人能力不可由map删除替代；已有强技能不是我方资源。 |
| [Robo-Dopamine 2.0 v1](https://arxiv.org/html/2608.15680v1)，3、A.1/A.2/A.5 | 指令、参考锚点、历史面板、before-after；成功轨迹来自RoboCasa/LIBERO/RoboTwin2/AgiBot，phase-aware editing产生robust/negative，400k signed pairs另加200k VQA。 | 训练general reward model；在线历史只读rollout prefix；下游RL中reward model冻结。 | 历史、非单调进度、负例与恢复、editing已覆盖。编辑算子预设符号不能未经核验用于新条件，也不能把它的大数据训练成本当我方小预算。未核实有完整公开局部证书数据。 |
| [MAGMA-GEN](https://arxiv.org/abs/2609.20056)；[作者方法页](https://magma-rob.github.io/magma-gen) | 当前agent失败rollout；privileged coach诊断并提局部修复；same-state matched re-execution实际改善下游后才保留监督。 | 产生recovery SFT样本；需要reset、执行技能及coach；全文HTML v1抓取404，本轮依据摘要和作者方法页，不宣称通读全文。 | 候选A“失败→修一个条件→重试→验证归因”已有极强近邻，还没有免除分支执行成本；不推荐当主线。 |
| [RoboReward v2](https://arxiv.org/html/2601.00675v2#S4)；[官方HF数据](https://huggingface.co/datasets/teetone/RoboReward) | 同一公开视频换任务指令；successful clip截断制造partial outcomes；OXE与RoboArena；54,135 video/task/reward1–5；test人工核验。 | Qwen3-VL 4B/8B微调；训练标签含VLM检查。 | 候选C“同轨迹换目标/截断”已有。可做外部数据与强基线，但字段没有独立局部事件/承载证据，不能用终局分数广播全前缀。 |
| [RoboMonitor v1](https://arxiv.org/html/2609.30715v1)，IV、V-A、VII | 25小时同步多相机/state/action用于predictive pretrain；52或100 episodes需dense phase/failure/completion标注；部署只读图像与指令。 | 预测表征预训练后Temporal SFT；在窗口内及重叠窗口监督/一致性。 | 少标签在线monitor已存在；仍需dense labels。候选应比较同预算普通Temporal SFT，而不是只比未微调大模型。单global phase也不同于分条件有效期。 |

## 可获得数据：哪些是真正的监督，哪些只是素材

| 资源 | 已核实可得内容 | 缺少什么、怎样使用 |
|---|---|---|
| [CALVIN官方dataset文档](https://raw.githubusercontent.com/mees/calvin/main/dataset/README.md)，State/Language章节 | 每步RGB/深度、7维actions/rel_actions；scene_obs24维含door/drawer/button/switch joint、两灯、三block6D pose；robot_obs15维含TCP、gripper width/joints/command；auto_lang_ann含task_id及start/end。D split166GB，debug1.3GB。 | 没有contact/force/支撑因果标签；状态可帮助核对部件未变/撤销，语言segment不等于条件有效期。未来可选少量真实play片段做证据审核，但本轮未下载，不保证debug有特定入口/承载例。 |
| [(Im)PerfectPour官方链接](https://drive.google.com/file/d/1hZkD2TG9LZhJLHb-JB-SZeuHdmBbSbRw/view?usp=sharing) | Drive可访问名ImperfectPour.zip；作者论文称406成功/138失败、两相机、pick/pour/place/wipe和人工phase/anomaly标注。 | 未下载zip，内部schema未核实；可作为有稀疏到段级人工标签的真实素材，不能声称有入口/承载/替代路线真值。 |
| [Aff-Grasp作者代码/数据入口](https://github.com/Reagan1311/Aff-Grasp) | ego2aff与学习代码、数据/模型链接；产物为object crop+graspable/function masks。 | 不是robot action-aligned execution feedback，不直接有任务准备/撤销监督；主要借用interaction-to-earlier-observation机制。 |
| [LIBERO-Recovery作者仓库](https://github.com/liulin815/LIBERO-Recovery) | 代码及ModelScope三入口：scene states、human recovery expert、pre-failure history；README描述接触/夹爪change时刻等eval输出。 | 顶部明确完整scene/data将2026-10-20发布。当前项目页2,178/3,184统计与论文v1数量不同；不可把完整数据当已拿到。字段完备性、配对对应关系未下载核实，不能主依赖。 |
| [RoboReward官方HF](https://huggingface.co/datasets/teetone/RoboReward) | 54k真实robot video、task、末端reward及自动检查；可公开检索。 | 没有phase/atomic relation/contact witness；可用于外观或task-alignment，局部监督仍需新审核。 |

## B候选必须说清的逻辑边界

1. 成功穿过入口只支持当次对象、姿态、路径与通行时刻的条件。进入时把盖推开、入口形变或物体转向，就不能把结论回推到早先状态。
2. 释放后稳定只证明当次载荷和稳定窗口。须排除机器人仍承托、隐藏支撑或其他接触来源；不能推成所有对象/所有controller均可放稳。
3. 未改变相关几何/支撑关系须由外部状态或少量人工边界审核确认，视觉“看着没动”不足。只推到最近可信变化点；遮挡或身份不确定时停止。
4. 技能失败不证明目标条件为假。false来自直接反见证，其他样本保留unknown；成功数量也不自动给出校准成功概率。
5. 若完整仿真oracle本来就能逐帧自动标，回溯机制在该域并不节省标签。完整oracle必须作为强对照；真实/新条件域预算比较应按人工审核分钟、独立证据单位，而非生成帧数。
6. 相同预算至少比较直接人审挑状态纠错、event-frame-only训练、证书frame nearest-neighbor、naive whole-prefix broadcast、普通phase/Temporal SFT；复杂模块胜出才能说需要它。标签选择规则可以成为数据设计贡献，但单规则不能保证方法论文新颖性。

## D备选：成功反证过强必要条件

直觉正确：目标起初未完成，独立目标成功且完整轨迹中条件c一直为假，足以否证“完成此目标必须曾满足c”；不否证某条路线/技能需要c。失败没有对称的必要性证明。主要难点是完整absence核验和发现真实多路线成功，而不是逻辑式本身。

两个强近邻：

- [Stern & Juba，IJCAI2017](https://www.ijcai.org/Proceedings/2017/0615.pdf)：成功轨迹学保守action model；成功应用前不存在的literal不能作必要前提。更早[Wang1994作者PDF](https://www.cs.cmu.edu/~mmv/papers/darpa-planning94.pdf)已用观察/practice删除不必要preconditions。
- [Thomason & Kress-Gazit，arXiv2105.06537](https://arxiv.org/abs/2105.06537)，正式[TRO2023 DOI](https://doi.org/10.1109/TRO.2023.3294918)：由少量controller执行观测持续修正symbolic-geometric abstraction，冻结执行者与条件修正并不新。

全任务“所有成功方案都曾满足c”对应[planning landmark定义](https://www.aiinternational.org/Papers/JAIR/Vol22/JAIR-2208.pdf)。D潜在差异只能是视觉监测者提出的goal-vs-route necessity claim及反馈校准、减少过度拦截；当前未确认多路线成功数据，单入口场景不支持侧口故事。保留为备选或B中的负necessity反馈，不以逻辑反证声称首次贡献。

## 与HER、TD、RUDDER的区别

HER用达成状态改写目标、TD传播value、[RUDDER](https://papers.nips.cc/paper/2019/file/16105fb9cc614fc29e1bda00dab60d41-Paper.pdf)重分配return。B是有条件的事实标签与有效期；其独立事实证据不能由return贡献分析代替。这个区别避免了错误归因，但不证明它比已有监督传播方法新。

## 检索与核查范围

遵循nature-academic-search的multi-source-search流程。该skill所列academic-search专门MCP未挂载，使用一手arXiv/作者仓库/官方数据网页，另用已连接Undermind语义检索（先orientation、list_workspaces、inspect_folders）发现MAGMA-GEN、Aff-Grasp和abstraction-repair，再回一手来源。没有启动深度搜索或额外子agent。Undermind对Counterexample-Guided Repair年份显示2021；这是preprint年份，正式TRO是2023，DOI核对后在上面分开标明。未核查全文的来源已在行内标记。
