# 主线 A：训练可靠 Monitor 的独立证据与问题收缩

核查日：2026-10-12（北京时间）。本文件是主线 A 的研究笔记；不修改历史材料，不运行训练、下载模型或操作机器人。引用的量化结果均为作者报告，未复现。Q=汇总实验；C=具体案例；P=机制/设置；H=本轮假说/研究设计。已阅读指定讨论稿、开发诊断和ARS独立审计；旧“免训练”与停止条件不约束本轮。使用 nature-academic-search 多源检索工作流；预期 academic-search MCP 未挂载，实际采用联网检索、arXiv 正文与附录、作者网站、官方 GitHub/HF，未以二手解读支持结论。

## 1. 条件结论

**泛化的“少样本SFT可靠监测、增加时间一致性、学习关系、识别非单调进度、据评分加权BC”已有密集且直接覆盖。** 首要近邻不只是RoboMonitor/RoboReward，还包括Robometer、ReTVL、WARP-RM、ConditionNET、RAFAIL、Robot Critics that Sweat the Small Stuff、Large Reward Models和CounterAlign。若本项目只是用Qwen3-VL-8B微调同类输出，再接筛选，创新证据不足。

A仍适合作为共同基础，但独立论文应从**具体失效分布、监督效率与下游使用后果**切入。资源有限、仿真为主时，优先保留下面的A1“语义硬错误的少样本可迁移纠正”作为诊断候选；A2“真实倒退与恢复的监督边界”需要先对抗ReTVL/WARP；A3“稀有错误的标注配置与触发延迟”工程价值明确，独立贡献需强实证。它们都只是条件候选，不是已确认空白。

当前八个开发例只能定位错物体虚构、结构漏检和前后状态读取错误。没有独立双标、盲测泛化或有效核验前后配对，不能用它们支持训练有效、原链无效、或特定机制优于现有方法。应保留当诊断素材，另建独立测试。

## 2. 六项合同：先决定监督什么

| 可实现设置 | 输入权限 | 输出义务 | 监督来源 | 更新参数 | 下游接口 | 主要成本 |
|---|---|---|---|---|---|---|
| A0 现成reward checkpoint轻量适配 | 目标+当前帧/视频前缀；无当前技能真值 | success/progress或原任务作用合同 | 少量仿真状态标签+人工核验 | LoRA/小预测头；政策冻结 | 离线评分；之后BC | 基座推理、标注、adapter实验 |
| A1 任务条件与实体关系的局部监督 | 目标+有时刻的前缀；训练可用仿真特权状态，部署不可用 | 当前条件真假/未知，实体ID绑定，某变化建立/撤销何条件 | 独立人工/仿真谓词+同事件不同目标配对 | 相同基座下比较直接标签SFT与结构监督；可先仅头部 | 数据过滤或固定技能的条件门控 | 定义可观察条件、困难负例、跨目标划分 |
| A2 稀疏事件监督的真实非单调学习 | 目标+前缀；离线筛选可另设完整轨迹臂 | 局部方向、恢复/必要动作的保留，不把所有0/负段删掉 | 真实向前执行的倒退/恢复标记；少数事件边界 | 小temporal head或LoRA；不必预训练WM | 固定动作块BC加权 | 有效恢复标签、matching retained data、BC复现 |
| A3 可靠低延迟执行监测 | 若可得到当前技能与预期phase必须单列 | failure/completion+触发/拒判，明确误报与延迟 | 小预算阶段+稀有失败事件，训练/标注预算匹配 | head/LoRA；可冻结skill policy | 技能恢复/停止/重规划 | 高层skill接口、触发校准、顺序闭环评价 |

不能把三个标签混用：条件状态是当前可观察事实；局部任务作用描述哪些条件发生变化；V^pi是固定后续策略下成功期望；A^pi需要比较同状态动作及后续策略。进度差或相对速度不是天然的动作优势。本文A2可使用进度差作为筛选启发，但只有下游测试能说明它是否适合BC。

## 3. 直接证据：最接近论文正文、附录与材料状态

下表日期取arXiv提交历史的UTC日期，避免与上线/检索日期混淆。开放状态截至本轮访问。后文的设计为本轮独立推论，不将作者未单列的指标当作能力缺失。

| 工作/首次—当前版本 | 本轮读到的直接证据定位 | 开放与复现边界 |
|---|---|---|
| **RoboMonitor** 2609.30715；2026-09-25 v1 | [正文](https://arxiv.org/html/2609.30715v1) IV、V、VI/Table I-II：25小时/12任务/2embodiment预测表征，Temporal SFT；52 episodes phase93.09%，failure AP45.87%，同监督Robometer failure59.39%；100时failure72.01%。四个离线监测评测任务均见SFT；闭环仅两个任务（Toolbox Sorting、Reel Packing）。 | [元数据](https://arxiv.org/abs/2609.30715)、[第一作者官网](https://abhiroopajith.github.io/)：under review，RoboMonitor项仅arXiv；本轮未确认官方代码/权重/数据。论文报预训练8H100、SFT4GPU，少标签不等于全流程便宜。 |
| **Robometer** 2603.02115；2026-03-02 v1→05-13 v2，RSS2026 | [正文](https://arxiv.org/html/2603.02115v2) III、IV、Appendix E/F/G：expert进度/成功+跨轨迹偏好、错任务与rewind；已做failure、IL检索、RL和想象轨迹评价。F：76M LoRA+heads，A6000约8h，非52episodes实验。 | [官方代码](https://github.com/robometer/robometer)、[权重](https://huggingface.co/robometer/Robometer-4B)、[processed数据](https://huggingface.co/datasets/robometer/processed_datasets)存在。项目页仍RBM-1M Coming Soon，仓库已提供processed下载入口；未验证全数据覆盖。 |
| **RoboReward** 2601.00675；2026-01-02 v1→01-08 v2 | [当前正文v2](https://arxiv.org/html/2601.00675v2) 4.2/5.3/A.2：同视频换目标+时间截断+VLM检查；负例缺失MAE1.45 vs完整0.845，去截断1.075。5.2有真实机器人RL。 | [数据卡](https://huggingface.co/datasets/teetone/RoboReward)：54,135条，test2,831人工核验；[8B权重](https://huggingface.co/teetone/RoboReward-8B)公开。主要是end-of-episode 1–5rubric；已补读v2的生成机制、rubric及data-mixture ablation，关键结论一致，未逐字diff。 |
| **WARP-RM** 2606.28320；2026-06-26 v1→09-06 v4 | [最新正文](https://arxiv.org/html/2606.28320v4) 3.1–3.5/4.7–4.8/5：time warp/rewind学signed局部速度，冻结DINOv3+bidirectional transformer；仿真WARP290 vsDemInf271（均保留31.5%数据），全量vanillaBC237；真实mistake AUROC0.83，作者明确尚未证明保留有用恢复段。 | [代码](https://github.com/uynitsuj/WARP-RM)、[仿真head](https://huggingface.co/uynitsuj/warp-rm-sim-bottles-sss15)、data/traces公开。官方代码有可选causal attention(默认False)与其他辅助头，因果化架构不是空白。负监督来自倒播，与真实向前退步的分布差由§5明确。 |
| **ReTVL / Beyond Monotonic Progress** 2606.24633；2026-06-23 v1→07-06 v2 | [当前正文](https://arxiv.org/html/2606.24633v2) 3/4/Appendix C-D：标retry开始点，前后偏好+绝对校准，BC保留恢复。Table1局部Drop AUC0.797 vsRobometer0.237；Table7strict-bad retention0.206 vs0.896；C.1排除错物体长错误、失败纠正、不可逆。 | [元数据](https://arxiv.org/abs/2606.24633)，本轮未确认官方代码/权重/数据。C.2报告稀疏标注42.7秒/轨迹平均；主文连续weights与A.2阈值描述需复现时澄清。不能把“成功内含错误”“低成本稀疏事件监督”当首次贡献。 |
| **ConditionNET** 最早确认[IEEE公开](https://ieeexplore.ieee.org/document/10812068)2024-12-23；arXiv2502.01167为2025-02-03 v1；RA-L10(2)2025 | [正文](https://arxiv.org/html/2502.01167v1) III-A/F、IV：当前RGB+当前action文字→pre/effect/neither；phase分割+success监督，差特征对齐动作。core时暂停异常检查，8连帧触发。 | [官方页](https://dsliwowski1.github.io/ConditionNET_page/)含(Im)PerfectPour数据入口；未确认实现/权重。需当前skill/expected phase由BT给定，区别于只有最终目标的Monitor；这是信息合同差异，非自动创新。 |
| **RAFAIL** 2609.18324；2026-09-16 v1 | [正文](https://arxiv.org/html/2609.18324v1) III、IV-D/TableIII：成功demo离线VLM标关系重要性，点云关系+progress条件RND；policy辅助头运行时预测importance/progress。去gate FPR11.6→69.8%，balancedAcc73.4→58.1。 | [元数据](https://arxiv.org/abs/2609.18324)。本轮未确认代码/权重/数据。runtime无VLM，但需RGB-D、tracking、policy辅助训练；不是完全独立RGB黑盒Monitor。结论明确：细微pose错误可能仍在成功分布内；两两可分割实体、tracking假设限制全局性质与接触力检测。 |
| **Robot Critics that Sweat the Small Stuff** 2606.21572；2026-06-19 v1 | [正文](https://arxiv.org/html/2606.21572v1) 3.1/4/5、AppA/C：同初始success/failure同时间帧pair+成功内时间pair SFT；fine failure benchmark与未来候选选择；AppA.2 held-out任务accuracy .740 vsROVER .533、ProgressLM .591。5.3未来grasp幻觉案例；5视频8A100约25s。 | [官方代码](https://github.com/SruthiSudhakar/robocritic)已公开，另[项目页](https://robocritic.cs.columbia.edu/)。成本高的闭环包括视频生成与critic，不能把单SFT成本冒充系统成本。 |
| **Large Reward Models (LRM)** 2603.16065；2026-03-17 v1→09-30 v3 | [最新正文](https://arxiv.org/html/2603.16065v3) III/IV：Qwen3-VL-8B，contrastive DPO、progress/completion SFT，时间proxy；progress/completion输入为当前帧或初帧+当前帧，contrastive二帧或加初帧三帧；冻结reward供PPO。Tri55.31低于单progress58.94与baseline55.62；completion69.38 vsbase69.23。 | [代码](https://github.com/physical-superintelligence-lab/Large-Reward-Models)、[adapters](https://huggingface.co/USC-PSI-Lab/LRM-models)公开。v3真机是weighted BC，PPO仿真；30iterations≈768k env steps；5评价seed但每condition一个trained checkpoint。 |
| **CounterAlign** 2608.21740；2026-08-22 v1 | [正文](https://arxiv.org/html/2608.21740v1) 3/App1-2：instruction-observation-action chunks重标，类似样本过滤、joint relabel nnPU，adversarial discriminator+offline RL。 | [作者项目链接](https://counteralign.airoa.io/)工具不可达；本轮未确认代码。输入包含action，作用是行为语义一致性，与视频结果Monitor部分重合；“换目标造困难负例”不是新的监督原理。 |
| **CriticHack** 2610.02527；2026-10-01 v1 | [正文](https://arxiv.org/html/2610.02527v1) 5.3/7/9、A.1/M：整体AUROC.813而wrong-object.372；优化放大错目标。已以sim标签小verifier纠正，384/456/2536标签；verifier-only可同样恢复。 | [元数据](https://arxiv.org/abs/2610.02527)。§10复现声明列CPUartifact/weights manifest，本文无可确认公开仓库链接。是真实优化反例，非所有模型/任务定理；硬件40trials差异未统计解决。 |
| **Vision-Language Models for Robot Success Detection** 2024-03-24 AAAI UC | [官方论文页](https://ojs.aaai.org/index.php/AAAI/article/view/30552)：MiniGPT-4少轨迹SFT，跨场景/视觉变化泛化困难，语言变化较稳。 | 3页本科论坛论文；成熟问题证据，不能与近年强模型直接排名。 |
| **SARM** 2509.25358；2025-09-29 v1→2026-04-27 v4，ICLR2026 | [当前正文v4](https://arxiv.org/html/2509.25358v4) 3/4/AppA：stage+within-stage progress，由自然语言subtask标注，reward-aligned BC；A.8另有仿真RA-QL例子：300专家、100标reward、DiffQL 10k steps。 | [opensarm](https://github.com/xdofai/opensarm)现在也含SARM2/ReWiND训练与labeler；不是纯新SARM实现。v2方法深读后补核v4实现、ablation、RA-BC/RA-QL；未做逐字版本diff。 |
| **ReWiND** 2505.10911；2025-05-16 v1→09-19 v2，CoRL2025 | [正文v1](https://arxiv.org/html/2505.10911v1) 3/5/App：冻结预训练embedding的小reward model，rewind与misaligned text，offline→onlineRL。限制讨论tiny data embedding微调可能伤泛化。 | [官方代码](https://github.com/rewind-reward/ReWiND)含MetaWorld reward训练、labeling与policy训练；权重/数据逐项未下载验证。 |
| **Relational Learning for Skill Preconditions** 2012.01693；2020-12-03 v1，CoRL2020/PMLR2021 | [PMLR正文](https://proceedings.mlr.press/v155/sharma21b/sharma21b.pdf)：仿真交互学对象对连续关系，少样本real技能前提，sweep/cut/unstack。 | [正式页面](https://proceedings.mlr.press/v155/sharma21b.html)。对象分解与关系的前提泛化已有成熟先例；本轮只读前提问题与机制，未完整代码审计。 |
| **Good Embodied Reward Models Need Bad Behavior Data** 2606.01036；2026-05-31 v1，ICML2026 position | [正文](https://arxiv.org/html/2606.01036v1) 3/4 Fig4-5：RoboArena比较并通过GVL的failure视觉/密集负reward ICL改善；纯文本负例弱。 | [官方PDF](https://cmu-intentlab.github.io/pdf/tian_icml_26_position.pdf)。方法性证据是ICL对照，不能当作少数据SFT实测；其建议WM造失败数据是倡议而非已验证全部链条。 |

## 4. 问题与机制重合矩阵（可合入总矩阵）

“高度重合”只针对明确候选版本；输入不同不足以自动构成新贡献。下表每行对问题、输入、监督、机制、训练/适应、下游六项同时比较。

| 我方候选版本 | 最近已有工作 | 问题/输出 | 输入信息 | 监督 | 机制/参数 | 下游 | 判定与剩余验证 |
|---|---|---|---|---|---|---|---|
| 少数episode训phase/failure/completion+时间一致性 | RoboMonitor | 几乎相同 | 两者goal+causal camera | 我方也标phase/事件 | Temporal SFT已覆盖 | 我方BC/对方恢复 | 高度重合；换下游不足，需具体监督及泛化问题 |
| 预训练reward model再LoRA | Robometer | progress/success同类 | video+goal | robot supervision | checkpoint+heads/LoRA已实做 | BC/RL/监测已覆盖 | 高度重合；可作为低成本强初始化 |
| 成功视频换goal、clip补negative | RoboReward | calibrated outcome | 同video换指令 | 自动生成与检查 | Qwen SFT | RL | 高度重合；编辑像素只是新增造数手段 |
| 时间倒放学负/速度，加权BC | WARP-RM/ReWiND | signed进退 | 离线窗口可非因果 | warp/rewind | frozen features+temporal head | 筛选/BC | 高度重合；真实回退分布与恢复保留可研究 |
| retry点学局部下降恢复保留 | ReTVL | 同需求 | causal history+goal | sparse retry point+outcome | pairwise+abs calibration | weightedBC | 高度重合；失败纠正/探索retry/任务条件仍待实验 |
| 前提/效果分类+差特征一致性 | ConditionNET | 核心条件判断相同 | 对方有current skill/BT phase | segmented skill成功失败 | frozenDINO+CLIP,train transformers | 恢复 | 部分/高度重合；移除skill权限需证可用性而非仅限制输入 |
| 任务关系重要性抑制无关变化 | RAFAIL | relation-aware failure同 | RGB-D+policy heads vs独立RGB | success+VLM importance | relation RND OOD vsSFT | 执行报警 | 部分重合；独立策略/视角泛化与semantic-specific FPR |
| 双帧+/-/0、完成、进度三输出 | LRM | 相同功能族 | goal+localframes | temporal proxies | LoRA/SFT/DPO | PPO/BC | 高度重合；标签应独立于时间proxy，三合一不自动收益 |
| paired success/failure训练细粒度critic | Robot Critics Small Stuff | 进度失败 | paired same-init frames | onlyterminal+时间配对 | VLM SFT | futurecandidate selection | 高度重合；真实partial recovery/错目标分组需诊断 |
| wrong-goal/identity hardneg再训练 | CounterAlign/Robometer/CriticHack | semantic错误 | 对方部分输入action/终局 | relabel/真实simlabel | discriminator/LoRA/verifier | offlineRL/优化 | 部分到高度；只有held-out relations+budget优势才可区分 |
| 基于目标关系核验避免错误目标 | UniGoal/Relational preconditions | 操作不同、机制相邻 | goalimage/RGB-D objects | navigation/interaction | graphmatch/relations | 导航/前提预测 | 方法借鉴；不宣称关系核验首创 |

## 5. 三个可保留具体问题与必要诊断

### A1：语义硬错误的少样本、跨条件可迁移纠正

**问题（H）**：在相同人工分钟数和训练算力下，监督目标实体与其关系的最小证据，是否比再增加一般成功/进度标签更有效地减少会被筛选放大的高分错例，并泛化到未见对象—容器—条件组合？输出限定为可观察条件与当前事件的建立/撤销，不先承诺完整自由语义因果推理。

证据入口是当前结构/实体错误与CriticHack的wrong-object放大；现有回应已包括instruction negatives、反事实重标、关系encoder和task-specific verifier。拟议区别**不是发现wrong-object**，而是验证“跨关系的监督单元与预算效率”能否超过直接success-SFT/Robometer适配、CounterAlign式relabel和专用verifier。若做不到则降为工程改进。

最低成本诊断：先造独立、可审读的60–100个短prefix，覆盖错物体、错关系、入口未有效打开、支撑撤销、无关外观变化；其中同像素配不同goal，给视觉几乎相同而作用相反的对照。训练尚不需要：比较当前8B、可负担强VLM、RoboReward/Robometer原checkpoint及ARS式充分提示。在没有现成可运行模型资源时只完成数据/标注与接口预登记，不能伪报模型实测。

先做**oracle下游价值检查**：以可信标签筛去semantic bad chunks并保留必要准备/恢复，和等量随机、全量BC、success-only筛选对照。若oracle选择不能改善固定策略，说明“Monitor更准→BC更好”这一链条不成立，应考虑技能门控或放弃该数据接口。

后续最小训练：比较纯label SFT、atomic state监督、state+cross-goal/cross-relation监督、仅更大随机负例量；标注预算按分钟、而非伪等量生成样本计。场景源轨迹/对象组合/编辑模板三重隔离，真实sim prefix为测试，不用编辑图测泛化。报告全局准确之外的top-reward-tail bad-retention、per-goal FPR、实体/关系条件联合错误。完整论文需新组合/新scene与固定BC下游，多个policy训练seed及独立成功判据。

支持条件：在匹配预算/负例数量后，关系监督在held-out组合降低高分semantic错误，保留正确准备，且下游提高独立成功。降级条件：只在同编辑模板有效、强底座已全部解决、等量一般SFT相同、或task-specific success head更便宜且同样好。应直接报告这些结果。

### A2：真实向前倒退与恢复的监督边界

**问题（H）**：从successful demos的倒播或retry启发得到的监督，在哪些真实前向执行中会错标，少量可信event标签能否校正且保留成功必需的准备/恢复动作？重点对象是“关盖→再开→放入”“移支撑→返回”及探索性/失败纠正。该问题同时涵盖A，若更新监督来自执行后果则延伸B。

WARP已在§5承认倒播分布差；ReTVL已做恢复保留，且C.1明确排除failed corrections和长错物体段。因此这里只能把被排除模式/可观察条件更新当具体评测边界，不能断言现有模型不能处理。把“非单调”直接改名的方向应放弃。

最低成本诊断：配对真实前向撤销与对应倒播、外观变化对照；前缀observer只看合法过去，离线observer可用全窗口另列。通过人工/仿真检查，分开“条件撤销”和“必要回撤”(如放置后退开)。同一视像时间速度变化不应被当semantic错误。先测WARP/Robometer/ReTVL可实现recipe与直接变化判别；没有真实weights时明确为recipe重实现设计。

训练对照：warp-only、retry-only、real sparse event-only、混合；所有臂用相同backbone/训练预算、相同真实标签预算。增加no-abs和causal输入对照，避免把额外输入权限/未来证据当机制优势。BC匹配任务、每stage、action chunk、保留量及更新数；只按positive-progress硬删可能移除necessary setup，必须报告recovery retention和required-neutral retention。

支持条件：作者同配方在新增模式失配，稀疏真事件校正跨模式泛化，BC保留恢复并提高成功；降级条件：现有ReTVL/WARP已好、只是标注更多、净收益只来自长episode筛选、oracle删段也不改善策略。完整论文成本是多模式真实forward rollout、时间核验、小训练+可复现BC，而非WM训练。

### A3：稀有错误的标注配置与触发延迟

**问题（H）**：给定很小标注预算，均匀phase标注、error event中心采样、错目标困难例或uncertainty采样，哪种支持低误报且及时停止/恢复？问题价值来自小数据failure能力与频率不对称，而非换LoRA本身。

RoboMonitor的52-episode failure AP未优于Robometer，ConditionNET core暂停、8帧过滤引入实际检测范围与等待，RAFAIL关系importance gate会抑制FPR也降低TPR。以上是已有作者实测/明确机制，可形成“准确稳定—漏错—触发延迟”三者的测试合同。不能因某论文没报delay就宣布它迟钝。

最低成本诊断：建立固定policy+固定恢复skill，不训练policy；异常注入时刻随机且含无关变化，记录第一次可观察证据与首次触发。比较静态Temporal SFT、同预算error-focused训练、threshold/hold-time calibration、低成本specialized ConditionNET式头。phase accuracy与switch rate不足，必须报固定FPR下recall、detect delay分布、错误停止次数、每minute调用成本及closed-loop task success。

支持条件：error-focused预算在新scene提升recall且不靠延迟更多，改善技能闭环；降级条件：简单阈值/8连帧规则已同样，或专用小head完全替代VLM，或标注成本高于few-shot prompting。完整论文需真实或高质量仿真扰动闭环与policy/skill更换，另测忘记旧phase。资源极少时只做冻结policy的门控，避免再引入RL。

## 6. 图像编辑、world model造数据与导航借鉴

**图像编辑是监督手段（H）**。标签必须以目标及前后条件定：开盖可为放入准备，关盖可为收纳完成，原图/编辑图没有固定正负。RoboReward和CounterAlign已用同视频换目标；[LfVoid](https://lfvoid-rl.github.io/)（arXiv2307.07837，2023-07-15v1、NeurIPS2023）已编辑初始观测生成goal、训练discriminator奖励。[SuSIE项目](https://rail-berkeley.github.io/susie/)可作为子目标生成相邻方法，本文未独立深读其全文，不据此主张具体指标。

可验证的编辑数据配方：同scene编辑只改变一条件、外观编辑保持条件、同改变换goal；独立人审编辑是否发生预期实体/几何改变。用真实仿真event测试、hold out生成器和编辑模板，匹配负例数量。若编辑只能教会痕迹则停止。连续历史中的遮挡、身份重现及撤销不能只靠单对静态图确认。

**World model造数与Monitor预测是两个命题。** 用WM候选失败/恢复视频增加A监督，需要另有可信真值检查，不能以生成器想象后果直接标物理真值；学习未来预测应归C。Robot Critics Small Stuff的未来grasp幻觉直接说明生成可见结果不是已经发生。将WM用于生产候选数据可降低获取cost，也可能增加validation cost，须计入总标注预算。

**导航仅借机制**：[UniGoal正文](https://arxiv.org/html/2503.10630v1)（首次2025-03-13v1，当前v3 03-18）用goal/scene graph、partial matching、verification及blacklist；HM3D IIN ablation remove verification58.2 vsfull60.2。迁移候选是实体ID+关系证据、被新观测推翻的事实撤回、防重复错误匹配。上述已有navigation实证不自动意味着操作可用，应与普通结构化state table/直接SFT比，尤其禁止把blacklist错误永久保留。完整导航系统不在A最小成本计划中。

## 7. 成本分解与暂缓项

| 项 | 先验证所需 | 完整论文所需 | 暂缓/停止理由 |
|---|---|---|---|
| 泛SFT基础 | 独立少量标注，checkpoint推理基线，LoRA资源估算 | 多budget、多scene、下游 | 当共同基线；自身近同RoboMonitor/Robometer |
| A1 semantic条件监督 | cross-goal诊断、真值核验、oracle filtering价值 | matched-budgetSFT、held-out关系、BC或skill闭环 | 如果普通success head同效则无独立方法贡献 |
| A2 true forward reversal | 真回退与倒播的配对审读、existingrecipe比较 | 混合label训练，恢复/neutral保留，BC多seed | ReTVL已覆盖retry保留；只能研究证实的边界 |
| A3 rare failure预算 | anomalyevent合同、冻结skill门控、阈值基线 | 标注效率曲线、延迟/FPR、跨skill闭环 | 简单规则同效时降为部署研究 |
| 从零预测表征预训练 | 先复用现成reward/vision表征，查是否净收益 | 无标注action多camera corpus+pretrain | RoboMonitor8H100级别训练非有限资源首选 |
| 完整VLA PPO/真机RL | 首先证明reward/offline oracle可用 | simulator/rollout、policy优化、独立success、rewardserver | 工程依赖远高于BC/skill门控；不是A必需 |
| 生成视频WM+critic闭环 | 可先真实候选短skill，不训生成模型 | dynamics质量、multi-candidate、latency/闭环 | SmallStuff 8A100约25秒显示成本；归C有近同方法 |

不能凭“一个GPU”推算本项目小时：Robometer的A6000约8h是特定数据、steps、batch与76M LoRA+heads的实测，迁移只可作参考；8B多图SFT的显存/吞吐取决于分辨率与window长度。标注成本按人分钟、复审与废弃生成样本计，源数据清洗/skill集成/独立后果评价也属于论文成本。

资源变化：有现成冻结skill与仿真接口时A3可能先于A1；有混合质量动作chunk与现成BC系统时A1/A2优先；只有RGB开发视频而无action/下游数据，先做诊断与合同，不能承诺BC论文。若有多GPU与已有WM/RL框架，可提升A与C接口联动，但仍须对抗SmallStuff/Robometer DreamZero/World-Gymnast而不是重做名称。

## 8. 审读材料与核验限制

`a_materials/`保留arXiv HTML文本转存，仅用于本地阅读；版本包含RoboMonitorv1、Robometerv2、WARPv1/v4、LRMv1/v3、ReTVLv1/v2、ConditionNETv1、RAFAILv1、RobotCriticsv1等。本轮未下载权重、运行训练、模拟rollout或真实机器人。

[来源版本清单](a_materials/sources_a_manifest.json)保留17条arXiv工作标题、直接URL及UTC提交历史，便于审计首次arXiv版本与当前版本。arXiv首次提交不必等于全网首次公开：ConditionNET的IEEE Date of Publication为2024-12-23，早于arXiv；其余来源表主要以最早可核arXiv公开日记录，未声明比其他所有渠道更早。

官方GitHub HEAD记录（2026-10-12访问）：

- robometer/robometer: `352d160389daa964788de1ec933d1925f3a6de4f`；249 blob文件。已读README、rbm model、trainer部分、download script。
- uynitsuj/WARP-RM: `26f9894abdaf883af8db78a38e164764e5bf7c00`；63文件。已读transformer.py、loss.py、reproduce_sim.md。可选causal仅证明实现存在，未查全训练recipe是否启用。
- rewind-reward/ReWiND: `ea5dd3be409bbe81e9d0177f73202b9fbf41d1f2`；60文件，README训练与labeling流程。
- physical-superintelligence-lab/Large-Reward-Models: `5845ab0f7c3c6a0bef8bd37bf7f07e9533f7ed2f`；25文件。README提供RLinf reward-server/PPO与HF adapter入口；不能等于SFT数据生产全可复现。
- xdofai/opensarm: `9978198d4c6601f34063fa40e63f9ddc5baf7f68`；153文件。README包含SARM2；本轮SARM2没有独立全文审计。

检索用语覆盖execution monitor/success detector/progress reward/relative progress、retry/recovery/non-monotonic、condition/precondition/effects、object-relation/semantic failure、counterfactual relabel/data curation/weightedBC及image-goal navigation。已做标题搜索、种子引文扩展与官方链接核查；不是穷尽搜索。“本轮未确认公开材料”不等同永久没开源；“待确认”不等同领域空白。

建议给师姐的A讨论句：**训练是需要建立的基础，但泛化SFT路线已经很满。先看在固定标注分钟数下，实体—关系条件监督是否比一般success/progress标签更能减少高分错目标并保持必要准备和恢复；只有独立目标/关系与下游均成立才继续。若已有模型和简单success head解决，就把训练当基线，把核心问题移向可信反馈或预测接口。**
