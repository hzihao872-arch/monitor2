# 文献证据入口（非候选排名）
检索截至2026-10-10；新颖性只能报告已查范围，不能由未找到排他证明。近期条目默认 arXiv preprint，除明确标注的会议/期刊。本文件供fresh审阅直接检查原文与本地事实。
旧材料：D:/monitor2/research/prerequisite_monitor/ars_independent_audit_20261010/ARS_INDEPENDENT_AUDIT_20261010_zh.md 与 SOURCE_MANIFEST.json；全文及全部表已缓存。新 sources/*.html 是本轮抓取正文；搜索 raw receipts 在 sources/aris_*.json。
字段/标签映射尚未用户确认。下列摘要只列相关机制，不宣称尚未被覆盖。

| 文献 | 身份与原文 | 与候选有关的已检查机制 | 本地证据 |
|---|---|---|---|
| ARS | arXiv2609.34484v1, 2026; https://arxiv.org/html/2609.34484v1 | 目标感知事件提出，自适应视图，独立上下文核验，编辑事件，准备/部分/撤销，离线分块BC。炉灶开后关明确案例；没有公开充分代码/prompt。不能称只评价目标物。 | 旧审计ars_v1.html、ars_v1_text.txt及17表分析 |
| VICtoR | Hung et al., 2024 arXiv版本/后续出版身份见审计; https://arxiv.org/html/2405.16545v2 | 给定任务与对象/状态/动作词汇及环境生成任务知识，然后识别视觉阶段；开盒/开抽屉先导已有。 | 旧审计正文 |
| ConditionNET | Sliwowski & Lee, RA-L2025; https://arxiv.org/html/2502.01167v1 ; DOI10.1109/LRA.2024.3520916 | 已学习行动preconditions/effects并监测执行。不能把“前置条件”概念作为新。 | 旧审计正文；Undermind DOI |
| ReSET | arXiv2509.18043v1, 2025; https://arxiv.org/html/2509.18043v1 | 从人类视频学习环境重构，开放盒子/清障已有。更正：§IV-A scoring network用人类视频单调时间先验监督，并非逐状态实测基策略成功标签；下游成功实验须分开。 | 旧审计正文及本轮§IV-A核查 |
| SOLE-R1 | arXiv2603.28730v2, 2026; https://arxiv.org/html/2603.28730v2 | 历史窗口和此前分数、正负进展、在线控制；本研究prefix不是独占。 | 旧审计正文 |
| ARM | arXiv2604.03037v2, 2026; https://arxiv.org/html/2604.03037v2 | 因果历史、视觉/本体/语言、progress/regress/stagnant和完成；历史与恢复非空白。 | 旧审计正文 |
| TOPReward | arXiv2602.19313v1, 2026; https://arxiv.org/html/2602.19313v1 | completion末尾True logprob；本地迁移中真实状态识别有错误。 | 追加报告及源码审计 |
| Robometer | arXiv2603.02115v1, 2026; https://arxiv.org/html/2603.02115v1 | 训练progress/success/preference；项目P0中B准备配对3/3，不能说全领域不会准备。 | 项目原始报告 |
| RoboReward | Lee et al., arXiv2601.00675, 2026; https://arxiv.org/abs/2601.00675 | counterfactual任务重标和temporalclipping，partial/failure；goal swap本身不是新。 | 本轮搜索一手摘要 |
| Robo-Dopamine 2.0 | Xu et al., arXiv2608.15680v1, 2026; https://arxiv.org/html/2608.15680v1 | history-conditioned pairwise、signed OOD、失败恢复与阶段重复；含参考图与多视角，不能当同输入主baseline。 | sources/2608.15680v1.html |
| Dream2Reward | Zhang et al., arXiv2608.18787v1, 2026; https://arxiv.org/html/2608.18787v1 | 正示范学习成功潜在转移，比较实际位移方向与幅度，history causal，wrongdirection/overshoot/stall。转移评分已有，不满足本研究无demo输入/免新增训练。 | sources/2608.18787v1.html |
| ProcVLM | Feng et al., arXiv2605.08774v1, 2026; https://arxiv.org/html/2605.08774v1 | 程序结构与阶段内变化，remaining actions后进度；还含task-free actionsegmentation训练。 | sources/2605.08774v1.html |
| CMA | Zhang,Xiang,Chen, arXiv2609.27247v1, 2026; https://arxiv.org/html/2609.27247v1 | 两合法历史重合同当前观测，交叉已存动作到不同世界，区分敏感性/正确选择/physicalvalue/逐pair可靠性。对象是历史策略，非变化monitor，但反事实续行与memoryaudit要承认近邻。 | sources/2609.27247v1.html |
| CounterAlign | arXiv2608.21740v1, 2026; https://arxiv.org/html/2608.21740v1 | 专家action配mismatch instruction、对抗reward训练、offlineRL；goal swap不新。 | sources/2608.21740v1.html |
| SR-WM | Cheng et al., arXiv2608.22294v1, 2026; https://arxiv.org/html/2608.22294v1 | 软视觉实体→角色绑定，预测contact/predicateestablishment/preservation/fixture/phase，用于动作生成筛选修复；额外本体和训练。关系/实体表述不能自动新。 | sources/2608.22294v1.html |
| What Changed and What Could Have Changed? | Kung et al., ICCV2025; https://openaccess.thecvf.com/content/ICCV2025/html/Kung_What_Changed_and_What_Could_Have_Changed_State-Change_Counterfactuals_for_ICCV_2025_paper.html ; DOI10.1109/ICCV51701.2025.01143 | LLM statechange和counterfactual监督procedure-aware视频表示，错误检测/动作分段；必须区分“用变化/反事实”大概念与当前作用/约束。 | sources/2503.21055v1.html及CVF主页面 |
| PRM-as-a-Judge | Ji et al., arXiv2603.21669v1, 2026; https://arxiv.org/html/2603.21669v1 | outcome/process/diagnosis，路径一致性/局部物理分辨率；RoboPulse微观差异。不能只换密集诊断名。 | sources/2603.21669v1.html |
| PRM-as-a-Judge1.5 | Team, arXiv2608.14284v1, 2026; https://arxiv.org/html/2608.14284v1 | RoboPulse++区间进退判断，context-dependent任务、失败侧进度、drawdown恢复、效率。具体AppendixC需用于细比较。 | sources/2608.14284v1.html |
| Robots That Take Initiative | Patel&Chernova, arXiv2609.28910v1, 2026; https://arxiv.org/html/2609.28910v1 | proactive assistance，闭环人类响应与无帮助counterfactual价值。问题不同但节省工作量/新障碍效应有近邻。 | sources/2609.28910v1.html |
| MAGMA-GEN | arXiv2609.20056, 2026; https://arxiv.org/pdf/2609.20056 ; https://magma-rob.github.io/magma-gen | 全文已补齐25页。§4.3相同父状态、候选恢复动作、匹配扰动后续行筛选恢复训练数据；重执行本身不是新增贡献。 | sources/magma_gen.pdf、magma_gen.txt及aris_magma_checked.json |
| Progress Reward Survey | arXiv2607.21655v1, 2026; https://arxiv.org/html/2607.21655v1 | 组织进度接口/机制/数据/benchmark，grounding与uncertainty为已有评价维度。作为检索地图，不能替代具体近邻证明。 | sources/2607.21655v1.html |

感知分片追加后已读O-VAD正文/附录 https://arxiv.org/html/2607.18142v1 ：自动定位、跨时身份与状态/交互、视觉复核及整体/部件去重均已有。因此“加跟踪再描述”不是本候选精确增量。freshjury另核查TubeletGraph https://arxiv.org/html/2511.04678v1 ，也有恢复轨迹再描述变换，原设定给初始对象mask。审阅原文见trace，不能由输入差异直接推出新颖性。

Points2Reward https://points2reward.github.io/ 项目页已读：示范与执行的语义点对应评分，示范输入与当前约束不同。其余谱系未穷尽：OASIS-Map https://dynamic.robots.ox.ac.uk/projects/oasis-map/ ; VideoArtGS https://arxiv.org/abs/2509.17647 ; CoTracker3 https://arxiv.org/abs/2410.11831 ; SoM https://arxiv.org/abs/2310.11441 。这些尚不可据以作完整排他判断。
