# 宽任务基底的原生错题核查：还没有证实新的 B 类缺口

日期：2026-10-03，Asia/Shanghai。承接 D017、D024—D068；本轮单执行者、仅研究与来源核验。没有模型运行、训练、付费 API、新权重、整库下载或架构设计。S6-draft-4、S7-screening-4 保持，C1/C2/C3 未批准，阶段 8 关闭。

**结论：作者已经证明原生下降判断有残余错误；我们尚未证明一个新的、强方法仍判断不好的同任务窄子类。**本轮取得实质反证：ep513 全部 19 张发布帧不支持 H-D——第一项小瓶放置保持，第二项试管放置未完成。R²VLM 官方单样本推理入口也已补核到，旧记录中的“推理入口未审查”不再是完整现状。两项进展均不等于取得强法在目标子类上的逐例错误。

## 1. 继承状态与类比范围

按指定顺序核读现有状态、D055—D068 的证据界限、EvoNav 论证及 R1 续行计划；定向复核旧数据清单、来源筛选与已有论文/代码。工作目录不是 Git 仓库，修改前为 status、decision_log、data_manifest 和不得变更的运行/协议文件保存了[字节备份与 SHA](sources/native_gap_audit_20261003/before_edit.json)。目录中未发现晚于 D068 的另一份研究结论需要合并。

Open-Nav 与 EvoNav 都解决零样本连续环境视觉语言导航。Open-Nav 已有轨迹历史与进度估计；EvoNav 的窄解释是既往错误反馈及未来动作/地标推演利用不足。整体导航比较、案例及消融支持该解释，但不能把导航 SR 当作局部判断准确率，也不能推断作者实际研发顺序。[Open-Nav §III—IV](https://arxiv.org/html/2409.18794)、[EvoNav 正文 §5](sources/evonav_main.pdf)、[补充 A—B](sources/evonav_supp.pdf)

**RoboMeter 仍是较合适的宽基底角色，而非功能等同物。**它跨机器人、任务、场景输出逐帧进展/成功及两轨偏好，是奖励与监测模型；Open-Nav 组织感知、候选航点和决策来实际行动。PRM-as-a-Judge 是评测工具，RoboPulse++ 是试卷；二者不能替代被诊断的模型。Robo-Dopamine 也是宽覆盖候选，并在同卷下降判断更强，应成为关键同任务比较。其完整 RL 框架虽包含行动学习，却需要任务适配/交互，不能仅为“像完整代理”而优先于本项目的冻结监测目标。R²VLM 的递归步骤更新更贴近过程推理，但原生证据主要在 ALFRED/Ego4D；目前没有足够理由把它认定为比 RoboMeter 更合适的**机器人操作宽基底**。[RoboMeter §III—IV](https://arxiv.org/html/2603.02115v2)、[Robo-Dopamine §3](https://arxiv.org/html/2512.23703v1)、[R²VLM §3](https://arxiv.org/html/2603.17312v1)

ProgressCompass 是已针对上下文缺口提出的解法，不能把它已经解决的问题重新命名成我们的创新。宽基底只提供寻找空间，不保证存在新缺口。

## 2. 先固定判断对象，避免把 B 偷换成 C

| 语义对象 | 本轮处理 |
|---|---|
| 事件曾经发生 | 历史事实成立后，物体移动不必抹去该事件；例如完成一次按钮按压。 |
| 最终仍须满足的结果 | 需按完整任务解释其终局义务；先前成立不能直接证明现在仍成立。 |
| 执行中持续约束 | 必须有相应任务要求；不能从“最后放在架上”增设“此后任何时刻都不能离开”。 |
| 合法撤回/正常调整 | 指令要求送回、重放等可以继续增加整体进展；已绑定的 place_block_mat 是控制。 |
| 破坏旧成果 | 必须先证实成果曾达成、任务仍要求保留、后续可见失效；不能只读负标签。 |
| 遮挡下未知 | 区分真实状态与当前输入能否判定；不把看不见自动记失效或保持。 |

**A**：作者已经报告的原生判断错误。**B**：同一原生输出和评分目标下，尚未单列验证的错误子类。**C**：额外要求指定条件的当前成立/失效/未知。

纠正旧报告 §2 一句过宽表述：**给原生进展任务加入失败轨迹，不自动构成 C。**仍用整体进展/方向评价时，可以是新的测试分布或 B 子类；只有增加逐条件判断等输出义务才构成任务扩展。反之，两例都标 Falling，而旧关系一失效一保持，不代表原生整体方向必须给出不同答案。不能用 ep618/ep621 的关系差异直接要求原生标量区分二者。

H-D 也有这个约束：新步骤成功与旧成果损坏并存时，整体净进展不必由逻辑直接确定为下降。必须有该任务原生参考/作者方向标签；否则先是语义材料问题，不能替模型规定一个未获支持的答案。

## 3. 作者自己的试卷：任务、分母和能支持的结论

以下分数分别保留原生含义，不跨论文排行。

### 3.1 RoboPulse++ / PRM-as-a-Judge 1.5

重新从[固定论文 C.1—C.5.2](sources/recovery_search_20261003/robopulse_paper.html)提取表格，并与[官方同版本](https://arxiv.org/html/2608.14284v1#A3)核对。

| 项目 | 核验结果 |
|---|---|
| 原生任务、输入 | 任务条件化的整体进展方向；任务文字及采样观察。C.4 写 1 FPS。PRM 各自使用原生格式；一般 VLM 的 Pair 是相邻观察，Sequence 是人工区间全部帧，因此不是统一因果权限。Dopamine Forward 的官方实现是起始—当前比较，不能笼统叫相邻帧。 |
| 公开试卷分母 | test 700 episodes、17,052 逻辑帧、2,244 区间。Table 5 的 275 是各来源 task entries；JSONL 的独特完整任务字符串为 269，不能静默混为一个任务分母。实际重算见[分母审计](sources/native_gap_audit_20261003/native_denominator_audit.json)。 |
| 输出与评分单位 | 绝对进展先差分；连续量做五帧**因果**移动平均后取符号，类别输出直接映射。每段剔除首尾各两个采样时刻，汇总全体有效预测点计算 F1/Accuracy。不是每 episode 一票，也不是 2,244 个独立任务。 |
| 尚未齐全的分母 | JSONL 实有 +1/0/−1 区间 1,130/537/577；正文二分类只写 ±1。0 标签处理、预测差分恰为 0 的处理、端点和首个差分对齐、短区间是否被全滤除，所查公开代码没有给 Table 6 的完整评分器。不能自行把 1,707 个非零区间当有效评分分母。Table 8 也未给具体子集 ID、episode 数或有效点数。 |

| 原表/模型 | Rising P/R/F1 | Falling P/R/F1 | Macro-F1 / Accuracy |
|---|---|---|---|
| Table 6 Robo-Dopamine Forward | .92/.92/.92 | .79/.50/.61 | .77/.84 |
| Table 6 Robo-Dopamine Backward | .92/.88/.90 | .72/.55/.63 | .76/.82 |
| Table 6 RoboMeter | .89/.86/.87 | .47/.54/.50 | .69/.80 |

这证明**该卷上的下降漏判与误报仍存在**，Forward 的 Falling recall .50 尤其提示召回不足。它不告诉我们这些错点是否涉及旧成果、H-D、感知错误或遮挡；F1 也不是“有多少机器人执行成功”。正文称最佳 Rising F1 .92 与表一致；不把不同列的最大 precision 当 F1。

Table 8 是历史依赖子集的**类条件准确率**：Forward Rising/Falling/Overall 为 .844/.408/.746，RoboMeter 为 .951/.901/.940。它既留下总体错误，也强烈反对“强法普遍不会处理历史撤销”的故事。跨模型差异不能当纯历史消融，不能拿 .901 与全卷 Falling F1 .50 相减来解释历史贡献。[C.5.2/Table 8](https://arxiv.org/html/2608.14284v1#A3.SS5.SSS2)

C.5.1/Table 7 的 155 个 Falling 区间分成 interaction-relation 121、task-order 34；这是执行失败类型，**不是监测器错判的聚类或分布**。

### 3.2 其他方法的原生试卷

| 方法 | 输入 → 输出；评分单位与分母 | 作者强项、剩余误差及边界 |
|---|---|---|
| RoboMeter | 指令+视频；因果 VLM 给逐帧整体进展、success，双轨偏好。ID Table VI：25,726 条独特标注轨迹；OOD Table VII：571 条，其中 MIT Franka 304。正文 §IV 又写 976 OOD 轨迹、6 embodiments，而 Table VII 为 571/5；该版本存在口径不一致，本轮不擅自调和。成功轨迹的 VOC 是奖励与时间的 Pearson；混合质量排名是 Kendall。 | E-5/Table XXVII 在 MIT Franka 七任务做整轨失败检测，suboptimal 并入 failure；平均 TPR/TNR/F1=.77/.70/.81。fold towel=.54/.56/.58，put spoon=.57/1/.73，只能定位任务层较难，不能归因旧成果。Table VII 的 304 不能直接认定为 XXVII 实际评分总数，后者缺逐例清单。Fig.4 正确降低掉落 marker 的进展，是反证案例；§V 承认稀有失败、长程事件记忆及不可见物理量限制。 |
| ProgressCompass | 指令/前缀画面→自主子任务定位、验证、整体 0–100 曲线。ContextProgress：24任务×5=120 clean episodes、71,708 帧、552子任务；另15 held-out negatives。整体进展 MAE、时间秩相关及边界误差，非逐条件三分类。 | Table 1 RoboMeter 无上下文 MAE25.42，人工 oracle上下文4.91、自接端点11.39；§5 完整系统9.3、ρ=.93。人工子任务和边界属额外信息；附录C部分采样设置也变化，不能说所有资源严格相等。§5.3去除预期转变使 MAE9.3→17.5/18.3，未验证而停住的episode 7→40/45；**7条完整系统停住**是已报告剩余现象，但没有 ID/成因可归为旧成果失效。 |
| R²VLM | 任务文字+当前局部snippet+上一轮递归推理记录→可修订步骤/完成状态与0–100整体进展。ALFRED 669/722、Ego4D 529/718条自动构建后人工保留的未见场景样本。ALFRED 1 FPS、每4秒snippet；Ego4D 2 FPS、每2秒snippet。B.3按推理轮次平均，长轨权重大；完成acc另做类别逆频率加权。 | Table1 ALFRED MAE2.19、ΔMAE2.17、bin .917、acc .988；Ego4D 19.25/3.88/.318/.761。低Ego4D bin提示进展位置仍难，不能归为旧关系错误。§3.2明确更新完成状态；附录E.2展示依据新观察修订步骤，是强反证。主要专家演示、分步事件进展，不是本项目每个持久条件真值。 |
| Robo-Dopamine 原版/公开Preview | 原版指令+起始/目标图+before/after多视角→相对hop，经三种模式融合为曲线。§4.1/Table1评七数据源的轨迹排序；Table2另做三任务，每任务60条（成功/部分成功/失败各20），共180条终局分类。 | Table2多视角56/60、54/60、57/60，平均92.8%，单视角83.9%；这是终局分类，非通用局部进展准确率。多视角针对遮挡/空间精度已有贡献。公开Preview支持无目标图，但不得与原版、PRM Table6或八月2.0精确权重混称。 |
| Robo-Dopamine 2.0（八月论文） | 指令、起始/目标参考、查询状态对、前序/中间历史面板→带符号进展；离线synthetic OOD用成功源轨迹的reference panels，在线才用实际rollout历史。 | Table1五类VOC的同checkpoint static/panel均值.967/.986；OOD-robust .906/.958，仍有误差。这里VOC是Spearman，与RoboMeter的Pearson不同。附录E.2的遮挡例仍有末段偏差、抽屉例过早饱和，是A层剩余案例，但无绑定episode ID/原始输出，不能认作旧成果失效。五类测试各自的确切episode/点分母在所核§4/附录E未找到。 |
| RoboMonitor（边界比较） | 指令+两/三相机八时刻因果窗口→七类phase、completion、failure。四任务全部参与监督；52或100训练episode，66 held-out episodes/7,022观察窗口，两个SFT种子。 | TableI 52训练时failure AP45.87±.68，RoboMeter+Temporal SFT59.39±3.11；100训练时RoboMonitor72.01±.14。不是冻结零样本分数，也不是旧成果子类成绩。不能通过这种训练量差异给本项目强法排榜。 |

一手出处：[RoboMeter v2 Tables VI/VII/XXVII、E-5](sources/native_gap_audit_20261003/robometer_v2.html)、[ProgressCompass §2/3/5、附录B/C](sources/system_refresh_20261003/progresscompass_v1.html)、[R²VLM §3/4、附录A/B/E](sources/system_refresh_20261003/r2vlm_v1.html)、[Robo-Dopamine 原版 §4.1/C.1](https://arxiv.org/html/2512.23703v1)、[Robo-Dopamine 2.0 §4/附录E](sources/direction_selection_20261003/robodopamine2_v1.html)、[RoboMonitor §V/TableI](sources/system_refresh_20261003/robomonitor_v1.html)。这些数值都是原表/正文复核，不是本轮复现。

## 4. 强反证和发布资源：具体查了哪里

ProgressCompass 已处理 state recall、sequence tracking、recurrence disambiguation，含合法送回。附录B的“satisfied steps stay fixed”只能作为检查边界的理由：同一附录也区分 lasting state、brief interaction 和 observation。历史事件固定可能完全正确；仅据这句话判其在损坏后失效，是未经验证的推论。

| 方法/资源 | 已取得与本轮实际检查 | 仍缺；当前精确原法推理结论 |
|---|---|---|
| RoboMeter | 官方代码revision `352d160389daa964788de1ec933d1925f3a6de4f`；模型入口revision `beef63bc914c5c189329d49c6d712d96d632aa34`；既有OOD元数据、episode ID。固定[eval_server.py](sources/direction_selection_20261003/eval_server.py)对每个前缀用四个linspace索引，返回整体分数。已核官方树的evals及eval_commands路径，未见发布预测结果目录；论文Fig.4/14—16无可复用逐例ID映射。 | 此前定向本机缓存未发现精确权重，本轮未重新扫描或下载；Table6/8当次完整配置和逐例预测缺失。不可声称当前能精确复现。官方四帧路径不等于ProgressCompass附录C的八帧runner。 |
| PRM-as-a-Judge | 本轮官方main仍为`34e8cd4396fe903d6205028da17e32ba01d723d9`；完整[目录快照](sources/native_gap_audit_20261003/prm_current_tree.json)的`eval/results/`仍仅`.gitkeep`。[recorded示例](sources/prm_scope_review_20261003/official/eval/examples/manifest_recorded.jsonl)明确是synthetic smoke，不能当作者实测。[metrics.py](sources/native_gap_audit_20261003/prm_current/eval/prm_judge/metrics.py)算过程曲线指标。 | Table6/8逐例预测和Table8子集ID未见。新增核读[curves.py](sources/native_gap_audit_20261003/prm_current/eval/prm_judge/curves.py)与[cli.py](sources/native_gap_audit_20261003/prm_current/eval/prm_judge/cli.py)：默认居中加权曲线平滑，不能代替C.4因果差分平均的二分类评分器；不是据此宣布论文用了未来帧。 |
| ProgressCompass | 复用当日[项目页快照](sources/system_refresh_20261003/progresscompass_project.html)的Code coming soon；[基准README](sources/baseline_diagnostic_20261003/contextprogress/README.md)明确未含baseline predictions/model outputs；有task/episode/标签/视频。Fig.3(a)合法回撤曲线无episode ID，不能硬绑定本地episode1。 | 本轮实时网页打开失败，故不宣称重新确认“当前仍未发布”；按已核快照无法运行，缺代码、论文组合和精确runner。不是只能等待作者：可继续输入/材料核查，或将来运行另一可用精确强法；不以通用Qwen替代。 |
| R²VLM | **补核到推理入口**：[官方树](sources/native_gap_audit_20261003/r2vlm_tree.json)revision `3b5c09ff1baea40301a790a0c15048df3fc81a5b`；[ALFRED runner](sources/native_gap_audit_20261003/r2vlm/code/script/Alfred/infer_vllm_single.py)读取`question`/`turns[].images`，传递上一轮记录，保存`raw_output/history_cot/model_answer`；[Ego4D示例](sources/native_gap_audit_20261003/r2vlm/code/script/Ego4D/inference_example.py)同类。是本地兼容服务接口，不是必须调用付费API。官方ALFRED RL权重revision `6c84c9bffe680e310ad7fcaaf7016134e0a0608f`。 | 已查树无逐例预测发布目录；示例代码有输出功能不等于作者已公布输出。此前本机无精确权重，ALFRED原图也未取得；单样本runner不能证明Table1全评测/评分配置齐全。迁入机械臂数据需声明域迁移，增加条件真假则属C。 |
| Robo-Dopamine | 官方[固定树](sources/native_gap_audit_20261003/dopamine_tree.json)revision `2c714abca66329f8e2113587226bc9556726f6c2`含`eval/evaluation_grm.py`、`evaluation_api.py`、`examples/inference.py`；无匹配本轮episode的预测文件。PRM README固定Preview revision `980f3d1819c870f62c36169a9486e971049bb09a`。 | Preview与各论文精确checkpoint关系仍不完整，当前未确立精确本机权重。2.0的源参考面板与真实历史权限不同；不能拿离线高VOC证明因果旧条件监测已经解决。 |
| RoboMonitor | 核论文§V、TableI及既有来源快照。 | 未核得可用任务训练权重/runner/逐例预测。当前不训练，不能重建其监督条件后冒称冻结比较。 |

各法对新增逐条件三值请求都不能仅由上述标量/阶段输出自动映射；R²VLM虽然输出步骤状态，也未给每个任意指定关系的校准“未知”契约。资源结论范围限于所列目录、文件和版本，不断言整个互联网不存在。机读[运行缺项单](sources/native_gap_audit_20261003/inference_readiness.json)保留这些区别。

## 5. 实际推进的材料绑定：ep513 被否定为 H-D 正例

下载前写入[范围与纳排规则](sources/native_gap_audit_20261003/scope.json)：保留ep510/513/514全部检查记录，不按未来模型输出筛选；ep513看全19帧，两对照各看预定4帧。沿用有界小批次原则，本批上限6MiB；先HEAD和固定树核大小，实际39个来源文件5,402,835B，其中27张PNG。没有新模型输出。[URL/revision/字节/SHA清单](sources/native_gap_audit_20261003/fetch_manifest.json)

**完整绑定链：**RoboMeter/Robo-Dopamine在RoboPulse++的原生整体进展方向 → [固定JSONL](sources/recovery_search_20261003/RoboPulsePlusPlus.jsonl) `episode_id=513` → `images/ep513/NNN_view1.png` → 作者原始区间`(start_frame,end_frame,reward_label)=(0,10,+1),(10,14,+1),(14,18,−1)`。revision为`abcb94c1e924282c0005e53cff0b22a073de748a`。区间保持原始边界字段，**不继续沿用旧报告未经评分器确认的半开括号**。

任务要求左臂把小瓶放入架子左空槽，再由右臂把试管放入右空槽。对象绑定：左侧短黑盖小瓶；右侧透明杯内长试管；架子上起始已存在的另一根长管是不同对象，不能算第二项完成。任务文字来自作者索引，未取得执行时任务修订历史。

| episode /实际核看 | 单人观察；作者标签保持原样 | 纳排与不确定性 |
|---|---|---|
| ep513，逻辑帧0—18全看；[联系图](sources/native_gap_audit_20261003/ep513_contact_partial.jpg)、[原末帧18](sources/native_gap_audit_20261003/images/ep513/018_view1.png) | f0小瓶在架左；f9—11夹爪撤离后可见已在左槽，f16—18仍在。f12—15右夹爪接近杯内目标试管，末段撤回，试管仍在杯内。作者14—18为整体Falling。 | **排除H-D正例**：未发生可核后续放置成功，也未见第一成果损坏。保留后续未完成/旧成果保持的控制。无监测器逐例预测；不称模型错例。 |
| ep510，f0/5/10/16；[对照联系图](sources/native_gap_audit_20261003/ep510_ep514_contact.jpg) | f16小瓶在左槽，目标试管仍在杯内；作者0—16为Rising。 | 仅稀疏开发核看。原生Rising不证明完整任务/后续步骤成功。 |
| ep514，f0/6/12/19；同上 | f12/19小瓶仍在左槽；末帧目标试管被夹起、接近架子，放开并插入完成无法由所看帧确认。作者0—19为Rising。 | 保留不确定，不把接近槽位或正标签当成功；非已核H-D。 |

**时间与分母边界：**这些是发布逻辑帧坐标，不是已验证的秒或机器人时钟。不能把C.4的1 FPS直接套到每个原视频。ep513下降区间14—18，若按闭区间帧去首尾各二，仅余16；若半开则不剩帧，且差分对齐还可能改变实际范围。这里只作条件算术，不宣布作者的实际有效点数。三条episode是三份开发材料，27帧不算27个任务。

**许可、划分和重复：**RoboPulse++卡为`other`；三例上游物理episode/视频、许可尚未绑定，不能借用ep618/621已核的MIT来覆盖它们。只作本轮公开来源核查；尚未清为原法推理/正式评价输入。作者split为test，本项目已看后均为development；任何后续匹配的上游原轨、另一视角、裁剪与重采样均排除保留测试。机读记录含对象、坐标、原标签、缺项与逐图SHA：[case_registry](sources/native_gap_audit_20261003/case_registry.json)。

原有绑定仍有效：ep621→ViFailback ep2/episode36→LeRobot5197是单人旧绿蓝关系失效，但红块后续失败；ep618→ep1/episode58→5060后续失败、旧关系保持，两例59张发布帧已匹配原视频。ContextProgress place_block_mat/episode1→原episode4是明确合法送回，六段原生进展不应下降。三例都没有对应强法原始预测；未重新包装为新独立证据。[已有三例登记](sources/baseline_diagnostic_20261003/case_registry.json)、[上游映射](sources/recovery_search_20261003/upstream_trace/source_mapping.json)

## 6. 两张缺口卡：只保留待检 B，不立已证实主缺口

### B1：较长正常推进后，短时可见的旧终局关系撤销被漏作原生下降

- **原生任务/输出：**仍是整体进展方向；只纳入作者标Falling、任务要求保留旧结果、实际原法输入有充分可见证据的区间。不要求原法额外输出旧关系真假。
- **为何重要：**有成果先达成时，整轨终态标签不能显示回退发生的时间；短暂回退还可能被采样/方向平滑漏掉。这是诊断假说，不是已证实机制。
- **已覆盖/低分：**PRM C.5.2已经覆盖一般子目标撤销，Table6仅证明A层下降错误。B1可能剩余的只是具体时长、可见性与任务语义组合；不能把“识别撤销”本身当创新。
- **可绑定材料：**ep621原生下降22—28及原视频，单人可见失效锚；ep618和本轮ep513提供旧成果保持控制，但两者整体也可下降，不能期待不同原生答案。合法撤回使用place_block_mat。当前没有合格修复例，明确缺项。
- **强反证：**RoboMeter Table8 Falling .901、其Fig.4正确处理掉落；R²VLM可更新完成状态，Robo-Dopamine2.0已研究历史/恢复。
- **未知：**ep621在论文当次输入中是否捕获了必要前态与后态，是否属于Table8，方向参考和端点掩码，任何精确强法在此处的输出。
- **最便宜否定：**先审四帧采样是否实际包含充分前后证据；没有则收窄为输入采样问题。若有且精确强法正确报下降，则该开发例不支持剩余缺口；若唯一错误只是新增逐条件输出，则撤销B归类。即使一例错也不证明子类错误率或机制。
- **证据强度：**现象/材料较强，强法目标子类错误为零条；只适合作为优先否定的诊断入口。

### B2 / H-D：后续步骤成功，同时破坏最终仍须保持的旧成果

- **原生任务/输出：**必须先确认该事件对应作者原生整体方向标签；新增成功与损坏若净效应/权重未定义，不能先规定Falling。逐条件状态另列C。
- **为何重要：**新正向证据可能掩盖旧损坏，是可检验的有选择解释，不能先设为题目答案。
- **已覆盖/低分：**已有研究覆盖一般撤销、历史与恢复，但未核到单列H-D的成绩。没有低分或作者案例能特指H-D。
- **可绑定材料：**当前无已核正例。ep621第二步骤失败；本轮ep513第二步骤未完成且旧成果保持；ep510/514也不提供已核正例。全部保留排除/未知记录。
- **强反证：**状态修订强法、Table8高分、ProgressCompass的lasting/event区分；整体标量不必与某一旧关系一一对应。
- **未知与最便宜否定：**先取得一个原任务/原标签下的真实正例，若后续并未成功、旧成果合法撤回、损坏不可见或原生目标不要求降分，立即排除；若精确强法正确处理，停止该实例的不足故事。
- **证据强度：**比B1弱；目前连合格正例和原生评分映射都没有。不能优先于已有可核材料。

不设第三张“缺上下文/合法回撤”卡：这是ProgressCompass已直接研究的A层问题，目前没有证据表明其强解法仍在我们指定的细分情形犯错。也不把遮挡未知单独包装成B；强制三值弃答通常属于C。

**选择：还不能选定一个新的研究主缺口。**若仅安排下一步低成本核查，B1先于H-D，因为有原视频和失效锚；这只是材料/输入诊断优先级，不是创新选题或架构批准。

## 7. 下一件可执行动作与停止条件

**只做一次本地源文件核查：为ep621原生下降区间22—28，按固定RoboMeter服务端四帧采样代码枚举每个查询时刻的实际输入坐标，并与既有上游帧匹配及失效锚对应。**同时列ep618同任务保持锚，判断先前关系成立/后续失效的证据是否真能同时进入输入。所有所需源码、帧映射、原视频都已在本地；不需要模型、下载或付费。

输出应为“原生查询索引—客户端帧序列—服务端四索引—原视频坐标—可见/遮挡/未采到”的一张表。须先核客户端的采样与帧序列，不直接把原PNG序号当1秒；四帧可用性也不能冒称Table8论文配置已复现。若缺抽帧时钟或C.4有效点掩码，保留两种可能，不事后选有利者。必要证据未被输入保留时，优先否定“推理/记忆机制不足”的解释。

将来若进行少量原法诊断，再完整读07协议、08、config_stage7并核精确权重/资源，先冻结纳排、作者目标、输入权限、输出映射、接口失败与成本记录。保留正确、错误、未知、非法输出；包含失效、保持、合法撤回、遮挡，并明确修复材料缺失。没有合法精确原法条件就停在输入清单；不恢复普通Qwen试错。没有独立复核不做H1、BCY、显著性或正式规模。

## 8. 本轮交付与最终证据判断

已保存本报告、39件小来源、三例材料登记、输入缺项单与分母审计；新增数据事实才追加data_manifest，旧版本和旧事实保留。仅追加D069—D071及status入口，不修改run_ledger、08、07协议或配置。来源SHA、PNG与固定HF LFS哈希、JSON、报告本地链接及旧文件保留检查见[validation.json](sources/native_gap_audit_20261003/validation.json)。这些文件核验不是独立标注。

目前得到的是**已知普遍难点A，加两个尚待否定的同任务窄假说B**。没有强方法在这两个精确子类上出错的逐例证据；汇总Falling错误不承担这个证明。强法正确处理、原生标签/目标并不要求预期输出、采样/遮挡/语义足以解释差异、或问题只出现在新增C输出，都会推翻或显著收窄候选。**现阶段没有足够依据开始设计改进架构。**
