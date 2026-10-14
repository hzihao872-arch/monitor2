# 从宽基底原生错题出发：两条可供阶段汇报的方向线索

日期：2026-10-03。单执行者；承接用户“先找到可能方向，再向老师阶段汇报”的新优先级。本轮核作者原生任务错误，不把独立复核、局部错误率或完备评分器作为提出假说的前提。不设计架构、训练或运行模型，也未向老师发送信息。

## 1. 这轮真正前进了什么

**找到了一条绑定具体任务的 RoboMeter 原生输出错误：在“Unzip the pencil case”检索评价中，偏好分支的前五条包含一条失败轨迹，且只包含三条成功轨迹中的两条。** 这来自作者 Table XXVI，不是我们看失败视频推测模型犯错。同一表中进展分支选到3成功+2部分完成，没有失败，构成强反证和现成对照。

另一个直接任务级入口是“Fold the towel”：作者 Table XXVII 中 RoboMeter 的失败检出率TPR为0.54，成功正确识别率TNR为0.56。它同时有漏报与误报，值得研究正常调整、反复操作、真实停滞或未完成之间的混淆。但尚不知道这些错误分别属于哪种执行情形。

**现在可以拿给老师讨论方向；还不是一个已证明的新B类缺口。** 新进展是“有名有据的强方法错题入口”，不再只是一般Falling低分或机器人执行失败。主要文献仍是已缓存的[官方论文v2](sources/native_gap_audit_20261003/robometer_v2.html)，原始出处为 [RoboMeter附录E-4](https://arxiv.org/html/2603.02115v2#A5.SS4)、[E-5](https://arxiv.org/html/2603.02115v2#A5.SS5)。机读摘录包含完整表格与上下文：[author_evidence.json](sources/native_error_leads_20261003/author_evidence.json)。

## 2. 从同一篇论文内部定位错误，保留答对项

### 2.1 原生失败检测：哪里更值得查

原生输入为指令与视频观察，输出逐帧进展/成功概率，再由作者窗口规则形成整轨失败判断。失败类包含failure及未完成任务的suboptimal；下表只列同一次评价的TPR/TNR，不与其他论文的MAE或F1混排。

| Table XXVII任务 | RoboMeter TPR：失败检出 | RoboMeter TNR：成功正确识别 | 当前能推断什么 |
|---|---:|---:|---|
| move banana | 1.00 | 0.75 | 有成功误报；没有报告失败漏检 |
| move mouse | 1.00 | 0.75 | 同上，不能凭任务包含约束就说约束判断失败 |
| pour pebble | 0.71 | 1.00 | 有未成功执行被漏报 |
| **fold towel** | **0.54** | **0.56** | 两个方向都存在较明显错误，优先查错因 |
| pull tissue | 0.73 | 0.50 | 成功误报值得查，失败也有漏报 |
| put spoon | 0.57 | 1.00 | 有漏报；现有论文展示的掉落案例是正确检测，不能当错例 |
| stir pot | 0.82 | 1.00 | 存在漏报；RoboReward同表TPR0.91/TNR1.00，是替代方法已较好的反证 |

不能从“折毛巾”直接推出“可变形物体是原因”，也不能从“抽纸”直接推出“重复动作是原因”。作者Fig.9已经展示成功识别停滞/振荡的例子，所以“不会识别停滞”不能成为新贡献。合理候选是**哪些正常调整与未完成过程仍被混淆**，再看具体错误是否支持。

正文写100条、30成功/70失败、7任务；每任务实际分母和评价ID未公开绑定。本地MIT元数据有304条，LeRobot中“Fold the towel in half”有56条（24 successful、24 suboptimal、8 failure），都不能当Table XXVII折毛巾那一行的分母。TPR/TNR是整轨监测成绩，不是逐帧下降准确率。

### 2.2 原生偏好/检索：已绑定到具体任务的错误

Table XXVI使用有质量标签的Trossen OOD数据，按语言任务检索五条。文中说每个目标任务有3成功、2部分完成、2失败。方法沿用前文：Prog按预测进展的VOC排名，Pref汇总两轨偏好比较为胜出矩阵并排名；前文检索使用腕部相机。不能将其写成按最后一帧分数排序，也不能把离线检索直接叫在线报警。

| 目标任务 | 方法 | 成功 | 部分完成 | 失败 | 不相关 |
|---|---|---:|---:|---:|---:|
| Open the red drawer | RoboMeter–Prog | 3 | 2 | 0 | 0 |
| Open the red drawer | RoboMeter–Pref | 3 | 2 | 0 | 0 |
| Unzip the pencil case | RoboMeter–Prog | 3 | 2 | 0 | 0 |
| **Unzip the pencil case** | **RoboMeter–Pref** | **2** | **2** | **1** | **0** |

这足以证明**偏好分支最终检索排名中存在质量选择错误**：至少一条成功轨迹未入选，而一条失败轨迹入选。不足以证明某一个success–failure直接两两比较必然反转，原因还可能在偏好聚合、视角、输入、并列处理等环节。

表格也包含SigLIP、STRAP、RoboReward失败选入，但不能把它们与Pref选入的失败说成同一episode：没有逐例检索列表。进展分支在此处正确，更不能说所有强法存在共同错误。

补充背景：Tables XIV/XV的RoboMeter不同质量对偏好准确率平均82.5%，不同任务对97.6%；Trossen分别76.2%与99.0%，作者每数据集各抽500对。它们提示质量区分值得查，但两类配对不同，不是纯因素消融；也不能把82.5%称为本项目“近完成”子类准确率。新增核读固定源码的 `QualityPreferenceSampler` 明确按同任务、不同质量构造对（见§6）；论文当次500对ID仍未取得。

## 3. 实际材料绑定：七条笔袋视频全部保留

已有本地LeRobot任务/episode/帧元数据已读，本轮另取同一官方固定revision下的 `train/metadata.parquet` 和该任务全部七条小视频。固定revision：`3f3ee69ecc0ee0db627684da7d599ec26d08175c`；来源为 [robometer/rbm-1m-ood](https://huggingface.co/datasets/robometer/rbm-1m-ood/tree/3f3ee69ecc0ee0db627684da7d599ec26d08175c)。数据卡Apache-2.0；原始采集层许可本轮没有重新审计。

**模型原生任务—输出：**按“Unzip the pencil case”比较/排列执行质量，输出偏好及检索前五名。**作者错误证据：**Table XXVI任务级名单组成。**具体媒体—作者标签：**如下。缺少的是把作者错误选择接到某一行的视频ID，并非缺少任务或现有材料。

| 官方文件 | 官方UUID | 作者质量标签 | 同序号LeRobot episode候选 |
|---|---|---|---:|
| [video_000016](sources/native_error_leads_20261003/video_000016.mp4) | `70598bda-1b06-469e-acc2-8207e178df25` | success | 16 |
| [video_000019](sources/native_error_leads_20261003/video_000019.mp4) | `8906e1e0-14df-4cb3-b82e-baf44e77224b` | failure | 19 |
| [video_000022](sources/native_error_leads_20261003/video_000022.mp4) | `4d984596-5a93-468d-8ba0-7279ffeb3b52` | failure | 22 |
| [video_000023](sources/native_error_leads_20261003/video_000023.mp4) | `299ab523-67f7-42a2-a3d6-fd41b6904156` | suboptimal | 23 |
| [video_000024](sources/native_error_leads_20261003/video_000024.mp4) | `8556e043-8f10-4fa1-8775-1f7a22fb50db` | success | 24 |
| [video_000025](sources/native_error_leads_20261003/video_000025.mp4) | `2378544f-0f0c-4082-a234-a53780f6a1e2` | suboptimal | 25 |
| [video_000026](sources/native_error_leads_20261003/video_000026.mp4) | `abe808eb-ae29-4ee4-8c52-39acc7cab0d5` | success | 26 |

`train`路径的UUID与LeRobot另一布局的语义ID不同；数字序号、任务、来源和归一化质量吻合，但尚未逐像素验证两布局身份。**表中的视频绑定直接以train元数据为准，不依赖这个跨布局候选对应。** Table XXVI候选检索库可能含Trossen其他任务的干扰轨迹；七条是目标任务的完整公开候选组，不冒称完整检索池或论文实际ID清单。

每段本轮视频为320×240、64帧、30 FPS、2.133333 s。这是发布重采样片段回放时钟，不能说机器人在2秒内完成任务。另一布局32帧、10 FPS、3.2秒的时钟不混用。抽查统一帧0/8/16/24/32/40/48/63；[56帧总览](sources/native_error_leads_20261003/pencil_case_overview.jpg)覆盖所有七段，媒体保留全部64帧。例：失败UUID `8906...` 的f32对应发布回放1.0667 s，f63为2.1 s；这些时间点没有作者逐帧质量标签，只有整段failure。

单人初看：各质量轨迹都包含接近同一笔袋、操作拉链附近的视觉过程；动作/目标相关性不足以自动说明完成质量。小拉链、局部开口、腕相机运动和遮挡是**待排查的竞争解释**。没有把视觉上看着相似升级为作者已证明的错因，也不重标作者success/suboptimal。当前没有查看任何该组模型逐例输出。

来源/字节/LFS SHA在[fetch_manifest](sources/native_error_leads_20261003/fetch_manifest.json)，媒体参数和标签在[clip_registry](sources/native_error_leads_20261003/clip_registry.json)，既有布局坐标在[task_episode_bindings](sources/native_error_leads_20261003/task_episode_bindings.json)。没有公开逐例预测已绑定；查过的论文表、结果目录见[此前审计](native_task_gap_audit_20261003.md)。

## 4. 两张探索方向卡：足够讨论，不提前宣布创新

| | 方向Q：目标/动作相关，但完成质量判别不足 | 方向T：正常调整与真实停滞/未完成混淆 |
|---|---|---|
| 当前优先级 | **优先材料入口**：有任务级原法错误及七段公开候选 | 更贴近在线监测的并行文献线索，本轮不另开模型实验 |
| 原生输出 | 两轨偏好、检索排序；进展分支是同系统强反证 | 整体进展/成功和原生失败报警 |
| 已知作者问题A | 笔袋Pref前五含失败、漏成功；不同质量配对仍有错 | 折毛巾TPR/TNR0.54/0.56；抽纸0.73/0.50 |
| 候选B解释 | 当目标对象、操作套路都正确，真正完成差别集中在局部结果时，是否容易把“做过/接近完成”评得过高 | 成功执行中的阶段调整、回退或重复，是否与真正没有进展的操作混淆 |
| 已有覆盖/反证 | Prog在笔袋组正确；红抽屉两分支都正确；原方法本就训练质量偏好 | 作者已正确检测部分停滞/振荡；详细任务说明可改善长任务进展；ProgressCompass已处理上下文 |
| 目前未知 | 错选ID、具体两两偏好、聚合名次、相机/采样、是否真的局部完成差别 | 哪些episode误报/漏报、对应过程情形、阈值与视觉各自贡献 |
| 最便宜否定 | 若错误仅是聚合/视角，或进展/成功均正确，就不能声称监测器普遍不会判完成；放弃泛化说法 | 若错误不集中于调整/重复，或仅改变原生阈值即可解决，不建立该机制故事 |

Q是RoboMeter宽原生任务内的线索，但若项目继续限定在线进展监测，它只能提供诊断入口，必须再检查进展/成功输出，不能用偏好检索错误替代在线漏报。T的任务范围更贴近原领域，但现阶段解释证据更弱。**两者尚未构成一个经逐例验证的共同错误类。** 不将“局部结果”与“正常调整”强行统一成新的架构概念。

H-D退居已有备选，不再指导本轮筛样本。ProgressCompass上下文解法、R²VLM步骤更新能力仍需保留，不重复提出“加上下文/加历史”作为新颖性。

## 5. 给老师阶段汇报可以怎么说

“我们选择RoboMeter作为宽机器人奖励/进展基底，先从作者原生评价找剩余问题。目前找到两个具体入口：折毛巾监测既有漏报也有误报；拉开笔袋任务中偏好检索会选入失败轨迹，而进展分支在同组正确。已取得笔袋任务的全部七段候选视频和作者质量标签。我们想优先检查，在动作和目标看起来正确时，模型是否仍会混淆真实完成程度；同时区分输出分支、视觉信息与排序规则造成的错误。现在有探索价值，但尚未证实新的共同缺口，也还未设计方法。”

这个汇报不需要先有正式样本量或独立标注。老师可帮助判断两个入口中哪个科学问题更值得展开；本报告不是请求批准架构，也没有代用户联系老师。

## 6. 已追到的原法代码与下一动作

本轮已查非截断官方代码树 `352d160389daa964788de1ec933d1925f3a6de4f`，并有界取得5份评价源文件，全部Git blob匹配。其中：

- [quality_preference.py](sources/native_error_leads_20261003/code/robometer/data/samplers/eval/quality_preference.py) L135以后按task分组，明确排序 `failure < suboptimal < successful`，构造跨质量对。这提供了原生质量诊断入口，不需新增三值条件输出。
- [compile_results.py](sources/native_error_leads_20261003/code/robometer/evals/compile_results.py) 的 `run_quality_preference_eval` 读取偏好预测/参考和chosen/rejected元数据，按任务及质量组合汇总。[README](sources/native_error_leads_20261003/code/robometer/evals/README.md)列出逐例results、task_groups、task_details文件格式。**能保存结果不等于作者已发布这些结果。**
- 本轮所读5文件与树路径尚未找到Table XXVI完整检索胜出矩阵聚合脚本；不能把一般quality preference准确率计算冒充该表复现，也不能宣布整个官方仓库都没有相关实现。

已将七段视频的全部16个跨质量无序对登记为[原生诊断输入清单](sources/native_error_leads_20261003/native_pair_input_manifest.json)：6成功—失败、6成功—部分完成、4部分完成—失败。只登记，不运行；A/B展示顺序、精确采样、相机与checkpoint须在实际运行前冻结。这16对共享七个episode，不能当16个独立任务，也不等于作者Table XXVI检索结果。红抽屉答对组保留为元数据控制。

**下一件具体动作是把16对中的原法偏好判断与同轨进展/成功判断放进同一份诊断单，先核实际使用的腕相机和原法配置，再决定是否具备少量精确推理条件。** 优先排查“偏好本身错”还是“聚合排名错”，不继续围绕ep621补细节。权重和论文检索配置仍缺，不用普通Qwen代跑。

如果源码没有对应输出，保留这个有证据的任务级方向即可向老师讨论，不要求等待作者。准备实际原法诊断时才完整核协议、精确权重和资源；本轮无推理。只有需要正式H1效果比较时才恢复独立复核等门槛。

## 7. 可复核记录

新来源13件共843,835 B，其中7视频694,343 B、元数据57,703 B、5份源码91,789 B；均先核固定树大小再GET，媒体/元数据核LFS SHA，源码核Git blob。沿用上一来源批次6MiB总预算，5,402,835+843,835=6,246,670 B，未超6,291,456 B。初始512KiB小文本上限在查清七段总大小后，明确改用原6MiB剩余预算，见[media_scope](sources/native_error_leads_20261003/media_scope.json)；没有增加总体预算。未下载大聚合视频、新权重或整库。

本机默认PyArrow19读已有Parquet报格式错误，改用已经安装的Python3.12/PyArrow25.0.1成功读取，未安装依赖。工作流preflight只读识别环境，不视为已完成原法运行准备。模型运行次数为0；run_ledger/08/07协议/config保持字节不变。数据清单仅因新媒体/元数据追加；所有任务组、重复视角和转换版本仅开发，不能用UUID变化转成保留测试。S6-draft-4/S7-screening-4、C1/C2/C3未批、阶段8关闭保持。

[验证结果](sources/native_error_leads_20261003/validation.json)包括来源哈希、7段媒体标签/数量、56张派生帧、JSON、报告链接和保护文件哈希。
