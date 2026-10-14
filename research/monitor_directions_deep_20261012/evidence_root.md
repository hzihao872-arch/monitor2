# 跨主线核查：原有证据、ARS当前实现、导航迁移和选题可识别性

核查日：2026-10-12，北京时间。阅读与公开来源快照均未运行Monitor、训练策略或连接机器人。

## 1. 原有基础的真实边界

先读用户指定三份材料。10月9日诊断报告八个开发例中compact2严格合同8/8通过，但结构漏检、虚构物体、完成过早和事实更新错误仍在。8个D/C配对终判槽位没有有效输出，主要是依赖/核验接口失败，故无法估计核验净收益。文字oracle也错用初始事实；oracle来自AI审读而非独立双标。不能以这些结果证明原架构必然失败或已经有效。[诊断原报告](../prerequisite_monitor/change_first_development_20261008/runs/diagnostic_20261009_window/FINAL_REPORT_20261009_zh.md)

另外读取10月8日架构蓝图的任务定义、证据表和下游段落：入口宽度与目标物尺寸、支撑接触等部分真值仅在评价侧；原受控变化有运动学路线，不等于已有可训练的主动开盖/推板策略。旧结果中Robometer曾正确识别部分准备，禁止把“所有现有方法都不能识别环境准备”作为起点。旧文件的免训练与唯一下一动作不约束本轮。

## 2. ARS：论文重合没有随代码公开而消失

论文v1首发2026-09-28。§3.1允许离线未来证据，§3.3–3.6有事件账本、重新取证、独立上下文核验、局部下降和终局辅助。图2/附录B炉灶开关是目标锅尚未搬运时的条件建立与撤销实例；§4.2主要下游是动作块筛选后BC。能力范围、单例和量化验证须分开。[ARS全文](https://arxiv.org/html/2609.34484v1)

本轮GitHub API固定到commit **0b61a5de0c39af1788d960ea8dd996aa76b27f7f**，下载38个文本/代码文件审读，非运行。仓库已含agent、configs、scripts、RL4VLA子模块；10月10日空仓库记录是历史事实。公开树中能确认推理、审计、semantic-mismatch采集/转换/评价入口；本轮没有确认该树提供论文全部BC与真实数据训练流水线或原始评测数据。[固定仓库树](https://github.com/midea-ai/ars/tree/0b61a5de0c39af1788d960ea8dd996aa76b27f7f)

代码重点：common.md、bootstrap_observations.md、challenge_observations.md、progress.md；session.py确认新证据来源与覆盖要求，修订清除confirmation。提示明确要求拆开准备、控制取得、结果证据和失败重试，并允许准备/撤销。configs/config.yaml提供全轨迹附件、fresh challenge、40/60/40阶段步上限、可选终局标签默认关闭；不能把本地四阶段命名当创新。README说明默认27B、测试环境96GiB/GPU，推理与仿真采集环境分开。[固定README](https://github.com/midea-ai/ars/blob/0b61a5de0c39af1788d960ea8dd996aa76b27f7f/README.md)

Qwen官方仓库存在视觉支持的Qwen3.6-27B，含权重/config与部署说明。ARS名称不是笔误。本轮只保存模型卡与API元数据，未下载权重；更强底座是否解决本项目问题仍需实际对照。[官方模型卡](https://huggingface.co/Qwen/Qwen3.6-27B)

## 3. 跨主线新实证：静态总分不充分

CriticHack v1首发2026-10-01。§5.1/5.3报告同一优化同时提高任务成功和错对象失败，aggregate AUROC .813而success-vs-wrong-object .372；§7的task-specific outcome verifier有效，但verifier-only与乘积相近。§8/附录E说明真实40次/条件的变化未统计分辨，勿把仿真强证据延伸为真实显著性。它支持对高分错误子类与下游分布进行审计，但“加核验器乘奖励”已有直接覆盖。[CriticHack正文](https://arxiv.org/html/2610.02527v1#S5)

本项目的推论：在同样保留预算下，报告高分片段里的错目标/条件已失效比例，以及必要过渡与恢复片段的保留率。仅ROC或平均分类率不能证明筛选安全；仅成功率提高也不能证明局部作用正确。此处是实验设计启发，不是我们的新实测。

## 4. 导航值得借什么，不能推出什么

UniGoal v1首发2025-03-13：§3.2–3.4目标/场景图匹配、匹配阶段切换、目标核验与黑名单；输入posed RGB-D，实例目标图权限宽于语言目标+RGB前缀。可借鉴对象身份与关系共同匹配、错误候选撤销；但静态地图中的永久黑名单移到动态操作会错误屏蔽恢复后重新有效的状态。应比较可撤销记忆、永久黑名单、无记忆，在目标交换、状态反复与遮挡重现测试，控制视觉特征一致。[UniGoal](https://arxiv.org/html/2503.10630v1#S3)

ImagineNav++首发2025-12-19，本轮另核查v3（2026-04-30）：训练Where2Imagine选择视图，配合Novel View Synthesis和记忆；当前视图想象不等于动作后的物理可行性。可借鉴“为了不确定关系获取哪种观测”，但主动移动相机增加行动权限与真实成本。只有在已有多个合法相机时才能低成本模拟观察选择；给正确crop/3D位姿的oracle收益不能报作RGB方法收益。[ImagineNav++](https://arxiv.org/html/2512.17435v3)

ProgressLM先读v1，另核查v2（2026-05-21），讨论answerability与text demonstration的隐式状态累积，提示同一动作外观在不同历史下对应不同累计状态。其mental simulation是进度推理机制，不能自动算动作条件world model。使用目标参考、记忆或unknown均已有近邻，区别必须来自明确监督义务与迁移验证。[ProgressLM](https://arxiv.org/html/2601.15224v2)

## 5. 广检路线与边界

除各分支web搜索，根任务使用Undermind语义库分别搜索“可撤销任务条件监测”“终局结果驱动局部适应”“动作条件预测与恢复”，各20项，再核对重要条目DOI/arXiv及正文。命中ConditionNET、Relational Learning for Skill Preconditions、RAFAIL、ContactGuard、FARM、Foresight、MURAL、Bellman-Guided Retrials等不同名称机制；原始结果保存在sources/undermind_*.txt。使用学术MCP语义库与arXiv/作者仓库组合，非PubMed/CrossRef全库系统综述。未命中不表示不存在；仅元数据命中不得作为深读证据。

## 6. 建议研究问题的可识别性

1. **状态事实**问“盖在此刻是否打开”，不等于目标已完成。
2. **局部任务作用**问某具体变化是否建立/破坏与当前目标相关的可见关系；对多个目标可以不同，mixed允许与goal_done共存。
3. **执行条件**必须相对于定义的技能/动作和可见信息，不能从终态目标推出所有策略均可执行。
4. **价值/成功概率**依赖后续策略、预算和干扰分布；策略变了，同一状态值可变而事实不变。
5. **动作优势**需要对替代动作/状态价值作比较。视觉前后关联本身无法证明因果优势；同初态配对干预可在仿真评价侧支持。

成功终局在“开盖—关盖—再开盖—放入”与“开盖—等待—放入”上相同，不能唯一确定关盖区间局部作用。若只提供终局而要求逐段事实监督，问题不可辨识；应额外获取后续可直接核实的事实、稀疏局部标注、配对执行或明确的动态模型假设。不能把TD估值、终局重标或时间归一进度称作可靠局部真值。

## 7. 审读入口

sources保存原文HTML/纯文本、固定ARS代码、GitHub API与官方模型元数据。SOURCE_MANIFEST_root.json记录URL、读取UTC、大小、SHA256和失败；59项下载成功。snapshot_sources.py仅取公开资料，不加载模型。三主线证据笔记另见evidence_a/b/c.md，最终取舍见REPORT_zh.md。
