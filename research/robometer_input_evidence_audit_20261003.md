# RoboMeter 输入证据审计：ep621 还不能作为干净的原法错例

日期：2026-10-03；单执行者。承接 [原生试卷核查 D069—D071](native_task_gap_audit_20261003.md)，本轮只执行其中冻结的下一动作：核固定源码抽帧、原视频坐标和可见性。零模型调用、零网络下载，不设计架构。全部材料仅开发，单人看过完整参考，不是独立或前缀盲审。

## 1. 当前结论与研究意义

目前有作者已知的原生下降方向判断难点 A，以及尚待验证的同任务窄假设 B；仍没有 RoboMeter 或同卷强法在 ep621 上的逐例错误。这个审计得到的实质进展是：**“原法没采到历史”不能笼统解释这条材料；但遮挡、输入网格与评分边界仍使它不适合直接归因于旧成果更新不足。** 因而降低 ep621 作为首个机制反例的优先级，保留为采样/遮挡诊断和开发材料。

ep621、ep618 原生标签同为末段 Falling，但旧绿—蓝关系一个失效、一个保持。原法对两者都判断下降完全可能正确；它们不能单凭这组原生标签组成逐条件有效性判别试卷。若要求原法另报指定关系的成立/失效/未知，即新增 C 输出义务。

## 2. 固定的一手源码与真实权限

本轮读取本地已登记官方快照，不重新下载。

| 来源 | 核验事实 | 边界 |
|---|---|---|
| PRM 客户端，[robometer.py](sources/prm_scope_review_20261003/official/eval/prm_judge/prm/robometer.py)，revision `34e8cd4396fe903d6205028da17e32ba01d723d9`，L311、L357—364 | 数组输入直接载入；视频默认 nominal fps=1，数量按 `round(n*fps/native_fps)`，位置为包含两端的整数 `linspace`；不是机械地每25帧取一次 | 两种合法接口不等于论文实际选用的接口；数组路径不是作者实验配置的证明 |
| RoboMeter [eval_server.py](sources/direction_selection_20261003/eval_server.py)，revision `352d160389daa964788de1ec933d1925f3a6de4f`，L211—234 | 对每个查询前缀用 `linspace(0,i-1,4,dtype=int)` 选四帧，分别建样本；没有把前次生成文本作为该循环的记忆传入 | 只重建索引，没有启动服务、加载权重或产生预测 |
| [rbm_heads.py](sources/direction_selection_20261003/rbm_heads.py)、[setup_utils.py](sources/direction_selection_20261003/setup_utils.py) | PIL图像、Qwen视觉处理、多图/视频分支和resize受配置控制 | 没有实例化最终processor；这里看的是解码原图，不证明模型最终tensor中同样可辨。类默认128不能当论文实际分辨率 |
| PRM论文 C.4，既有[论文审计](prm_robopulse_scope_review.md)及[评分器核查](native_task_gap_audit_20261003.md) | 论文写1 FPS、五帧因果差分平均、区间首尾去两帧；仓库默认居中曲线平滑不能替代该评分器 | 原始0区间处理、端点、差分对齐、实际有效点掩码仍未恢复 |

精确源码哈希、提取的纯抽帧函数与服务端表达式见 [code_extraction](sources/robometer_input_audit_20261003/code_extraction.json)。只执行纯索引算术及本地解码，无模型代码导入。所有查询像素均不晚于当前帧；但客户端网格依赖完整视频长度，不能冒称精确实时流式输入，也不因此声称有未来图像泄漏。

## 3. 原生任务—输出—区间—媒体绑定

两例完整指令相同：

> Use the left arm to stack the green cube on top of the blue cube. Subsequently, use the right arm to place the red cube on top of the green one to complete the three-layer structure.

原生方法输出是整体进展曲线；RoboPulse++区间标签是整体进展方向，**不是指定关系标签，更不是监测器错误标签**。

| 项 | ep621 | ep618 |
|---|---|---|
| 上游物理episode | ViFailback `stack_three_color_cubes_ep2/episode_36` → LeRobot5197 | `stack_three_color_cubes_ep1/episode_58` → LeRobot5060 |
| 发布逻辑帧与末段标签 | 29帧；22—28，-1/Falling | 30帧；18—29，-1/Falling |
| 本地高位相机视频 | 361帧、25 FPS | 376帧、25 FPS |
| 发布帧↔原视频 | 29张逐像素精确匹配 | 30张逐像素精确匹配 |
| 开发参考含义 | 绿在蓝上曾成立，后来失效；后续红块任务失败 | 后续红块任务失败，绿—蓝关系保持 |
| 作者该方法逐例预测 | 未取得 | 未取得 |

原视频坐标 `frame/25` 是编码回放秒，不是额外推测的机器人时钟。原始 revision `21df46c2585c52e5a62df5f4b946bae6cbc6fed7`，转换版 `619791b94f61667333fe179d471051e0bca0e06f`；RoboPulse++ `abcb94c1e924282c0005e53cff0b22a073de748a`。URL、媒体SHA、许可及上游对应沿用 [source_mapping](sources/recovery_search_20261003/upstream_trace/source_mapping.json) 和现有 [data_manifest](../experiments/data_manifest.json)。上游MIT不自动解决聚合标签的全部许可口径；本轮未作新的许可结论。

逐例预测缺项不是笼统的“等作者”：已经查 PRM Table6/8、固定仓库 `eval/results/`（只有`.gitkeep`）、`eval/examples/manifest_recorded.jsonl`（synthetic smoke，不是作者预测），以及RoboMeter官方服务入口。此前[精确原法缺项清单](sources/native_gap_audit_20261003/inference_readiness.json)仍成立：本机精确权重/依赖/运行条件尚未齐备。本轮没有准备启动模型，未重新硬件审计，也没有以普通Qwen替代。

## 4. 两条接口路径与28个查询包

在看查询包前写入 [scope](sources/robometer_input_audit_20261003/scope.json)。保留全部：发布数组路径中末段全部逻辑坐标；默认视频路径中当前源帧不早于发布Falling起点的全部查询。ep621为7+3包，ep618为12+6包，共28包、两个物理episode；没有把多帧算多个任务。完整输入、任务、网格和时间见 [input_manifest](sources/robometer_input_audit_20261003/input_manifest.json) 与 [坐标CSV](sources/robometer_input_audit_20261003/query_coordinates.csv)。视频路径未擅自转移作者评分标签。

ep621的原视频默认1 FPS路径实际选14帧：`0,27,55,83,110,138,166,193,221,249,276,304,332,360`。它不等于29张发布PNG的序列。下表选四帧包说明结果，完整记录包含其余正确/未知材料：

| 路径/查询 | 四个原视频帧 | 当前秒 | 单人输入证据判断 |
|---|---|---|---|
| 发布数组 q22 | 6,93,181,281 | 11.24 | 当前绿—蓝关系仍保持；Falling区间起点不等于旧关系已失效 |
| 发布数组 q24 | 6,106,206,306 | 12.24 | 206提供历史完成证据；306当前支持关系遮挡较重 |
| 发布数组 q25 | 6,106,206,318 | 12.72 | 历史证据保留；当前遮挡 |
| 发布数组 q26 | 6,106,218,331 | 13.24 | 历史证据保留；当前遮挡 |
| 发布数组 q27 | 6,118,231,343 | 13.72 | 231为旧关系成立，343绿块在桌上且与蓝块分离；本次最清楚的开发失效锚 |
| 视频默认 q11 | 0,83,193,304 | 12.16 | 历史证据保留；当前遮挡/过渡 |
| 视频默认 q12 | 0,110,221,332 | 13.28 | 历史证据保留；当前遮挡 |
| 视频默认 q13 | 0,110,221,360 | 14.40 | 分离迹象但仍部分遮挡，证据弱于343，待复核 |

这里的未知是**本次材料可辨性审计结论**，不是作者新标签，也不是模型答复。全部单人判断见 [visibility_review](sources/robometer_input_audit_20261003/visibility_review.json)，旧关系参考标签保持不改。四张联系图覆盖所有包：[621数组](sources/robometer_input_audit_20261003/ep621_published_array_packets.jpg)、[621视频](sources/robometer_input_audit_20261003/ep621_mp4_default_1fps_packets.jpg)、[618数组](sources/robometer_input_audit_20261003/ep618_published_array_packets.jpg)、[618视频](sources/robometer_input_audit_20261003/ep618_mp4_default_1fps_packets.jpg)。不可把当前遮挡解释成“不可能推断”；只能说它不足以干净归因于推理机制。

## 5. 评分边界的最低成本反证

**条件检查，不是论文评分重现：**假如直接对发布逻辑区间22—28应用首尾各去两帧，闭区间读法剩24、25、26；半开读法剩24、25。最清楚的q27在两者中都被去除，余下帧正是当前关系遮挡较重的片段。[边界算术JSON](sources/robometer_input_audit_20261003/boundary_sensitivity.json)保留两种解释；没有选择较有利的一种。

实际作者1 FPS网格、差分对齐和掩码未知，所以不能声称Table6确实没有评到失效，也不能声称强法在这个片段答错。可以确定的是：以“发布帧看到失效”直接跳到“作者原生评分已有这类强法错误”，证据链不成立。

## 6. 研究选择、推翻条件与下一步

不增加第三个概念候选。沿用B1“旧终局关系撤销附近的原生下降漏判”作待否定入口，B2/H-D继续无正例。B1的重要性来自最终任务要求，其创新性和强法错误尚未证明；ep621材料不能承担机制结论，ep618保留旧成果保持控制。RoboMeter已有历史能力、ProgressCompass解决任务上下文、R²VLM动态更新步骤，继续是强反证，不能用本次可见性审计抹掉。

若精确强法在可见证据充足、原生评分可对齐的片段正确输出下降，当前B1故事就应收窄/放弃；若问题仅在新增逐条件三值输出出现，则转标C；若差异被输入采样、遮挡、语义或阈值解释，则不能归因为历史更新机制。本轮已发现足够的材料混杂，**现在没有足够依据开始设计改进架构**。

下一件单人低成本动作：有界核现有本地RoboPulse++任务和三份ViFailback原标注中，是否有“完整任务明确、当前关系清楚、下降区间内有足够非边界可见帧”的候选；先列全部元数据纳入/排除及匹配ID，再只查看本地已存在媒体，不按H-D预筛，不下载整库。沿用旧成果保持、合法撤回和遮挡对照。如果本地没有第二条可对齐材料，就明确停止扩张这条案例故事，保存精确原法缺项清单；不能靠追加概念或普通Qwen填补强法证据。

本轮派生19张原视频PNG，无新增物理episode。只因新增输入坐标事实在data_manifest追加派生审计记录；模型台账、08、评价协议与配置字节不变。S6-draft-4、S7-screening-4、C1/C2/C3未批准及阶段8关闭保持。来源、派生和保护文件哈希与链接检查见 [validation](sources/robometer_input_audit_20261003/validation.json)、[source_hashes](sources/robometer_input_audit_20261003/source_hashes.json)、[artifact_hashes](sources/robometer_input_audit_20261003/artifact_hashes.json)。
