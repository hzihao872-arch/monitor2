# B 机制强近邻复核：别人有没有做过，怎样实现

日期：2026-10-13。仅一手论文正文与官方代码只读核查；没有训练、评测、下载模型或数据。沿用 nature-academic-search 的多源发现、一手核验流程；Undermind 用于候选发现，技术判断以链接正文为准。本文是新文件，不替换旧报告。

## 判断

**有人已经做过 B 的通用核心，并且有完整系统与代码：实际交互产生监督，将晚到的局部后果配回较早视觉观察，再更新视觉预测器供未来决策。WVN 是最有决定性的旧先例。** 将它概括为“低标签、后视监督、冻结视觉、小头在线进化”不能支持新的方法主张。TACIT 则直接覆盖少量操作示范中的“未来真实接触监督前面的视觉帧”。

这不等于已经找到“任意物体准备条件的严格三值证书、可证明有效区间、条件撤销”完整同构工作。本轮未找到该完整方案；这个有限检索结果不能证明其新颖。若剩余实现只是人工确认部件不变后广播标签，它更像监督构造/标注预算研究，必须同预算比较直接状态纠错、事件帧学习、几何或人工 oracle。不能先宣称新学习范式。

## 1. WVN：最强完整先例，且可读实现

[Wild Visual Navigation 正文，§3.3–3.5、§5.1–5.2](https://arxiv.org/html/2404.07110v1) 是 RSS 2023 系统的扩展。机器人当前速度与命令之差经 Kalman 平滑及 sigmoid 得连续通行分；短程监督图保存足迹，投影到较早相机视角的 mission nodes，为视觉分块生成标签。冻结 DINO/STEGO 特征，小型共享 MLP 回归通行分并重建特征，在线更新；示范启动约数分钟，论文报告低于五分钟。无需逐像素人工标签，但要真实机器人、位姿与速度遥测。

未走区域目标设零，按重建置信度加权负例损失：像已走样本的未知区域可不贡献。它并非严格 true/false/unknown 逻辑；没有证明动态部件在回溯区间不变。新体验能覆盖旧未知保守判断，不能等同“条件改变时撤销旧真标签”。视觉估计接入导航，底层 locomotion controller 不由此训练。

### 官方代码核验

[官方仓库](https://github.com/leggedrobotics/wild_visual_navigation) 有实际 Python/ROS 实现与示例入口，非空仓库。本轮核读：

- [supervision_generator.py](https://github.com/leggedrobotics/wild_visual_navigation/blob/main/wild_visual_navigation/supervision_generator/supervision_generator.py)：`update_velocity_tracking` 实做速度误差、Kalman、sigmoid。
- [traversability_estimator.py](https://github.com/leggedrobotics/wild_visual_navigation/blob/main/wild_visual_navigation/traversability_estimator/traversability_estimator.py)：`add_supervision_node` 筛有效监督节点，world footprint 投到附近 mission camera，通过 `torch.fmin` 合并监督掩码；`make_batch` 与训练、checkpoint 代码可读。
- [loss.py](https://github.com/leggedrobotics/wild_visual_navigation/blob/main/wild_visual_navigation/utils/loss.py)：`graph.y_valid` 分已标/未标项，未标损失乘 `1-confidence`，重建损失只用已标数据。

这确认实现入口，而非确认仓库可在本地直接运行；未安装依赖或执行代码。可借用图像—体验关联、分离更新与推断的实现。已有示例/权重不等于我们已有能用于部件条件监督的传感数据。

## 2. TACIT：未来接触给前视觉帧的 masked teacher

[TACIT 正文，§III-A/B、§IV-A/C](https://arxiv.org/html/2609.24507v1)。触觉 taxel 阈值、去抖和事件合并得到接触起点；初始有效帧给接触中心，经指尖运动学和标定变到共享坐标。前帧选择最近未来事件，以该点为中心给相机点云 Gaussian 标签；仅保留提前 0.25–6 秒且几何支持达阈值的帧。没有事件就不造 target，而非负标签。BCE 教空间 attention，输出汇入 diffusion policy。

真实任务各十条示范，球/peg 共检测十二/二十七接触事件，依赖真实触觉、RGB-D、运动学标定；不是十个人工标签。监督空间关注点，不是准备条件真假；未证明对象不变或证书撤销。策略也训练，推断仍输入触觉，因此不是冻结机器人 monitor。论文中未发现代码/数据公开链接，定向检索亦未核实官方仓库，不作为现成可复用数据。正文报告 pre-contact 与 contact-time 监督无一致优劣，不能先假定回溯一定有收益。

## 3. Experience-Driven Terrain：冻结小头持续更新亦已有

[Experience-Driven Continual Learning 正文，§III-B–E、§IV-A](https://arxiv.org/html/2609.39755v1)。完整 touchdown→liftoff 后得到滑移、法向力、牵引指标、能耗、加载率及置信度；将结果配给触地前最近、五秒内、同五厘米格的视觉 descriptor，避免未来视觉泄漏。冻结 DINOv3，置信加权 evidential MLP 输出五属性及 uncertainty；缺测置信零，低可靠接触拒收，未观察 map 格保留 unknown。

五十个近期训练样本及十个 held-out 才启动更新，bounded replay 配独立历史验证门，候选通过才替换预测器。需 offline-trained 初始 checkpoint；连续适应对比用记录的硬件 contact stream，闭环导航独立在仿真评测。**不是现实从零少量接触在线进化已被完整验证。** 连续物理目标不是条件三值标签，五秒关联也不是动态部件不变证明。标准 Go2 控制器、RGB-D、关节遥测与标定均必要；未核实公开官方代码/数据入口。

## 4. Relational Preconditions：后果监督关系表征，条件真值另标

[Relational Learning for Skill Preconditions 正文，§3.1–3.3及附录](https://arxiv.org/html/2012.01693v1)。约十万模拟对象对，用虚拟 spring-damper robot 做局部扰动，记录位移、旋转、接触。相同扰动下效果相似/不同构造 triplet 正负对，并回归 effects；3D voxel ResNet 学关系 embedding。其“正负”是关系相似度，不能当条件可执行/不可执行。

随后冻结关系模型，训练 RN/GNN 预测真实场景 skill preconditions；下游仍依赖有标签场景，多视角几何重建，unstacking 支撑重要性有人工标注。没有晚到事件向历史区间传播，也没有三值 unknown 或撤销机制。应作为 effects-supervised representation + 少量条件分类基线。[作者入口](https://mohitsharma0690.github.io/) 可定位论文；本轮未核实该论文专属官方完整代码/数据，不能把邻近论文代码算成它的实现。

## 5. AffordTrajDP：此前被高估的近邻，实际是向前几何传播

[AffordTrajDP 正文，§3.3–3.5、§4.1](https://arxiv.org/html/2608.01603v1)。GroundedSAM 裁对象、CLIP 在同任务记忆中取已知 contact，经 dense correspondence 转到目标 RGB-D 点。Any6D/ FoundationPose 得对象位姿示范，模型预测未来 SE(3)，contact 随未来位姿传播，作为 diffusion policy 条件；仿真每任务三十或五十示范。

“动态”指 contact 坐标随对象未来运动更新，**不是**真实后果回头赋予前状态条件标签；训练执行策略，不是在线更新 condition monitor。没有 true/false/unknown、有效区间证书或部件变化撤销。本文未交代可直接复用的 outcome-certified condition 数据；未核实官方公开代码。它提供对象坐标对齐思路，但不应列成 B 完整先例。

## 对 B 的最终处置

可实施链条“后果→前图→小预测器→决策”已经成立，而且 WVN 代码可供方法理解。因此不能再以它为核心宣布聪明的新 idea。操作领域直接的 TACIT 和冻结头持续学习的 Terrain 工作进一步压缩空间。真正尚需论证的是：特定载荷/对象/路径下的局部证据究竟能覆盖哪些前帧、部件变化何时使标签失效、unknown 如何避免错误负标，以及这套更严格规则在同人工分钟预算下能否胜过直接纠错。没有相应事件/变化数据与定量优势证据，当前只能称待验证的监督设计研究，不是已确认的新方法。

本次只做机制核查，不执行该方案；也没有把传感 metadata、仓库存在、论文实验用数据当成本地已具备的数据。
