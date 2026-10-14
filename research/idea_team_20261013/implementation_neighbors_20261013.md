# 主B实现近邻深读：Aff-Grasp、ConditionNET、RT-Affordance

2026-10-13。一手论文、作者项目页、作者源码只读核查；未运行提取脚本、模型、训练或仿真。本文件不改写旧提案。

## 独立判断

**主B宽泛的实现骨架已经有充分先例，不能作为新的方法卖点。** 后来的交互产生早先图像监督，冻结预训练视觉表征训练小头，条件不再满足时停止/恢复，这些均已有。Aff-Grasp 加 ConditionNET，再配普通轨迹结束后增量训练，已经实质覆盖这个宽泛组合；增量训练本身也不是新机制。

更具体的B仍能实施，但当前额外内容主要是条件语义和监督合同：哪种真实后效支持哪种通行/承载命题、哪些区间允许标注、何时只让证据失效而不判条件为假、什么时候任务已完成而无需保持条件。不能仅凭相关论文没有完全使用这些词，就说有强新颖性。若只用人写有效期规则再训练分类器，很可能是一项数据设计与评测工作，尚非新的学习算法。

## Aff-Grasp：已实现从后来接触到早先图像

一手来源：[论文3.1–3.3](https://arxiv.org/html/2408.10123v2#S3)、[作者仓库](https://github.com/Reagan1311/Aff-Grasp)、[作者页](https://www.genli.top/affgrasp/)。源码固定核查commit：`ae12143e27de0ec9c4c26f5920b7e307ecfdbf32`。

论文的标签是抓取部位和功能部位的像素mask。后期真实使用提供接触点，映射到遮挡较少的pre-contact图，再由SAM扩大为mask。部署GAT读取单图预测部位，不读取同一次执行的后期片段。它不是任务进度或承载稳定评价器；训练侧与部署侧信息不同并非B独有。

源码管线可以具体借：

1. [`1_obs_frame_loc.py`](https://github.com/Reagan1311/Aff-Grasp/blob/ae12143e27de0ec9c4c26f5920b7e307ecfdbf32/ego2aff/epic-kitchen/1_obs_frame_loc.py)读取EPIC action CSV的start frame、手物检测文件。围绕动作起点，倒找NO_CONTACT、目标存在且遮挡较少的一帧；用bbox尺寸、IoU、距离筛选。
2. [`2_obs_pts_loc.py`](https://github.com/Reagan1311/Aff-Grasp/blob/ae12143e27de0ec9c4c26f5920b7e307ecfdbf32/ego2aff/epic-kitchen/2_obs_pts_loc.py)由手mask和物体box交叠提点，SURF+homography回投到该早帧，投出物体mask的点snap到mask。随后选择其他提示点。
3. [`4_fun_pts_loc.py`](https://github.com/Reagan1311/Aff-Grasp/blob/ae12143e27de0ec9c4c26f5920b7e307ecfdbf32/ego2aff/epic-kitchen/4_fun_pts_loc.py)从动作叙述和工具/功能字典定位工具使用片段，取接近目标的工具内部点；[`affordance_util.py`](https://github.com/Reagan1311/Aff-Grasp/blob/ae12143e27de0ec9c4c26f5920b7e307ecfdbf32/ego2aff/preprocess/affordance_util.py)有DINO/FeatUp correspondence utilities。不能假定所有functional点都来自可靠实际使用；论文明确没有对应动作时用离抓取点较远的位置作启发式。
4. [`3_point2seg.py`](https://github.com/Reagan1311/Aff-Grasp/blob/ae12143e27de0ec9c4c26f5920b7e307ecfdbf32/ego2aff/epic-kitchen/3_point2seg.py)把抓取与功能点分别作为SAM正负提示，生成两种mask，保存裁剪图与编码mask。

因此论文所说无需新的人工mask，不等于完全没有人工信息：action narration和timestamps、预先存在的object–affordance关系、预训练检测/分割器都参与标签管线。SAM产物与实际功能点仍是伪标签，不是独立物理成功合同。

[`ego_video_data.py`](https://github.com/Reagan1311/Aff-Grasp/blob/ae12143e27de0ec9c4c26f5920b7e307ecfdbf32/affordance-learning/data/ego_video_data.py)按文件名noun及手写`AFF2OBJ_dict`把128/255像素值转换为grasp/functional classes。这里`support`对应spatula、shovel、trowel的功能部位；不能读成“指定平台经释放后稳定承载”的监督。

[`GAT.py`](https://github.com/Reagan1311/Aff-Grasp/blob/ae12143e27de0ec9c4c26f5920b7e307ecfdbf32/affordance-learning/models/GAT.py)使用DINOv2、qkv LoRA、embedder、depth分支和类别prototype，focal/dice mask loss。更新这些模块而冻结其余视觉参数已经是现成做法。论文允许depth injector仅训练使用；实际代码需要检查所选训练/推理配置，不能无条件宣称所有发布模型推理时都不用depth。

复用限制：提取README仍TODO，脚本含本地默认路径、各模型依赖和交互显示。源码可借算法步骤，但不是一条已验证的开箱流水线。用它找2D接触部位，也不能直接得到入口净空、载荷和稳定真值；homography回投点不证明功能在整段环境变化里一直有效。

## ConditionNET：已实现前提/后效学习及失效监控

一手来源：[论文III-A–F、IV-A](https://arxiv.org/html/2502.01167v1#S3)、[作者项目页](https://dsliwowski1.github.io/ConditionNET_page/)。官方页链接数据，未链接模型代码；本轮检查作者公开仓库列表未找到论文实现。因此下述是论文实现规格，不是假称已读实际dataloader。

训练由人工标注动作名、成功/失败、pre/core/post区间及异常。把同一次示范的prep帧与post帧作所有组合的三元组；按已知逆动作关系把某动作post作为另一动作pre。冻结DINOv2与CLIP，训练State Transformer、action-conditioned Condition Transformer和三分类头。除了分类损失，还使post/pre特征差与动作语言对齐，后者只使用成功示范。

部署输入是当前单帧及当前动作，输出precondition/effect/unsatisfied。行为树给期望阶段；pre和effect阶段比较期望与预测，core阶段暂停异常监控，连续8帧异常才触发。官方例子明确存在effect退回unsatisfied和重试恢复。因此“条件撤销”“机器人策略不同时训练”“实时小condition模型”均不能作为B的新能力。

但其人工阶段标签不是独立物理条件证书；没有以局部接触/承载后果审核合法回推区间的完整机制，也未见部署后更新Monitor权重的实验。不能从缺这项描述推出新颖性，只能据此定义比较：以同人工预算，B物理证书是否比阶段监督有用？

## RT-Affordance：另一个确切的hindsight训练先例

用户检索到的OpenReview `s8VMLXKH1X` 是匿名稿题名《RT-Affordance: Reasoning about Robotic Manipulation with Affordances》。可读实名版本是 [2411.02704v1](https://arxiv.org/html/2411.02704v1#S3)，《RT-Affordance: Affordances are Versatile Intermediate Representations for Robot Manipulation》，作者页：[RT-Affordance](https://snasiriany.me/rt-affordance)。

轨迹含image、action、end-effector pose、gripper state。夹爪开闭transition和终局时刻抽出关键pose，再根据相机标定投到图像构成hindsight affordance plan。训练initial image+language→plan的生成器，同时训练plan-conditioned policy；部署无须读取真实未来。计划是实际pose，不是成功认证的条件真值，也没有区间有效期/撤销监督。

IV-A确认PaLM-E2 1B、RT-1+MOO+新增机器人轨迹、RT-2 web data，以及约750张额外人工affordance图片，作者报告采集约1小时、标注约2小时。这只是额外域内数据预算，不是整个训练只用750张图，也不是保持未适配的原policy不动。IV-E表明web data与额外图片都重要。因此它既是“后期轨迹产生早期学习标签”的强先例，也是不能藏强控制器和底层训练成本的提醒。

## 我们仍须新增什么，怎样具体实现

下面是B可以做的实现设计，不是已经写好的代码或论文证明。

1. **条件合同**：先手写一个object-scale通行查询和一个指定载荷/区域承载查询。证书记录`trajectory_id, event_time, object_id, part_id, query_context, label, valid_interval, independent_source, reviewer`；再单独记录该条件当前是否仍需满足。
2. **独立锚点**：用已有逐帧sim_states与接触/释放/稳定合同，先得到受控仿真真值。真实视频需独立审核或触觉/接触日志，不能用SAM mask或VLM自评冒充物理证书。
3. **监督mask**：只有能独立确认相关变量不变的小区间允许传播。未知区间mask掉；旧证据失效不等于负标签。负例要独立封堵或无合格支撑等反证。目标完成用独立合同解除义务。
4. **前缀学生**：借ConditionNET的冻结视觉/语言表征加condition模块，或复用现有Qwen表征；以mask监督条件成立与必要性阶段。最简单版本可先用当前帧，并与完整前缀版本比较，不能预先保证历史模块有用。每张证书计权一次，按源轨迹划分。
5. **部署及更新**：在线仅读前缀；轨迹结束后新证书进入审核池，更新条件模块并回放旧证据。记录更新前对新片段的预测。已有固定技能存在后，条件检查仅排除缺条件的动作，不把一项环境条件成立等同完整技能获准。

这些新增项里，关键难处仍是有效范围审核和真实反馈的独立性。Aff-Grasp帮我们借标签提取/回投，ConditionNET帮我们借条件学习与监控；它们不能替我们免费给出承载或通行证书。即使工程可闭合，仍需证明同人审分钟优于直接挑状态纠错和证书检索，才说明B的额外设计值得做。

**据当前证据，应把B称为可实施的研究假说或数据/监督设计；不应称为已辨认出强新颖性的主方法。** 此判断允许后续换idea，不要求维护旧推荐。
