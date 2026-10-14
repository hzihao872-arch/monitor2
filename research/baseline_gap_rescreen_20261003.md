# 新基底复筛：停止 VLAC-Cut 重合切口，条件转向 RynnValue

核查日期：2026-10-03。按用户最新取舍，停止把时间投入“VLAC-Cut 错误物体进展误判是否已被 ARS 修复”的同例实验。沿用 [研究流程](../PROGRESS_MONITOR_RESEARCH_WORKFLOW.md)，本轮只做文献、官方材料和源码核查，没有模型推理、策略训练或机器人实验。

## 1. 决策

**建议更换主候选：RynnValue 优先，DenseReward 第二；VLAC-Cut 降为参考基线。** RynnValue 的理由是作者已报告一种具体的使用失败：进展驱动的数据筛选提高了四任务平均成绩，却让抽屉任务的策略成功率从 40% 降至 0%。这足以提出诊断方向，但还不能宣布发现评价器的新错误类型，更不能宣布已有免训练解法。

下一步只值得做有界的错误链追查：原始帧 → 原生分数 → 筛选决定 → 被删片段的作用。**不直接设计补看/验证架构，不直接复现完整策略训练。** 若最终仍只是视觉完成判断不准，或无法取得足以区分解释的材料，就降低此切口优先级。

## 2. VLAC-Cut：查过其他入口后，仍不值得强行保留

| 入口 | 原生证据与限制 | 取舍 |
|---|---|---|
| 终态失败判断 | Table 2 的失败 F1 为 61.02%，成功 F1 为 90.17%，TSA 为 84.30%；F1 不是漏检率，代码默认 90 分阈值也不是物理成功定义 | 有剩余错误，但容易回到已停止的完成判断路线 |
| 停滞/中性段与切分 | 切片确实是原生用途；本轮未找到足够明确的错切对齐案例或专门边界统计 | 评价缺项不等于已经证明系统失败 |
| 百分比任务计划依赖 | 已核展示 task_description 内含步骤及百分比；缺少计划消融不能证明依赖导致错误 | 不将输入假设包装成新缺口 |
| 短时边界、采样与插值 | 已配对洋葱例在原始预测点上也有反向变化；它不能自动提供另一类独立错误 | 不重复包装同一个错误物体案例 |
| 在线延迟 | 离线用途与在线输入预算不同 | 新增服务要求不能倒推原生方法失败 |

具体来源和历史 GT 配对见 [ARS 覆盖审计](vlac_ars_coverage_audit_20261003.md)、[首轮基底报告](new_baseline_search_20261003.md)。结论是研究投入取舍，不是证明 VLAC-Cut 没有其他缺陷；也不是证明 ARS 已解决该例。

## 3. 新候选比较

| 候选 | 日期、能力及开放情况 | 本轮结论 |
|---|---|---|
| **RynnValue** | arXiv v1 2026-08-10；HF 模型仓库创建 07-27，不能称 08-10 才首次出现。视频＋指令产生剩余时间与语言分析，用于跨域排序、奖励和数据筛选。代码、4B/8B 权重入口、评估和策略端代码可见 | **主候选，版本和数据可得性有条件**；有明确任务级筛选负收益 |
| **DenseReward** | arXiv v1 07-14；HF 权重仓库创建 08-06、最后更新 08-07，数据 08-27。4B，一帧/三帧，输出进展及错误类别；覆盖真实与仿真来源 | **第二候选**；真实来源误差明显，但尚缺逐例原生预测 |
| Robo-Dopamine 2.0 | arXiv v1 08-16；多场景/时序评价强。已见官方旧 preview 8B/4B 分别在 03-05/04-05 发布，不能自动等同 8 月版本 | 需目标参考与版本绑定；不排在前两名之前 |
| AnyviewMeter | arXiv v1 09-17；针对视角变化，使用相机几何并做任务适配 | 更适合作为视角问题的训练型比较，不优先作为零样本宽基底 |
| HiRE | arXiv v1 09-22；用成功/失败交互历史修正基础表征奖励 | 是重要免训练查重对象，但依赖带结果的交互历史，不是同输入条件的新基底 |

论文一手来源：[RynnValue](https://arxiv.org/abs/2608.09853)、[DenseReward](https://arxiv.org/abs/2607.13033)、[Robo-Dopamine 2.0](https://arxiv.org/abs/2608.15680)、[AnyviewMeter](https://arxiv.org/abs/2609.20106)、[HiRE](https://arxiv.org/abs/2609.27068)。本轮前三篇所取 arXiv metadata 仅列 v1；后两篇读 v1，未完成其全部发布历史核对。ProcVLM、RoboMonitor、FIERCE 维持首轮判断，不重复扩展。

## 4. RynnValue：真正值得追的现象，以及不能越过的结论

### 原生现象

固定官方仓库 commit `353a3caa732107aff374ef410069a78c4b830d6d`，README 的 Filter-BC 表报告：

| 任务 | 不筛选的多任务 SFT | 进展筛选后 BC |
|---|---:|---:|
| 面包放篮 | 30% | 70% |
| 铲牛排 | 70% | 75% |
| 双臂传盒 | 0% | 25% |
| 盒子放入抽屉 | 40% | 0% |
| 平均 | 35% | 42.5% |

作者说明两组使用相同初始化、来源数据和优化流程。不能只摘抽屉负例：三个任务改善，平均也改善。作者将下降推测为视觉歧义导致有用片段被当成无进展而丢弃；这仍是解释，不是已发布逐帧因果证据。[官方固定版本结果](https://github.com/alibaba-damo-academy/RynnValue/blob/353a3caa732107aff374ef410069a78c4b830d6d/README.md#filter-bc-progress-filtered-fine-tuning)

**这些数是策略成功率，不是监测器准确率。** 不能说“抽屉进展判断准确率为零”，不能从零成功推断该任务训练帧全被删除。Filter-BC 表未明确单列试验分母、随机种子和置信区间；相邻 RL 段的 20 trials 不自动移植到此表。论文其他 RL 表的抽屉高成功率属于不同训练设置，不能与此多任务 SFT 对照混用。

### 已核代码把疑问落到了哪个环节

`progress_advantage.py` 从 LeRobot parquet 读取 `progress`，计算相邻增量及有限窗口折扣和：`A_t = sum(lambda^k * (p[t+k+1]-p[t+k]))`，尾部补零，仅保留 `A_t > threshold` 的起始帧。指定实验配置使用 zero 阈值、lambda=0.98，窗口继承默认 50；策略 action_horizon=16，两者不是一个参数。源码已有 mean/median/quantile、窗口和折扣配置，不能把调阈值或加长窗口直接当新方法。[筛选代码](https://github.com/alibaba-damo-academy/RynnValue/blob/353a3caa732107aff374ef410069a78c4b830d6d/pi-rl/src/openpi/training/progress_advantage.py)、[配置](https://github.com/alibaba-damo-academy/RynnValue/blob/353a3caa732107aff374ef410069a78c4b830d6d/pi-rl/src/openpi/training/config.py)

该入口读的是已标注的 progress；本轮尚未把真实实验的“剩余时间 → progress”转换、采样率与输入窗口绑定到具体 dump。评估适配器虽有归一化模式，不能据此断言筛选数据就是那样产生。默认数据路径是 `/path/to/franka_lerobot_data/...`，并非可下载的数据集 ID。

可区分的竞争解释：

1. 分数确实错了，有用片段被低估；必须有画面、标签、原生输出对齐才能判定。
2. 分数在它原本定义下合理，但短窗口变化不足以衡量某段动作的训练价值，例如准备、保持或恢复行为。这是候选解释，尚未找到真实对应片段。
3. 各任务保留率变化，导致多任务训练分布偏移；也可能涉及采样、归一化或训练方差。先排查这些更便宜的解释。

本轮查阅完整 GitHub 树（686 个条目、未截断）及筛选入口，尚未找到该表对应的逐帧白名单、四任务保留率和绑定预测 dump。仓库里的演示视频不自动等于失败实验轨迹；Robometer 子目录中的原模型输出不能冒充 RynnValue 输出。

### 新旧版本的实质风险

论文 v1/HF 卡对应的 8B 排序 Kendall tau_a 为 0.675；最新 GitHub README 报 0.704，并描述 quantile tokenizer 和因果推理注意力。**实际下载核对的两个 HF config 仍是 symlog**，绝对支持上限 512 秒、相对支持 ±256 秒；8B config 仍记录隔离注意力。故不能宣称下载当前 HF 权重就复现了最新表，更不能默默改 tokenizer 后沿用原权重。

- 4B HF revision：`3f73b5d2b5e53b21f248c8791004dde6a8cf2b92`。
- 8B HF revision：`8738c5e4ce4418ea0266e9fbeffae0eb9bbb230e`。
- 两者 API 最后修改日期为 08-11；4B 卡也仍描述旧版指标。最新 Filter-BC 表所用 checkpoint 尚未绑定。

[4B config](https://huggingface.co/Alibaba-DAMO-Academy/RynnValue-4B/blob/3f73b5d2b5e53b21f248c8791004dde6a8cf2b92/config.json)、[8B config](https://huggingface.co/Alibaba-DAMO-Academy/RynnValue-8B/blob/8738c5e4ce4418ea0266e9fbeffae0eb9bbb230e/config.json)。HF API 参数总量约 5.14B/9.57B，模型名中的 4B/8B 不能直接当显存预算；本地 8GB GPU 不据此承诺直接运行。

## 5. 查重：保留的是诊断价值，不是已确认新颖性

| 方法/现有能力 | 已覆盖内容 | 对下一步的约束 |
|---|---|---|
| ARS §3.7 | 以局部进展决定 action chunk 是否用于策略训练，前端有主动取证与验证 | “更准确地打分然后筛选”高度重合；不再重启通用补看/验证方案 |
| WARP-RM / WARP-BC | 学习相对进展速度；重叠窗口汇总，用片段终点速度筛选和加权；比较不同保留预算 | 差分、局部窗口、相对时间及重加权已有先例，需检查是否只是同机制改名 |
| HiRE | 无额外网络训练，借成功/失败历史校正奖励陷阱 | 有结果标签的回看校准不是空白；若依赖这些信息，不能仍称无目标反馈 |
| RynnValue 自身 | 已有相对时间头、多种阈值，以及最新仓库中的推理注意力对比 | 这些不能再次作为“我们新增的架构”；相对时间头也不是独立物理进展真值 |

一手来源：[ARS](https://arxiv.org/html/2609.34484v1)、[WARP-RM](https://arxiv.org/html/2606.28320v1)、[HiRE](https://arxiv.org/html/2609.27068v1)。检索包括 RynnValue 后续/免训练、progress filtering、relative progress、recovery actions、hindsight reward calibration；本次未找到可核实的“已修好 RynnValue 这一抽屉表格失败”的直接结果，不代表领域没有相关解法。

免训练约束指冻结评价模型及其改进机制；原文 Filter-BC 本身仍训练策略。若将来要声称提高机器人成功率，最终必须有相应策略验证，不能用离线曲线改进替代。本轮不启动这项昂贵验证。

## 6. DenseReward：为何列第二

论文 Table 1 总体 MAE 为 0.081，DROID 为 0.259，Isaac/RoboSuite/LIBERO 分别为 0.081/0.051/0.044；DROID 上仍优于表中其他方法，不能解读成全面落后。DROID 已在训练来源中，不能称纯零样本 sim-to-real 失败。[论文](https://arxiv.org/html/2607.13033v1)

本轮完整读取公开三帧测试 JSON 的 28,032 行，仅做元数据统计：

| 来源 | 帧样本数 | 占比 | 文件名归组 episode 数 |
|---|---:|---:|---:|
| DROID | 2,524 | 9.00% | 149 |
| Isaac | 11,114 | 39.65% | 254 |
| RoboSuite | 11,640 | 41.52% | 464 |
| LIBERO | 2,754 | 9.82% | 91 |

用这些行数加权论文四舍五入后的来源 MAE，得到 0.080935，与总体 0.081 算术相容；来源宏平均是 0.10875。**这是公开数字与样本权重的核对，不是重新运行模型得到的 MAE，也未证明此 release 就是原表使用的精确 split。** DROID 的较大误差值得诊断，但“整体成绩掩盖困难来源”本身不是免训练架构贡献。

复现限制：官方 GitHub repository metadata 显示 size=0，tree 接口返回 409 empty repository；HF 权重、提示词、配置和测试标签可读，不能说代码已完整发布。公开 split manifest 共 19,171 episodes，与论文 26,579 的口径不同，主要差异在 Isaac。17 条 DROID 标签高于 1、最高 1.070；这种少量格式异常不能拿来解释全部 0.259 误差。Figure 3 已查看，但无配套 GT 曲线，不能凭曲线外观制造逐例误判。

可复算脚本及结果：[audit_dense_metadata.py](sources/baseline_gap_rescreen_20261003/audit_dense_metadata.py)、[dense_metadata_audit.json](sources/baseline_gap_rescreen_20261003/dense_metadata_audit.json)。[官方模型](https://huggingface.co/densereward/densereward-3frame)、[代码仓库](https://github.com/dense-reward/dense-reward)。

## 7. 后续投入边界

RynnValue 只进入“小规模诊断候选”，不立即立项开发。优先绑定 Filter-BC 对应模型版本、标分数据与筛选输出；随后看四任务保留率，追少量被删片段，同时保留改善任务作对照。一个任务零成功不够推出普遍机制。

若拿得到输出，先区分评分错误、窗口/片段用途不匹配、任务配比变化；比较同保留量随机筛选、原有阈值选项、任务均衡等简单解释，再判断是否值得提出架构。若只能在作者未公开的大规模实机训练中寻找证据，暂缓这个切口；转向 DenseReward 的真实数据逐例诊断，不为保住基底无限补实验。

本轮交付达到：换基底建议、原生问题入口、源码定位、重合核查、复现风险。尚未达到：确定错因、确认方法新颖性、完成新模型复现。

## 8. 证据保存

所有新来源保存在 `research/sources/baseline_gap_rescreen_20261003/`；[fetch_manifest.json](sources/baseline_gap_rescreen_20261003/fetch_manifest.json) 保存请求 URL、UTC 时间、字节数和 SHA256。GitHub tree/API 响应另存本目录。小型来源与标签共约 18 MB，未下载模型权重、整库视频或执行不受信任远端模型代码。历史报告和旧实验台账不变，状态入口另作追加式更新。
