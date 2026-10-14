# 检索、证据等级与未解决事项

日期：2026-10-13，Asia/Shanghai。任务边界：只检索/阅读/源码核查/新笔记，未运行任何模型、训练、评估、仿真或机器人实验；没有下载模型或数据集。只保存小型论文网页/元数据与选读源码。`D:/monitor2`不是Git仓库；没有创建提交或改动实验代码。

## 1. 来源与工具

沿用 agentic-research-workflow 和 nature-academic-search，工作流为多源检索＋引文核验。读取了相应manifest、source routing、去重与检索规则。当前没有发现技能目录所列的专用 academic-search CrossRef/arXiv MCP工具，使用现有Web搜索发现、arXiv全文/abs、正式出版页面和作者/机构网站核验；代码经公开GitHub API/固定commit raw地址只读。没有把未连接数据库称作已经使用；没有启动Undermind后台深搜或子代理。

另直接读取CrossRef公开API，三项DOI的题名均匹配：Runtime Monitoring、ConditionNET、Hierarchical Task Decomposition；卷期/页码字段支持后两项的正式引文。响应摘要保存为 `sources/crossref_verification.json`。IEEE DOI跳转在Web工具不可读，CrossRef API核验成功，未把跳转失败误作DOI不存在。

检索不是穷尽系统综述：无召回率保证、没有逐篇搜索全部引用图。第三方结果只用于找题名/URL，结论以一手来源为准。下载HTML与元数据用于固定阅读版本；来源快照不是新的研究数据。

已有材料：

- `idea_team_20261013/MECHANISM_RECOMMENDATION_zh.md`
- `EXECUTION_FEEDBACK_MONITOR_zh.md`
- `IDEA_PRIOR_ART_AND_IMPLEMENTATION_zh.md`
- `source_discussion.md`
- `assets_readonly_audit.md`
- `literature_followup_20261013.md`、`overlap_followup_20261013.md`、`mechanism_temporal_candidate_20261013.md`、`mechanism_logic_candidate_20261013.md`等。

原讨论的“首次/已有Monitor只看目标物体”等宽泛说法不作为当前结论。两张截图通过图片查看工具实际读取；它们确认师姐认可更新流程，但没有明确“原模型”的指代。

## 2. 本轮查询族与新增先例

发现性查询包括：

1. `robot runtime monitor continual learning execution feedback failure classifier Sirius Fleet ThriftyDAgger`
2. `robot execution monitoring learn success detector autonomous interaction online update reward model`
3. `robot progress monitor hindsight feedback continual reward model HiRE`
4. `robot failure detector continual monitor training`
5. `execution monitoring incremental learning robot`
6. `reward model online failures robot goal contrastive`
7. 精确题名/作者＋arxiv/github/code；分别检查GCR、Hierarchical Task Decomposition、RoboMonitor、ARS等代码入口。
8. 校准/时序：LTT、Selective Generation、ConformalSAM和经典TTT的正式出版/全文。

新增且优先补进主矩阵：

| 研究 | 为什么确实相关 | 核验等级 |
|---|---|---|
| [Sirius-Fleet](https://arxiv.org/html/2410.22689v1) | §3.1部署数据训练下一轮策略与异常预测器；§3.2.2最近轮分类器微调＋累计OOD更新 | 正文＋作者页＋实际代码配置/续训入口 |
| [Hierarchical Task Decomposition](https://arxiv.org/html/2505.04565v1) | §3.2自主执行与人的纠正修正异常模型；§3.3加恢复图；§7.3.5力域模型更新实例 | 正文＋IJRR/机构记录；未核实官方源码 |
| [ThriftyDAgger](https://proceedings.mlr.press/v164/hoque22a/hoque22a.pdf) | §4.2–4.5部署转移TD训练风险Q，每回合更新门控用Q与策略 | 正文＋PMLR元数据＋实际 `compute_loss_q/update_q` |
| [GCR](https://arxiv.org/html/2410.19989v2) | 在线失败末段更新奖励表征，评价者与RL共同学习；明确不是条件真值Monitor | 正文＋作者页；未核实官方完整源码 |

Runtime/Sirius是相关系列，但论文题名、机制、出版记录不同，不合并成一篇，也不把后续仓库冒充原版。正式与arXiv版本按题名/作者/DOI去重；同一研究的多网页不重复计数。

## 3. 十二篇主研究元数据与版本

完整作者列表、abs页面引文meta与版本历史保存在 `sources/bibliography_metadata.json`；各条abs页也保存。所有选用版本提交日期早于当前2026-10-13。

| 研究 | 阅读版本 | 正式出版状态的可核事实 |
|---|---|---|
| Model-Based Runtime Monitoring | 2310.17552v1，2023-10-26 | ICRA2024，DOI 10.1109/ICRA57147.2024.10611038 |
| Sirius-Fleet | 2410.22689v1，2024-10-30 | 作者页CoRL2024；[PMLR270，2025记录](https://proceedings.mlr.press/v270/liu25g.html) |
| Hierarchical Task Decomposition | 2505.04565v1，2025-05-07 | [IJRR](https://journals.sagepub.com/doi/10.1177/02783649251352112)2025在线，2026卷期；DOI如链接 |
| ThriftyDAgger | 正式PMLR PDF；arXiv2109.08273v1，2021-09-17 | [CoRL第五届/PMLR164，2022](https://proceedings.mlr.press/v164/hoque22a.html)，598–608 |
| GCR | 2410.19989v2，2025-05-14 | 作者正式PDF标ICRA2025；不用v1日期充当最新版日期 |
| RoboMonitor | 2609.30715v1，2026-09-25 | 本轮作为预印本，未独立核实正式录用状态 |
| ConditionNET | 2502.01167v1，2025-02-03 | 作者页RA-L2025，10(2):1337–1344，DOI 10.1109/LRA.2024.3520916 |
| ARS | 2609.34484v1，2026-09-28 | 本轮作为预印本 |
| WVN扩展 | 2404.07110v1，2024-04-10 | 本轮读2024扩展，不冒充RSS2023原版相同规格 |
| HiRE | 2609.27068v1，2026-09-22 | 本轮作为预印本 |
| Robo-Dopamine2 | 2608.15680v1，2026-08-16 | 本轮作为预印本 |
| Video2STL | 2609.37519v1，2026-09-29 | 本轮作为预印本 |

arXiv-issued DOI只说明归档标识，不能当会议/期刊正式录用。没有凭搜索页面“Published几个月前”判断出版时间。

## 4. 补充研究：值得借，但不代替直接Monitor先例

| 一手研究 | 本轮核查与借法 | 不应宣称 |
|---|---|---|
| [Experience-Driven Continual Learning of Terrain Traversability](https://arxiv.org/html/2609.39755v1)，§III-B/D、IV-A | 冻结DINOv3；完整足接触得到五属性后，关联触地前≤5秒同5cm格视觉；回放＋近期验证＋历史anchor升级门。硬件持续比较使用同记录流，闭环导航另在仿真 | 不是指定放置条件/完整进度；牵引指标非直接摩擦系数；不冒充本轮核实了官方源码 |
| [TACIT](https://arxiv.org/html/2609.24507v1) | 晚到触觉接触形成历史视觉空间注意目标；可借无事件不强造目标 | 不是条件真假或进度；策略/注意学习不能代替Monitor自我更新 |
| [Aff-Grasp](https://arxiv.org/html/2408.10123v2)，[作者代码](https://github.com/Reagan1311/Aff-Grasp) | 接触点回投较早干净帧，学单图功能部位；本轮保存v2避免只沿用v1 | 功能部位预测不等于独立支撑/通过物理真值；本轮未重查全部脚本运行情况 |
| [RT-Affordance](https://arxiv.org/html/2411.02704v1) | 轨迹关键姿态回投初图形成hindsight计划，再训练预测器/策略 | 是策略中间表征，不是已实现持续条件Monitor |
| [Inductive Learning of Robot Task Knowledge](https://arxiv.org/html/2501.07507v1)，方法/在线refinement | 从分段和几何语义学Event Calculus pre/effect；人禁止/改选动作后更新ASP规则。可借事件发起/终止和人反馈改规则 | 更新逻辑规范不是视觉基础模型TTT；安全依赖文中专家/感知假设，不能套作本项目无条件保证 |
| [Autonomously Learning to Visually Detect Where Manipulation Will Succeed](https://arxiv.org/html/1212.6837v1) | 执行行为→检测成败→视觉SVM主动适应，是更早行为成功预测先例 | 2012是预印本日期，不代表正式期刊卷期；行为成功位置不等于环境条件独立真值 |

Experience-Driven Terrain从上一报告的主近邻移到补充表，仅因为十二篇限制下优先新增**直接执行监控器**，不是降低其物理监督相关性。WVN仍为主物理反馈骨架；两者都需细分推理输入、监督输入和实际验证条件。

## 5. 结论证据台账

| 主张 | 支持来源/定位 | 可以得出什么 | 不能得出什么 |
|---|---|---|---|
| 监控器随部署反馈更新已有 | Runtime §III-D；Sirius §3.1/3.2.2；Hierarchical §3.2；Thrifty §4.5 | 不能以闭环首创立项 | 所有论文都是前缀进度模型 |
| 当前条件已有人学 | ConditionNET §III/IV | 行动条件监控是强直接近邻 | 任意环境条件/独立物理证书已解决 |
| 后视核验/范围/退步已有 | ARS §3.3–3.6；Dopamine2附录 | 不能以区间或后视首次作为贡献 | ARS已训练本项目的条件学生 |
| 物理体验回配旧视觉/小头更新已有 | WVN §3.3–3.5及源码 | 骨架可借、骨架不新 | 未走区域=可靠负例 |
| 在线结果修正评价者已有 | GCR §V-A/V-D；HiRE A.3 | 梯度与非参数两种路线都有直接先例 | 终局结果可广播为全部历史条件真假 |
| 未来表征学习≠物理回溯标签 | RoboMonitor §IV-A/B | 预训练和监控监督要分开 | 利用未来特征预测就构成已实现证书传播 |
| 小头/LoRA≠整体Monitor不变 | RoboMonitor §IV-B；WVN | 基础权重固定，函数仍更新 | 所有训练可在当前硬件完成 |
| 不需要条件≠条件false | 本项目合同逻辑；Task Graph、Video2STL提供相关组织先例 | 必须定义C/V/R接口并实验 | 单纯接口定义已是新学习算法 |
| LTT不产生物理真值或边界 | [LTT §2/3](https://arxiv.org/html/2110.01052v5)；本项目适配推导 | 固定候选可检验已定义风险 | 免费监督、出域保证、机器人安全保证 |
| 没有核到完整同构论文 | 本轮检索覆盖及上述拆解 | 当前可以提出可检验假设 | 证明领域无人做过或保证发表 |

## 6. 代码证据与复现边界

`sources/code_manifest.json`保存选读文件、固定commit、URL、本地文件与SHA256；树快照保存对应仓库sha。Sirius-Fleet、WVN、ThriftyDAgger、ARS均读了实际Python/配置/提示；没有安装依赖、加载权重、调用推理或跑测试。

GCR作者页无已核实Code入口；ConditionNET模型仓库、Hierarchical完整官方仓库、Experience/TACIT官方实现本轮均未核实。HiRE作者页在Web工具返回Internal Error，本轮据可读全文核查机制，不拿项目页失败推断没有代码。ConditionNET v2 HTML不可读；abs历史显示只有v1，所以改读并保存v1。专用academic-search MCP未挂载是路由限制，不是论文不存在。

研究preflight曾发起，未取得可复核完整报告；不依据该尝试声称检测到了GPU/预算。现有资产可确认程度来自旧只读核查，不代表本轮做了运行验证。

## 7. 当前仍待解决

1. 什么独立证据实际可获得？真实硬件、可靠策略、预算均未确认。
2. 入口/支撑合同的负证据能否独立取得？不能用终局失败替代。
3. 有效范围是否可以比直接状态标注更廉价？没有实测人工分钟。
4. 冻结表征是否能识别尺寸/身份/指定支撑？没有模型评估结果。
5. 接口分离是否改善最终进度，第二Monitor是否同样受益？均是待验证假设。
6. 跨分布或传播器更新后的独立校准是否可负担？当前九条开发录像不充分。

本轮完成的是来源支持的研究定位与可否证设计，没有把这些待解决项包装为已完成实验。

交付审核：四份中文报告、十二条BibTeX引文；三项DOI题名核对；所有本地Markdown链接可解析；保存源码/HTML的清单SHA256逐一匹配。`response_sha256`（如有）是原HTTP字节哈希，`sha256`是本地保存字节哈希，Windows换行转换可使二者不同。审核只是笔记/来源完整性检查，不是模型评测。
