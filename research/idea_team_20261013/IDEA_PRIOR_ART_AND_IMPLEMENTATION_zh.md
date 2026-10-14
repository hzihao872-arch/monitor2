# 实际使用反馈监督条件 Monitor：已有工作与实现核查

检索日期：2026-10-13。针对上一轮主推荐 B：后来的实际通过、接触或稳定承载，监督早先的环境条件判断；部署只看已观察前缀，反馈到来后更新监督者。本轮用网页检索和 Undermind 语义检索发现候选，再阅读一手正文与作者代码。仅研究和只读检查，未训练、评测或执行机器人实验；本文件不替换旧提案。

## 结论修正

**有直接先例。通用链条“实际交互后果→配回早期视觉→学习预测器→反馈更新”已经实现，WVN 最有决定性。** 我之前把 B 留作主推荐，是基于本地第一份可用监督；这不能说明它新颖。现有证据要求下调其方法创新判断。

没有核到一篇完整同构于我们全部设置的论文，但这不证明无人做过，也不证明模块组合有新贡献。尤其“冻结视觉、小头更新、后视教前视、条件撤销、按阶段限制传播”分别已有先例。

## 最值得读的实现

| 工作 | 实现链条 | 与 B 的重合及边界 |
|---|---|---|
| [WVN，RSS 2023；后续扩展](https://arxiv.org/html/2404.07110v1) | 速度跟踪误差给通行分→足迹投回旧相机图→冻结 DINO/STEGO，小 MLP 在线学→导航 | 后果回配、少人工标签、小预测器进化已完整存在；未走区域采用置信加权保守学习，不是严格三值条件逻辑 |
| [Experience-Driven Terrain，2026-09](https://arxiv.org/html/2609.39755v1) | 完整足接触给物理量→对应触地前 ≤5 秒、同 5cm 格视觉特征→冻结 DINOv3，五头回归→回放与验证门 | 与“监督者随经验更新”很近；有离线初始模型，硬件适应比较用记录流，闭环导航另在仿真验证 |
| [TACIT，2026-09](https://arxiv.org/html/2609.24507v1) | 触觉接触点→前 5–120 步相机点云的 Gaussian 目标→有效 mask 的 BCE→注意力条件化策略 | 真实晚到接触教早期视觉已存在；无事件不生成目标。输出关注点，不是条件真假；策略训练且推理仍用触觉 |
| [Aff-Grasp，ICCV 2025](https://arxiv.org/html/2408.10123v2#S3) | 叙述时间戳定位交互→检测接触点→回投干净早帧→SAM mask→单图部位预测 | 标签回投与前视学生已有；依赖时间戳、类别先验及伪标签，功能部位不能直接当承载真值 |
| [ConditionNET，2025](https://arxiv.org/html/2502.01167v1#S3) | 人工 pre/core/post 区间→pre/post 配对与逆动作增广→冻结视觉语言，学习条件分类→行为树监测恢复 | 条件学习与 effect 失效监测已有；监督主要是阶段标签，未见实际物理事件回推或部署持续参数更新 |
| [RT-Affordance，2024](https://arxiv.org/html/2411.02704v1#S3) | 夹爪切换/终局抽关键姿态→投到初始图作 hindsight plan→计划预测器与条件化策略 | 后期轨迹教初图已有；约 750 图是额外手标数据，另有机器人轨迹与 web data，不是从零小数据通用控制 |
| [ARS，2026-09](https://arxiv.org/html/2609.34484v1) | 全视频后视证据→核验事件与区间→修改后重核→允许进展回退 | 后视审核、范围和回退已有；主要离线推理，审计轨迹用于训练是论文提出的方向，非已训练的条件学生 |

### 代码入口和可复用程度

WVN [作者仓库](https://github.com/leggedrobotics/wild_visual_navigation) 有实际 Python 与 ROS 1 实现。核读了 `SupervisionGenerator.update_velocity_tracking`、`TraversabilityEstimator.add_supervision_node` 和 `TraversabilityLoss`：分别生成体验评分、重投影监督、处理已标/未标区域损失。适合首先借鉴图像—体验关联与在线学习组织；没有在本机验证运行。

Aff-Grasp [作者仓库](https://github.com/Reagan1311/Aff-Grasp) 的 `ego2aff/epic-kitchen` 有选早帧、接触点回投、点转分割脚本；部分提取说明仍 TODO，脚本有本地路径和交互显示。可读算法，不应视为一键可用管线。

ConditionNET 作者页有数据链接，本轮未核到模型源码；TACIT 与 Experience-Driven Terrain 未核实公开官方代码入口。论文有实现规格不等于可直接下载复用。RT-Affordance 作者页有论文和视频，本轮未核到实现仓库。

## 更早的先例与容易误认的近邻

[Where Should I Walk?，2019](https://cesarcadena.ethz.ch/files/RAL2019_lwellhausen.pdf) 已将传感足的力/力矩属性配给投影足点，训练视觉地形预测；后效配回视觉不是近期才出现。

[Autonomously Learning to Visually Detect Where Manipulation Will Succeed](https://arxiv.org/abs/1212.6837) 的 2012 预印本已有执行行为、检测成败、主动学习视觉 SVM、失败后继续适应。它预测指定行为的成功位置，不能自动等同于与控制技能无关的环境条件真值。正式刊载信息是 2013 在线、2014 卷期，不能照索引把期刊版写成 2012。

[Relational Learning for Skill Preconditions](https://arxiv.org/html/2012.01693v1) 先用模拟扰动效果学对象关系，再用下游条件标签分类；效果监督的关系表征与可执行条件标签是两层。

[AffordTrajDP](https://arxiv.org/html/2608.01603v1) 将接触锚点沿预测未来对象位姿向前传播以指导策略；不应误算为真实后果向历史赋条件真假。它在本问题中弱于 WVN/TACIT。

近期 [COTRATE](https://arxiv.org/html/2605.28442) 也覆盖传感体验评分、视觉对齐和特征回放。本文未核实其实际公开代码；正文有发布时机表述，不能仅凭摘要的“公开”当作已可复用。

## 对我们的具体含义

可以借用的工程骨架已经清楚：保存带时间与对象身份的前缀观测；实际事件出现后独立验证局部结果；按几何/运动学或视觉对应回配；未知监督做 mask；用冻结表征训练小头；新旧证据回放，并用独立验证决定是否替换部署模型。

**这条骨架本身不能再作为创新。** 若继续 B，较具体的待验证问题是：一次局部实际使用究竟支持哪些早期状态？相关部件、对象尺度、载荷或支撑配置变化时，哪些历史监督必须停止传播？停止相信旧证据与条件已为假如何区分？任务使用完某条件后，还需不需要继续维持它？

例如物块确实通过入口，只在有关物体和碰撞几何未改变的范围内提供存在可行通道的见证；它不证明所有控制器都能通过。物块进入后入口关闭，可能表示通行条件变假，但已消耗的进入义务无需恢复。释放稳定证书还要指定载荷、支撑来源与配置。终局失败不提供这些条件的可靠负标签。

这些是我们的研究假说，不是上述论文已证明的规则。若有效区间全部人工标好，再普通 SFT，主要贡献更接近监督数据设计。必须在相同人工分钟、相同真实交互数量下，与直接状态标注、事件帧学习、普通区间 SFT、证据检索以及 ARS 后视教师比较，才能说明额外设计值得做。当前尚无实验结果，不预设节省人工或提高准确率。

## 检索记录与详细证据

Web 查询覆盖 hindsight affordance、physical-contact supervision、skill preconditions、continual traversability 与精确题名。Undermind 两组语义问题分别查询：后接触体验配给接触前视觉并更新小预测器；稀疏反馈学条件并限制历史传播。候选经正文与作者代码核验；第三方概述仅用于发现。

- [导航、触觉及关系前提细节](D:/monitor2/research/idea_team_20261013/literature_followup_20261013.md)
- [Aff-Grasp、ConditionNET、RT-Affordance 实现细节](D:/monitor2/research/idea_team_20261013/implementation_neighbors_20261013.md)
- [ARS、Robo-Dopamine 2.0、RoboMonitor、HiRE 重合审查](D:/monitor2/research/idea_team_20261013/overlap_followup_20261013.md)

后者补充：Robo-Dopamine 2.0 已限制多子目标编辑传播范围，RoboMonitor 已有因果窗口监督，HiRE 已用执行结果编辑奖励支持集。因此不能靠改名称或拼接这些模块保证创新。本轮检索结论有范围，不是领域穷尽性证明。
