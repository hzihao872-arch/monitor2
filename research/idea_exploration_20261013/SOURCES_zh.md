# 一手来源与阅读定位

核查日期：2026-10-13，北京时间。下列版本为本次使用的固定版本，不表示每篇都是当前最新版本。MomaGraph 的论证使用 v2，TFP 使用 v3；早版快照也保留在目录中。

检索围绕环境条件与进度、后果／反事实监督、技能前提、执行反馈适应、动作条件预测与恢复、交互导航展开，并沿参考文献补查直接操作先例。使用公开检索定位后回到 arXiv 正文与作者仓库。没有进行系统综述或声称检索穷尽；未调用付费深度搜索。

`sources/` 保存网页与编号文本，`manifest.json` 保存 URL、版本和本地文件校验信息。文本行号由本地提取生成，与浏览器网页行号不同；定位以章节名与 HTML 锚点为准。阅读范围表示实际用于本次判断的部分，下载了全文不等于通读所有实验与证明。

## 决定选题取舍的来源

| 论文／固定版本 | 原文链接与定位 | 实际核查范围 | 用于哪项判断 |
|---|---|---|---|
| CoINS: Counterfactual Interactive Navigation via Skill-Aware VLM，2601.03956v1 | https://arxiv.org/html/2601.03956v1#S4.SS3 | III；IV-A–E；V-B | 反事实后果教师与能力条件化的主要借鉴；已有操作技能，不能当纯静态导航 |
| Relational Learning for Skill Preconditions，2012.01693v1 | https://arxiv.org/html/2012.01693v1#S3 | III，尤其3.1–3.3 | 操作中的交互后果表征与技能前提直接先例 |
| Robot Critics that Sweat the Small Stuff，2606.21572v1 | https://arxiv.org/html/2606.21572v1#S3.SS1 | 数据与训练机制；进度比较接口 | 成敗／时间配对代理与新成对后果监督的区别 |
| ARS: Agentic Reward System for Robot Learning，2609.34484v1 | https://arxiv.org/html/2609.34484v1#S3 | 3.2–3.4、3.7；相关事件与修订描述 | 环境准备、回退与核验已有覆盖；主要下游为离线筛选后行为克隆 |
| Robo-Dopamine 2.0: History-Conditioned and OOD-Aware Process Reward Modeling for Robotic Manipulation，2608.15680v1 | https://arxiv.org/html/2608.15680v1#Sx3.SSx2 | 方法3.1–3.5；附录A.1、A.2、A.5及数据规模描述 | 历史、编辑数据、带符号进度与恢复已有学习机制 |
| ConditionNET: Learning Preconditions and Effects for Execution Monitoring，2502.01167v1 | https://arxiv.org/html/2502.01167v1#S3.SS1 | III-A、III-C、执行监测逻辑 | 技能条件学习已有直接基线 |
| Do As I Can, Not As I Say: Grounding Language in Robotic Affordances，2204.01691v1 | https://arxiv.org/html/2204.01691v1 | 3.2、4.1–4.2、附录相关校准讨论 | 技能价值与任务相关性结合的先例 |
| HiRE: Hindsight Reward Editing for Policy Finetuning，2609.27068v1 | https://arxiv.org/html/2609.27068v1#S4.SS2 | 4.2；附录A.3；局限 | 执行历史适应、终局缓存选择与非参数强对照 |
| Model-Based Runtime Monitoring with Interactive Imitation Learning，2310.17552v1 | https://arxiv.org/html/2310.17552v1 | III-B–D | 正确的 MoMo 论文：交互部署中的监测与策略学习 |
| Demonstration-Free Success-Probability Reward Learning for Generalist Robot Policies，2609.33653v1 | https://arxiv.org/html/2609.33653v1#S3.SS2 | 3.2–3.3 | eVTA₀／RLER：结果自举奖励与策略学习，区别于局部条件反馈 |
| FIERCE: From Generalist Robot Policies to Fast Specialists via Progress–Failure Feedback，2609.18651v1 | https://arxiv.org/html/2609.18651v1#S3.SS1 | III-A、III-C；架构与策略更新接口 | 区分观察进度、动作条件风险与评价器适应 |
| Imagining Recovery: Inference-Time Counterfactual Realignment for Vision-Language-Action Models，2608.14822v1 | https://arxiv.org/html/2608.14822v1#Sx3.SSx3 | 方法：检测、锚点、想象续行、最小恢复与交接 | 对泛泛“想象未来＋最小修复＋冻结策略”的重叠最强 |
| ContactGuard: Pre-Contact Execution Monitoring with Action-Conditioned Latent World Models，2608.13438v1 | https://arxiv.org/html/2608.13438v1 | 3.4–3.5及动作／观察对照 | 接触前动作条件风险已有方法；制止接口与完整恢复不同 |
| Foresight: Failure Detection for Long-Horizon Robotic Manipulation with Action-Conditioned World Model Latents，2606.23085v1 | https://arxiv.org/html/2606.23085v1 | 3–4的方法与监督定义 | 动作条件未来风险不是新能力名称 |
| STRIPS-WM: Learning Grounded Propositional STRIPS-style World Models from Images，2606.06832v1 | https://arxiv.org/html/2606.06832v1 | 5；7的范围限制 | 视觉转移、条件与规划已有组合；注意确定性及实例范围 |

## 图、记忆与主动核验的直接对照

| 来源 | 原文与定位 | 核查所得、在本报告中的使用 |
|---|---|---|
| UniGoal，2503.10630v1 | https://arxiv.org/html/2503.10630v1#S3 | 核查统一图匹配、阶段策略及核验／排除；作为可借机制，不认为图匹配已解决操作物理条件 |
| MomaGraph，2512.16909v2 | https://arxiv.org/html/2512.16909v2#S4.SS3 | 核查功能关系随真实动作后效更新；同时查看6.4；操作中已有状态感知图更新 |
| TFP，2607.08283v3 | https://arxiv.org/html/2607.08283v3#S3.SS2 | 核查时间条件记忆、接触更新、训练与局限；其记忆属于学习策略，不能描述为纯冻结 Monitor |
| Robot Planning and Situation Handling with Active Perception，2604.26988v1 | https://arxiv.org/html/2604.26988v1#S4.SS2 | 核查IV-A–C及观察充分性／视角选择；操作前提与后效主动核验已有完整先例 |
| Code-as-Monitor，2412.04455v3 | https://arxiv.org/html/2412.04455v3 | 核查约束及实体／部分追踪接口；可用于构建几何监测对照 |

## 辅助边界核查，未据此声称完整复现

| 来源与版本 | 链接 | 本次关注范围 |
|---|---|---|
| GroundBench，2609.13308v1 | https://arxiv.org/html/2609.13308v1 | 第3节分因素定位；3.3的反事实重新提问。它不是图像几何编辑或轨迹后果教师 |
| PATCH，2606.16690v1 | https://arxiv.org/html/2606.16690v1 | 方法中的动作走廊、局部创新与时间过滤；区别于目标语义作用 |
| RAFAIL，2609.18324v1 | https://arxiv.org/html/2609.18324v1 | 关系重要性和运行时检测；输入／策略训练依赖与局限 |
| RoboMonitor，2609.30715v1 | https://arxiv.org/html/2609.30715v1 | 预测表征与标签效率机制；未将论文训练成本等同本方案成本 |
| Beyond Monotonic Progress: Retry-Supervised Value Learning for Robot Imitation，2606.24633v2 | https://arxiv.org/html/2606.24633v2 | 重试监督与数据范围；作为非单调进度的相关先例 |
| WARP-RM，2606.28320v4 | https://arxiv.org/html/2606.28320v4 | 时间扭曲／逆序代理及真实回退分布限制；不能把逆放等同真实物理撤销 |
| CounterAlign，2608.21740v1 | https://arxiv.org/html/2608.21740v1 | 摘要与核心定义级核查：其反事实重标注不等于受控环境分支后果；未完整审计训练与成本 |

## 三处容易误读的具体细节

1. Robo-Dopamine-2 的附录A.1区分不同技能与编辑算子：其所述 open／close／toggle／push 使用保留相关状态的鲁棒性算子；部分 grasp／place 操作则加入负例算子。这是其公布构造的范围，不能推断模型必然无法评价环境前提。原图正、负图负的规则也不能直接迁移到任意新任务。
2. CoRe 的虚拟最小恢复探针比较候选续行与完整恢复的轨迹偏离。不能把每个探针称为已经实际执行并证实目标成功的分支。
3. FIERCE 在III-A明确限制其风险分数的含义，不能把动作条件风险分数自然解释为校准概率或已验证的因果作用。候选一的教师标签同样须声明续行库与预算。

## 代码与旧核查的更新

ARS 作者仓库：https://github.com/midea-ai/ars 。本轮查看时已有 agent、configs、scripts 等实现及推理说明；旧资料中“仓库为空”的状态不能继续使用。README 的大显存测试配置不是已证实的最低需求。本轮没有安装、运行或完整代码复现，因此不对可复现性作完成声明。

## 证据如何支持判断

原文提供的是相邻机制、输入与监督定义。候选的贡献、成本排序和推荐属于基于这些证据的研究设计判断。主报告中的新接口、教师、数据规模和实验结果预期均是拟议内容，不是被引论文的实验结果。
