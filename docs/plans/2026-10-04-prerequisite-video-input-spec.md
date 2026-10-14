# 第一批隐含前置动作视频与模型输入规格

日期：2026-10-04。状态：**六类视频、实际模型输入帧、仿真真值与 TOPReward 原版六段评分已完成；Robometer 严格原版因 dtype 错误尚无结果，PR #33 兼容版六段评分已完成。** 本文保留预定规格，数值与限制见[实际报告](../../reports/prerequisite_probe_phase1_20261004.md)。窄口模板因主相机看不到蓝块而在模型输出前淘汰；按本文预定规则改用单格绿色托盘备选场景。

执行记录（2026-10-04）：[30 FPS 母版](../../experiments/prerequisite_probe/artifacts/raw/)、[1 FPS 模型输入](../../experiments/prerequisite_probe/artifacts/model_input/)、[隔离真值与实际帧哈希](../../experiments/prerequisite_probe/artifacts/truth/)、[模型原始输出、失败日志及状态](../../experiments/prerequisite_probe/artifacts/model_results/status.json)均已保存。[云端两种模型实际解码帧](../../experiments/prerequisite_probe/artifacts/model_results/)逐帧哈希与冻结输入一致。以下“拟”“尚未”等语句反映执行前预注册时态，以本段与实际报告为当前状态。

**接续核查**：六个编号输入已再做独立像素检查，记录见[观察表](../../experiments/prerequisite_probe/artifacts/blind_visual_observations_20261004.json)；因报告先行披露映射，不能算第二名盲审者。官方原仓库入口、模型卡、固定 revision 权重校验及 RTX 5090 运行记录见[报告](../../reports/prerequisite_probe_phase1_20261004.md)。模型外部输入、提示、帧数、视频和物理标签均未改变。[原生曲线与成对排序](../../experiments/prerequisite_probe/artifacts/model_results/analysis_native.json)只覆盖 TOPReward 原版和单列的 Robometer PR #33 dtype 兼容版；Robometer 严格原版继续标“尚无该模型结果”。任何未来的 LeRobot 端口、量化或改帧数结果也必须另列适配版。

## 1. 本次只问一个可证伪问题

在相同最终目标指令下，Robometer-4B 和 TOPReward 能否同时满足：

1. 红色物体确实挡住蓝色目标，移开后才可抓取时，把移障判为有限正向进度；
2. 红色物体虽被移动但仍挡路，或原本不挡路时，不给同类动作正向进度；
3. 直接抓取并放置蓝色目标时，能够给出明确正向信号。

任何一个单例错误只说明该开发视频上的现象；跨场景族重复后才能提出稳定失败主张。Robometer 已做过奖励训练，结果称对新任务的零样本迁移；TOPReward 是免额外奖励模型训练的主对照。两者都用[官方推理实现](https://github.com/robometer/robometer)与[TOPReward 官方实现](https://github.com/TOPReward/TOPReward)，不因预期结果改模型或提示。

## 2. 为什么选窄口隔间

候选比较：

| 场景 | 优点 | 首轮问题 |
|---|---|---|
| **窄口隔间，红挡块堵入口** | 蓝目标始终可见；阻断与解除能同时从画面和碰撞几何核验；刚体可复位 | 需要自建静态侧壁、顶盖和入口 |
| 单格绿色容器被红块占据 | 目标、障碍和容器都容易看清；清空容器是自然前置动作 | 无效移动要确保红块始终占据唯一有效放置空间；容器尺寸与成功判定需严控 |
| 红色盖子罩住目标 | 移盖很自然 | 蓝目标往往被遮住，模型可能只是没认出目标 |
| 开放桌面前方放红方块 | 制作简单 | 机械臂可能从上方绕过，难证明移动红物体必要 |

第一批选窄口隔间。使用 [ManiSkill 自定义刚体任务](https://github.com/mani-skill/ManiSkill/blob/main/docs/source/user_guide/tutorials/custom_tasks/intro.md)和 Panda 机械臂。隔间左右和顶部为固定碰撞体，只留面向机械臂的入口；蓝色方块在入口后，绿色托盘在隔间外。红色挡块在入口前侧，可从正面抓取。顶部做成带碰撞的栅格，缝隙允许主相机看见蓝方块，但不足以让夹爪通过；挡块也不能把蓝方块完全遮住。静态壁和顶盖是为了排除“绕过去也能抓目标”，但必须经多起始姿态规划与实际继续试验验证，不能仅靠设计图断言不可达。

如果窄口隔间无法通过预先规定的可见性检查，切换到“单格容器被占据”模板；记录淘汰原因，且在查看模型输出前决定是否切换。

同一条最终目标指令固定为：

> Put the blue cube in the green tray.

文字中不出现红色挡块、清障、抓取顺序或步骤。所有片段保持蓝色方块、绿色托盘、红色挡块、相机、灯光、机械臂初始姿态和指令相同；在受控分叉之间只改变挡块的位置或移动结果。固定相机斜前上方，使入口深度、挡块与蓝色目标均可见；另存正面辅助视角供人工核验，**模型首轮只看主相机**。

## 3. 第一组视频的分镜

每段从同一类稳定初态开始，统一为 14 秒：前 2 秒静止，中间 10 秒内完成动作，最后至少 2 秒保持稳定结果。原始录像拟用 30 FPS、640×480 RGB；评分输入固定抽取 t=0,1,…,14 秒的 15 帧，另编码为 1 FPS 视频。1 FPS 与 [Robometer 官方自有视频脚本的默认抽帧率](https://github.com/robometer/robometer/blob/main/scripts/example_inference_local.py)一致；15 帧也与 [TOPReward 默认 15 个视频前缀采样点](https://github.com/TOPReward/TOPReward/blob/main/topreward/utils/inference.py)对应。若动作在抽样中丢失，就在制样阶段调整动作时长和样本，而不是根据模型结果补帧。保留 30 FPS 原始视频以核查动作，不用逐条变速或挑帧制造有利输入。

| 视频代号（内部用） | 固定画面中的变化 | 标准答案要求 | 与谁配对 |
|---|---|---|---|
| B+ 有效移障 | 红挡块初始封住唯一入口；夹爪将它放到旁边停放区；最后入口持续开放，蓝方块未被触碰 | 移障前目标导向继续动作失败或不可达；移障后显著可达/成功 | 与 B0 使用同一仿真初态 |
| B0 无效移障 | 红挡块从同一初态被横向移动或稍微提起，但全程仍覆盖夹爪所需通道，最终也留在入口；动作长度和视觉运动量尽量接近 B+ | 动作全程未解除阻断，继续成功率没有实质增加 | B+ |
| U0 无关移动 | 红挡块初始在入口外，目标本已可达；夹爪把它移动到另一处不挡路位置 | 前后目标机会基本不变 | 与 B+ 保持目标、指令、动作类型一致 |
| H− 妨碍动作 | 入口原本开放；夹爪把红挡块放入入口 | 目标机会下降；从零进度起的模型主要看与不挡路分支的相对排序 | 同初态空动作 |
| G+ 正向能力锚 | 入口开放；夹爪把蓝方块放到绿色托盘 | 直接目标进展必须有正向信号 | N0 |
| N0 时间噪声锚 | 同场景保持不动，或尝试抓蓝方块但未接触并恢复原态 | 无物理进展 | G+ 与 B0/U0 |

在 B+、B0、U0、H− 四类中，蓝方块都不能在评分视频中被抓起或放到托盘；评分视频停在红色动作稳定后。用于核验的后续目标抓取/放置只存于隐藏真值包。这样模型无法直接从末尾成功画面推测“前一步有用”。

## 4. 仿真真值与纳入门槛

从动作前同一仿真快照分叉执行“指定红物体动作”和“等时长空动作”。分叉后使用冻结的、只许操作蓝色目标的继续控制器，固定时限与配对扰动种子，记录后续目标成功率和规划可达性。有效、无效、妨碍按[主计划的预定门槛](2026-10-04-implicit-prerequisite-phase1.md)判别；门槛在看模型输出前固定。若继续控制器本身无法在无遮挡场景成功，先修控制器，不能因此把有障碍状态标为“必要”。

每条开发视频的纳入检查：

- B+ 与 B0 在动作前的仿真状态逐字段一致；除挡块动作终点外，不出现蓝目标、托盘、相机或静态几何变化。
- 同一条视频主视角可辨认蓝目标、红挡块、入口与动作后是否仍阻断；2 名复核者独立判读“入口开/关/无法判断”，分歧先留在开发集。
- 30 FPS 母版与模型实际 1 FPS 输入均能看出动作前后状态；记录抽样帧索引、视频 SHA-256 与时刻。
- 目标导向控制器在无遮挡正控 G+ 初态可成功；B+ 相比等时长空动作确有较大的条件成功率提升；B0/U0 不满足该提升。

若入口视觉上看不清、控制器能绕路、模型抽样没有状态证据，这个模板不入正式测试。先修场景或镜头，保留剔除记录，不能边看模型结果边改。

## 5. 给两种方法的输入

**共同内容**只有英文最终目标指令与同一主相机 RGB 时间序列。每条模型请求的外部输入形如“`video=0001.mp4`（14 秒、1 FPS、15 帧）＋`instruction=Put the blue cube in the green tray.`”。文件名使用无语义编号，不附类别、步骤、仿真状态、继续成功率、目标终局或正确答案。方法各用自己的原生接口；“同输入”指同一视觉证据和任务语义，不强制把两个不同模型改成相同内部抽帧算法。

| 项 | TOPReward | Robometer |
|---|---|---|
| 受测版本 | 官方 TOPReward，Qwen3-VL-8B-Instruct；固定 repo commit、模型 revision、chat template | 官方 Robometer-4B checkpoint 与自有视频推理脚本；固定 repo commit、模型 revision |
| 视觉输入 | 由同一 1 FPS 序列形成完整轨迹；按其原生方式逐前缀评分 | 同一序列作为视频或无损帧数组；保持官方每时点进度推理与原生采样 |
| 文本输入 | 仅固定指令；保留官方实现自带的完成判断模板，并固定其开关和版本 | 仅固定指令；不启用额外步骤文字 |
| 原始输出 | 每个前缀的官方 `prefix_rewards` 原始指令对数似然及对应前缀长度；当前 Qwen 实现以结尾 `True` token 计分，官方逐视频归一化结果不作主指标 | 每个原生时点的进度值及时间戳；success head 另列诊断，不当成进度 |
| 记录 | 实际帧索引、分辨率、提示模板、权重版本、原始分数、耗时、失败/超时 | 实际帧索引、模型配置、原始进度和成功概率、耗时、失败/超时 |

TOPReward 的 `prefix_rewards` 在[当前 Qwen 实现](https://github.com/TOPReward/TOPReward/blob/main/topreward/clients/qwen.py)中，是给定视频和完整指令陈述后对结尾 `True` 的对数似然；它与 Robometer 的显式进度预测不是同一种量纲。因此分别看各自方法内部的事件增量与配对排序，不直接比较两个方法的原始分值大小。初始设备是本机 RTX 4060 Laptop 8 GB。能否运行两套原版权重尚未验证；显存不足或依赖失败是“未取得结果”，不能记作漏判。若使用量化、CPU offload、修改帧数或更换骨干，明确标为适配版，并保留原版尝试日志。

## 6. 第一轮怎么看结果

预先锁定动作前 2 秒和稳定后 2 秒窗口，分别求原生预测的中位数，计算事件增量。重点看 B+ 增量是否大于 B0/U0，B0/U0 是否出现不应有的上升，H− 是否低于匹配空动作；G+ 必须能打出正向信号。阈值先用 N0 开发片段估计评分自然波动并冻结；同时报告无阈值的成对胜/平/负。不得用每条视频各自的 min–max 归一化掩盖基线抬高或缩放问题。

**开发探针验收**：保存 6 类视频母版、模型实际帧包、仿真反事实记录、两种方法的原生曲线及逐例解释。若任一方法在 B+、B0/U0 或 G+ 上表现异常，先排查抽帧/目标识别/接口；仍有现象才在未见过的几何模板上盲测。若两者都正确，记录反证并收窄问题。第一轮任何结果都不能单独证明新方法有必要。

## 一手依据

- [ARS 的语义不匹配实验与指标](https://arxiv.org/html/2609.34484)：设计启发，不是本问题的已发表结果。
- [ManiSkill 自定义任务](https://github.com/mani-skill/ManiSkill/blob/main/docs/source/user_guide/tutorials/custom_tasks/intro.md)、[运动规划演示生成](https://maniskill.readthedocs.io/en/latest/user_guide/data_collection/motionplanning.html)、[Windows 支持范围](https://maniskill.readthedocs.io/en/latest/user_guide/getting_started/installation.html)。
- [Robometer 自有视频推理](https://github.com/robometer/robometer/blob/main/scripts/example_inference_local.py)与[TOPReward 官方使用说明](https://github.com/TOPReward/TOPReward)。
