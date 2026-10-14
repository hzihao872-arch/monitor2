# PRM-as-a-Judge / RoboPulse++：研究基底收口与剩余问题核读

日期：2026-10-03（Asia/Shanghai）。承接 R1、D017、D024—D054；本次追加 D055—D057。单执行者；仅阅读、来源核查与文档更新，没有模型运行或新实验。本文不是新阶段编号，也不替代 S6-draft-4。

**结论：可以收口“先找到能反映问题的研究基底”。**依据是已有直接文献证据，以及已追溯到原库的 ep621/ep618 开发案例。作者已研究子目标撤销及历史上下文；我们不再把复现这一现象或修好本地 Qwen 当作承认研究动机的前提。**尚不足以确认一个新的方法缺口**；R-C、整个 R1、H1 均未完成，C1/C2/C3 均未获批。

## 1. 对照 R1，把四类事实分开

| 层次 | 当前已取得／尚待回答 | 对 R1 的含义 |
|---|---|---|
| A. 文献支持的现象 | C.5.2 直接讨论已经完成的子目标被后续撤销，以及局部比较可能漏掉历史相关的退步。C.3、C.5 和 §5 讨论退步、暂时波动及时间上下文。 | R-A 的具体情景与文献依据成立；无需先证明自己的模型会错。 |
| B. 可追溯开发案例 | ep621 旧关系被破坏，ep618 后续失败但旧关系保持；原任务、原失败类型、原视频、LeRobot 映射和 59 张发布帧匹配已取得。 | R-B 已达到“取得可解释、可追溯开发基底”的局部目标，不从头找材料；不等于正式评测集验收。 |
| C. 强方法还剩什么 | 作者的整体 Falling 判断仍有错误；但错误是否发生在这两例、是否是逐条件判断错误、是否来自历史使用、强方法是否能在因果前缀下区分旧条件失效与保持，都没有现成结论。 | R-C 目前只完成本次文献与公开接口范围核查；尚无本项目可复核的强方法剩余错例，不能进入机制定案。 |
| D. 后续实验条件 | 对应判断目标的独立复核、强基线及合法适配、输入权限与时间解释、预算、开发／保留划分和冻结等。 | 这些约束在对应实验前执行，不倒过来否定 A/B；R-D 仅有此前交接草案，R-E/H1 与 R-F/阶段 8 未开始。 |

固定研究方向仍是冻结已有模型，判断当前要求、先前进展有效性、正常调整／停滞／真正退步及局部操作对其他条件的影响。EvoNav 只提供论证与公平验证流程，不迁移模块。本轮只对上述方向中的一个窄情景收口，不声称覆盖全部类别或长时程。

## 2. 来源与实际核读范围

优先复用[本地论文 HTML](sources/recovery_search_20261003/robopulse_paper.html)，固定 [arXiv:2608.14284v1](https://arxiv.org/html/2608.14284v1)。核读 §2、§3 开头、§5、B.1、C.1—C.5.2、D、F.1；本次访问官方同版本入口核对，未泛搜文献或以其他版本静默覆盖。

同时复核[数据卡](sources/recovery_search_20261003/robopulse_README.md)、[作者标签释义](sources/recovery_search_20261003/robopulse_discussion2.json)、原始[来源映射](sources/recovery_search_20261003/upstream_trace/source_mapping.json)、[标签映射](sources/recovery_search_20261003/upstream_trace/native_label_mapping.json)、[单人草案](sources/recovery_search_20261003/upstream_trace/relation_labels_draft.json)及两条密集参考联系图。没有重新标为第二人结果，没有重新解码全部视频冒充新增验证。

仅为查清现成资源及比较语义，有界查看作者 [PRM-as-a-Judge 仓库](https://github.com/YuyangLiu2003/PRM-as-a-Judge/tree/34e8cd4396fe903d6205028da17e32ba01d723d9)，固定 revision `34e8cd4396fe903d6205028da17e32ba01d723d9`：完整目录树 51 个文件条目、README、评测 README、两个适配／推理源码和合成 recorded manifest；另保存官方 advanced guide。仅新增 174,794 B 文本源文件，另存小型目录元数据，不取媒体、权重或整库。[来源 URL、SHA 与访问失败记录](sources/prm_scope_review_20261003/source_manifest.json)；[固定目录树](sources/prm_scope_review_20261003/official_repo_tree.json)。源码只作文本阅读，没有导入或执行其中的模型／服务函数。

## 3. 作者做了什么，结果支持到哪里

| 作者研究对象及准确出处 | 作者结果支持的结论 | 不能由此推出 |
|---|---|---|
| [§2.1—2.2](https://arxiv.org/html/2608.14284v1#S2)：将 rollout 视频、任务与可选其他视角转换为进展曲线，计算回退、停滞、恢复等过程指标。§3 默认 judge 是 Robo-Dopamine Forward。 | 已有系统研究终态成败之外的过程表现；我们无需重新证明“失败轨迹也有不同进展”这一基本动机。 | OPD 曲线指标不自动提供每个任务条件的当前真假、全程义务或在线首次可判时间；主文机器人策略排名不是 PRM 判断准确率排名。 |
| [C.3](https://arxiv.org/html/2608.14284v1#A3.SS3)：标注者先看完整执行和任务，再划进展区间。 | 标签依据任务相关变化，并用全程上下文区分暂时波动和实质退步。 | 全程区间真值不是前缀在线真值；有该标注说明不等于正常调整、慢速、停滞、退步四类都经过直接分类验证。 |
| [C.4.1—C.4.3](https://arxiv.org/html/2608.14284v1#A3.SS4)：统一为 Rising/Falling，连续输出差分后做五帧因果移动平均；类别输出不平滑；区间首尾各去掉两采样时刻；汇总有效点计算指标。 | 提供了一套原生进展方向比较流程。 | 边界被过滤的方向准确率不能当作事件发生时刻检出率或 t_v 后延迟；B.1 用于 OPD 的曲线高斯平滑不能与这里的方向平滑混为一谈。 |
| [C.5 / Table 6](https://arxiv.org/html/2608.14284v1#A3.T6)：700 episodes 的多种 PRM/VLM 比较。 | 作者报告 Robo-Dopamine Forward 总体 Macro-F1 0.77、Accuracy 0.84；Falling 最佳 F1 是 Backward 的 0.63，最佳 Rising F1 0.92。按作者结果，下降判断仍不完美。 | 这是已有研究已报告的难点，不是我们发现的新缺口；不能从总体成绩定位到 ep621/ep618，更不能直接诊断历史、感知或条件更新机制。 |
| [C.5.1 / Table 7](https://arxiv.org/html/2608.14284v1#A3.SS5.SSS1)：抽取 155 个 Falling 区间，分为交互关系失败 121（78.1%）与任务顺序失败 34（21.9%）。 | 描述被标为下降的机器人执行片段中两类失败的构成。 | 文中没有把分母定义成 judge 预测错误的 155 个区间。不能写作“判断模型 78.1% 的错误是关系推理错误”，也不能把 ViFailback 原失败类型当 judge 错误标签。 |
| [C.5.2 / Table 8](https://arxiv.org/html/2608.14284v1#A3.SS5.SSS2)：历史依赖情形，明确以已完成子目标被后续撤销为例。 | 序列式 RoboMeter 在该子集明显优于 Robo-Dopamine Forward，支持历史上下文有助于此类退步判断的解释。该现象及这种解释可以直接作为已有研究依据。 | 不是同模型历史消融，不证明历史是全部差异的原因；不证明所有退步均解决，也不证明我们的两个候选属于该子集或作者 judge 在其上预测错误。 |
| [F.1 / Fig.10、12](https://arxiv.org/html/2608.14284v1#A6.SS1)：挂杯的回退／恢复，以及最终成功但过程不同的立瓶案例。 | 展示作者系统如何描述恢复程度及成功执行的过程差异。 | 这些是轨迹／曲线案例，不是新增逐条件在线准确率验证，也不能证明所有纠正动作都无必要或都应被罚。 |
| [§5 Discussion & Future Directions](https://arxiv.org/html/2608.14284v1#S5)：时间上下文、负进展监督、更丰富语义／状态证据；明确离线评估可使用过去和未来观察。 | 作者自己承认 judge 与解释能力仍可改进，也已提出丰富证据等方向。 | 作者展望不证明我们的 C1 新颖；离线借助未来信息的合理性，不等于在线可以使用未来。 |

本地 HTML 的对应锚点与数字已核，数字为作者报告值，未在本项目重算或冒充复现。

### 3.1 Table 8 的完整口径与历史归因

| 作者的 class-conditioned / overall accuracy | Robo-Dopamine Forward | RoboMeter |
|---|---:|---:|
| Rising | 0.844 | 0.951 |
| Falling | 0.408 | 0.901 |
| Overall | 0.746 | 0.940 |

这足以支持“作者已处理并较好识别部分历史依赖退步”，无需本项目先重做才能承认。**论文 C.5.2 未给该子集的 episode ID、区间清单、样本数、逐例预测或不确定性区间**；不是说这些资料在任何地方都不存在，本次检查的公开资源未补到它们。两种模型的训练、模型本体、输入组织与推理方式不同，不能将 0.901 对 0.408 全部算作历史贡献。

另有一处需纠正的概括：C.4 中“Pair Style”是类别名。当前官方[Forward 实现](https://github.com/YuyangLiu2003/PRM-as-a-Judge/blob/34e8cd4396fe903d6205028da17e32ba01d723d9/eval/prm_judge/prm/dopamine_inference.py#L211)实际使用起始帧与当前帧，并在 L619 将分数作为绝对进展；相邻帧对应 Incremental。代码还有起始／目标参考图槽位。因此不能把 Table 8 写成“完全无历史的相邻两帧 vs 相同模型加历史”。当前源码也不是 Table 8 当次配置的完整证明。

### 3.2 同模型 Pair/Sequence 也没有一致增益

Table 6 的通用 VLM 对照更接近固定模型，但 C.4.2 同时改变了上下文、任务输出与预测构造：Pair 直接判相邻方向；Sequence 对人工划定区间内全部采样图逐图给绝对分数，再差分。后者对区间早期的判断可接触后续图，并不是统一因果前缀、同预算的历史消融。**该区间规则明确写在通用 VLM 小节，不能无证据套给 RoboMeter 的实际服务端。**

| 同模型（Table 6 原值） | Pair Macro-F1 → Sequence | Pair Falling F1 → Sequence |
|---|---|---|
| GPT-5.4 | 0.38 → 0.49 | 0.23 → 0.24 |
| Gemini 3.1 Pro | 0.58 → 0.35 | 0.37 → 0.12 |
| Qwen 3.6 Plus | 0.54 → 0.49 | 0.29 → 0.23 |
| Claude Sonnet 4.6 | 0.40 → 0.48 | 0.26 → 0.26 |

所以既不能声称“更多历史总是提高成绩”，也不能用其中下降的成绩否定历史的作用；还混有绝对评分难度、差分、信息量和提示／预算等因素。这里的 Qwen 3.6 Plus 与本地通用 Qwen3-VL 2B/8B 不是相同实验。

### 3.3 发布标签和复现范围仍有具体未知

论文 C.3—C.4 将目标空间写成二分类；[发布数据](sources/recovery_search_20261003/RoboPulsePlusPlus.jsonl)实有 537 个 0 区间，[作者回复](https://huggingface.co/datasets/lyy0715/RoboPulsePlusPlus/discussions/2)说明 0 是停滞、-1 不必不可逆。数据卡说明论文表格是二分类，但本次未查到 0 区间及零差分在计算中的完整处理代码。因此不自行并类，也不据此复算 Table 6/8。

这属于作者评测的可复现性细节，不是“问题基底不存在”，也不是已证实的新机制缺陷。两条已核发布帧约每 0.5 个上游播放秒一张，与论文通用 1 FPS 表述不能直接互换；只沿用原映射，不为了对齐论文重定义机器人时钟。

## 4. ep621 与 ep618 能说明什么

| 核查项 | ep621 | ep618 |
|---|---|---|
| 来源 | ViFailback `stack_three_color_cubes_ep2/episode_36`，LeRobot 5197 | ViFailback `stack_three_color_cubes_ep1/episode_58`，LeRobot 5060 |
| 作者原失败标签 | `task planning`，第 5 子任务 | `gripper 6d-pose`，第 5 子任务 |
| RoboPulse++ 原整体标签 | 0—22 上升，22—28 下降 | 0—18 上升，18—29 下降 |
| 我们的单人关系观察 | 绿—蓝关系先成立，后续错误操作破坏它；末段未见恢复 | 后续红块操作失败，但可见绿—蓝关系保持 |
| 对固定方向的价值 | 具体体现先前进展不一定仍有效 | 反例提醒：总体下降不能替代某个旧条件失效 |
| 明确不能说明 | 未完成后续放红块子目标，故不能证明“后续操作成功但破坏其他条件”；也未证实作者 judge 错判 | 不能改称整任务成功，不能证明全时间／亚帧保持或正常调整真值；也未证实作者 judge 错判 |

证据：两条原标注 [ep621](sources/recovery_search_20261003/upstream_trace/ep621_source_annotation.json)／[ep618](sources/recovery_search_20261003/upstream_trace/ep618_source_annotation.json)，[59 帧对应审计](sources/recovery_search_20261003/upstream_trace/exact_pixel_correspondence.json)，[ep621 密集参考](sources/recovery_search_20261003/upstream_trace/ep621_reference_contact.jpg)与[右腕参考](sources/recovery_search_20261003/upstream_trace/ep621_right_reference_contact.jpg)，[ep618 参考](sources/recovery_search_20261003/upstream_trace/ep618_reference_contact.jpg)。本次重新查看两条高视角联系图并核对既存来源／草案，没有改变旧标签。

共同边界：两例不是严格控制其他因素的因果配对，不是独立复核的正式集；14.44／15.04 秒发布视频不证明长时程普遍性；正常调整、慢速、停滞未完整覆盖。ep621 q=12—13 不确定、q=14 暂定可判的单人状态保留，不新造 t_e/t_v。原任务没有额外全程保持禁令，不把曾经达成后失效自动解释为违反一条新指令。分析错误后果不改变作者失败类型。

原库 MIT 与 RoboPulse++ 新增标注 `other` 分开，后者未获再分发授权的结论不变；已看记录、原始重复及其他视角只作开发。源任务／失败类别／子任务／关键帧只按原义复用。

## 5. 真正未知与工程问题

**已有证据支持的剩余难点**是作者基准上 Falling 判断未完全解决；这已经是前人的发现。**目前尚无足够依据支持本项目的新缺口或新架构。**“未报告逐条件评分”是报告覆盖边界，不等于“强方法做不到逐条件判断”；只有整体标量输出也不证明模型内部不含相应信息。

值得保留的窄问题是：**在后续操作都失败的情况下，冻结强方法能否在只看截至当前的合法证据时，区分“先前绿—蓝关系已失效”与“先前关系仍保持”，并对遮挡保留未知？**这是待检问题，不是已发现的失败。两例只提供目标差异，没有提供强方法预测。

待检假设 Q-remain-1：在统一前缀证据和明确关系问题下，现成强方法／简单逐条件适配仍会混淆这两种后果。最小反证是同样条件下现成方法已能区分两例；届时不能用这两例支持新机制。若只看到整体 Falling 原生输出，结论是“输出目标不同、该问题尚未被回答”，不能记作错误；若感知或遮挡主导，亦不能归因历史更新。即使两例答对，也只削弱这个两例动机，不宣称普遍解决。

D051—D054 的 JSON、摘要传递、零历史画面误判、遮挡过度确认及输入预算不匹配属于**我们自己诊断链路的工程／基础感知问题**。所有历史原文与失败保留；本地通用 Qwen 不是 RoboMeter、Robo-Dopamine 或 ViFailback 作者模型复现。修好这些不是收口 A/B 的前置条件，本轮也不继续修。

## 6. 现成资源、最小验证范围与唯一下一步

本次已实际核到的资源与未核到的部分如下。

| 资源 | 实查结果与可用性 |
|---|---|
| Table 8 的原始预测／子集 ID | 论文未列；固定官方工具库目录的 `eval/results/` 只有 `.gitkeep`，未见该实验逐例文件或子集清单。该结论只覆盖本次所查快照，不断言作者未保存或其他位置不存在。 |
| 工具库的 recorded 示例 | [manifest_recorded.jsonl](sources/prm_scope_review_20261003/official/eval/examples/manifest_recorded.jsonl)两个 case 明标 `synthetic recorded smoke`；不能当作作者 PRM 实测输出。 |
| RoboMeter 适配接口 | [源码](sources/prm_scope_review_20261003/official/eval/prm_judge/prm/robometer.py) L67—80 加载所选视频帧并向服务器提交；L392—402 请求只含任务、图像和元数据；L497 起读取整体 `progress_pred` 和 success probabilities，不原生返回 green_on_blue。适配器默认 `use_frame_steps=True`，但仅凭客户端整段提交不能断定服务端逐时用了未来图。 |
| 具体后续代码入口 | 客户端 L173 指向 `robometer/evals/eval_server.py`；此前已有 [RoboMeter 官方目录树](sources/replan_r1/rbm_code_tree.json)，revision `352d160389daa964788de1ec933d1925f3a6de4f`，确有该路径。尚未沿服务端核查 frame_steps 的实际截断／采样。 |
| 权重与完整论文配置 | 工具 README 给出公开 Robo-Dopamine Preview checkpoint 及 revision，不能据此认定它就是 Table 8 当次精确配置；本次未下载。RoboMeter 的论文当次精确 checkpoint、视角／前缀及子集配置仍未全部核定。 |

**下一步只做一件事：定向核读 RoboMeter 官方 `eval_server.py` 的 `use_frame_steps` 数据路径及其直接调用的采样函数，写清每个判断时刻实际可见哪些帧。**从已有固定目录树的[准确入口](https://github.com/robometer/robometer/blob/352d160389daa964788de1ec933d1925f3a6de4f/robometer/evals/eval_server.py)开始，只读必要源码，不运行、下载权重或扩展泛搜。产出应是一张“时刻→输入帧范围→输出含义”的证据表；遇到无法确定的外部配置明确停止在未核定，不推测因果权限。

选择这一步的理由：Table 8 已显示强序列方法对已知现象表现较好，优先查其真实能力边界比继续修弱替代模型更能决定是否值得研究。它也能避免把离线序列优势误当成在线条件监测已解决，或反过来无证据声称 RoboMeter 看了未来。这个源码问题无需模型复现即可回答其公开实现范围；仍不能单凭代码得出新方法必要性。

只有之后确需回答“该冻结强方法在这两条原生进展区间是否预测正确”，且公开逐例输出确实不可得，才考虑**两条已追溯开发轨迹的最小原法推理**：固定精确 checkpoint、原生任务／输入／采样／方向映射，保留原输出，先回答原生方向问题；不重跑 700 集、训练或搭建完整报告系统。这也不是完整 Table 8 复现，缺子集与配置就不能冒称复现成绩。

若要回答 Q-remain-1，则另需明确逐条件合法适配，避免要求只返回标量的原法输出不存在的字段；只补两例关系和可判性复核，不重标整库。改变问题文本、输出或前缀均标为适配，不能伪称原法。现有资源条件和本轮无模型边界不允许自动启动；也不默认转入 Qwen 调试、H1/C1 或阶段 8。上述是将来具体问题的最小范围，不是要求先复现才能承认已有现象。

## 7. 本轮更新与核验

已把[状态入口](status.md)、[R1 进度](../docs/plans/2026-10-03-task-progress-research-replan.md)、[决策日志](decision_log.md)、[来源续查 §13](07_alternative_sources_review.md#13-研究基底阶段收口与当前入口纠偏d055d057)和[现成证据追加](existing_problem_evidence.md)同步到本结论；历史原文保留，修改前十个关键文件另有字节级备份及[哈希](sources/prm_scope_review_20261003/before_edit.json)。

没有新的数据事实或运行，因此 `experiments/data_manifest.json` 保持 S7-screening-4 且字节不变；S6-draft-4、配置、08 实测报告和 run ledger 均不改，不新增运行记录。收尾检查见[验证报告](sources/prm_scope_review_20261003/validation.json)：文档本地路径／锚点、JSON、源文件 SHA、历史保留与不应改动文件分别核验。核验仅证明文件一致性，不冒充独立标注或实验验收。
