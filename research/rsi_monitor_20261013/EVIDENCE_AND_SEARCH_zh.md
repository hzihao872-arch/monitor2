# RSI—Monitor：原始证据与检索台账

检索日：2026-10-13，Asia/Shanghai。用户已明确目标为 arXiv:2609.36054。本文把 P（论文中已描述的机制/实验）、C（只读见到的官方源码）、H（本项目假设/适配）分开。P不是本机复现，C不证明运行正确，H不是结果。

## 1. 范围、技能、来源与限制

只读阅读四份指定背景：REPORT、DEEP_READ_AND_CODE、DESIGN_AND_MVP、EVIDENCE_AND_SEARCH；位置为 `../monitor_evolution_literature_20261013/`。读取 D:/、D:/monitor2/、research/ 的适用 AGENTS 路径并检索项目内 AGENTS，未发现适用文件。没有读取邻项目 D:/monitor_rsi 的 AGENTS 并套用到本项目。D:/monitor2不是Git仓库。

使用 using-superpowers、nature-academic-search（多源发现＋引文核验）、agentic-research-workflow（项目合同/证据与否证设计）与 PDF 阅读技能。brainstorming 用于方案分歧的检查；用户已明确授权写研究设计、禁止实施，故不创建实现计划、不要求重复批准文献研究。没有启动子代理、后台深搜或新服务。所列专用 academic-search MCP未挂载；已知论文直接用原始 arXiv/正式出版/作者官方GitHub核验，Web发现性搜索补查白皮书，不把二手解读当技术证据。当前不是穷尽系统综述，也不保证找到所有先例。

论文网页、元数据、两篇PDF及选读源码均为小型来源快照。`collect_sources.py`只抓公开原文与元数据，没有下载研究数据集、模型或实验日志，也未导入来源代码。preflight为只读资产检查，未加载模型；观察到约8GB的RTX4060 Laptop与当前Python环境缺torch元数据，不据此承诺可训练性。

来源记录：

- [retrieval_manifest.json](sources/retrieval_manifest.json)：原始URL、获取时间UTC、状态、文件、SHA256。
- [bibliography_metadata.json](sources/bibliography_metadata.json)：19条原始arXiv题名、完整作者、首次日期等 citation meta；不是正式录用数据库。
- 各 `*_abs.txt`：完整提交历史；首次日期和读取版本日期分开。
- 各 `*v*_full.html/.txt`：具体读取版本。main PDF为 `2609.36054v1.pdf`，页码保留在抽取文本；第4–5页另渲染目视核对Figure2和正文。
- [code_manifest.json](sources/code_manifest.json)：官方仓库当前固定commit、只读文件URL与hash。未声称运行复现。
- [background_manifest.json](background_manifest.json)：四份既有背景hash；最终核对不变。
- [references.bib](references.bib)：归档级引文；具体阅读版本/正式论文性质以本台账为准。

已出现的可复核限制：目标文章没有可用arXiv HTML，`/html/2609.36054v1`返回404，改读PDF全文。STOP v2 HTML也404，改读正式标COLM2024的v3 PDF；全文46页。DGM本轮读原始v1（2025-05-29），abs列最新v3（2026-03-12），没有把v1称最新。Hyperagents abs列v1（2026-03-19），HTML内部稿件标注Aug24,2026；记录这个差异，版本引用仍绑定v1，不自行给它编一个新版本。PDF首次渲染尝试fitz不可用，随后用已有pypdfium2渲染成功，未安装任何依赖。

## 2. 搜索记录与用户澄清

按顺序执行的发现性查询（原始字符串）：

1. `"recursive self-improvement" "white paper" 2026`
2. `"The Last AI Built by Humans" RSI`
3. `"Darwin Gödel Machine" self improvement paper official`
4. `"STOP" "Self-Taught Optimizer" arxiv`
5. `AI intelligence explosion white paper September 2026 Hinton Bengio author original`
6. `"AI R&D automation" "September" "white paper" 2026 Hinton`
7. `"ThriftyDAgger" "query" uncertainty risk`

最初先打开给定四候选abs及全文；查询5/6发现Chan等的目标白皮书。此时用户主动回复 `arxiv:2609.36054`，正式确定目标，随后直接读abs和14页PDF，不再凭署名数猜测。新闻/第三方摘要只用于发现标题与链接，不作为报告实证依据。随后精确打开已有Monitor近邻全文；不是重跑整套领域大检索。

源码由论文Code链接→官方仓库→GitHub tree固定SHA→raw指定文件只读保存。未调用README中的安装、训练、模型下载或执行命令。

## 3. 目标文章的证据等级

| 主张 | 原文定位 | 本轮可支持什么 | 不能支持什么 |
|---|---|---|---|
| 更强AI加入研发，研发产生更强AI的反馈机制 | 2609.36054v1 PDF p.3机制段、p.4 Figure2 | P：作者给出的软件研发加速机制 | 我们Monitor选择器已具备该机制或收益 |
| 爆炸属于有条件预测 | p.4 Evidence；p.5收益递减、Compute、Data、Time-intensive processes | P：证据被作者标为初步、混合/间接；存在瓶颈 | 已经观测到无限加速、机器人收益复制宏观收益 |
| 当前未达到触发门槛 | p.5右栏、Societal impacts前的总结段 | P：不能把可能性改写为发生事实 | RSI不可能或一定会发生 |
| r与速度外推 | p.5左栏，r>1段，引用Ho/Whitfill并指向SM | P：作者转述有假设的估计 | 不是本文在Monitor上的训练曲线，不转述为本项目收益 |
| 需要测研发投入与进展 | p.7 Obtaining visibility下指标清单 | P：关注投入、进展和瓶颈的测量 | 不能把政策清单当Monitor方法规范 |

精确短引文（21词，p.5）：

> “Productivity gains from AI R&D automation have not yet reached the threshold needed to trigger an intelligence explosion”

译意：AI研发自动化的生产率收益尚未达到触发智能爆炸所需门槛。句子接着讨论作者认为新系统可能接近门槛，仍属判断。来源：[原始PDF](https://arxiv.org/pdf/2609.36054v1)。本文件不重复长摘录；完整快照用于内部可追溯阅读。

论文分类：依据内容结构，判为证据评议/政策观点与白皮书式预印本，没有提出并运行一个新的闭环RSI算法。不把arXiv-issued DOI、作者机构或新闻报道作为同行评审/机构背书证明。

## 4. RSI系统和概念的最近邻

| 来源 | 已核内容/定位 | 对我们设计的作用与局限 |
|---|---|---|
| [The Last AI Built by Humans v3](https://arxiv.org/html/2609.11873v3) | §2.2.2/2.2.3定义与邻近范式；§3.4经验获取；§3.6改进机制；§2.3证据范围 | P：持久后继与机制复用的框架；包含工业报告等证据，路线图不等于完全实证。H：本项目采用更保守操作性定义 |
| [RSI综述 v2](https://arxiv.org/html/2607.07663v2) | 摘要/评价器分类、loop closure与failure modes | P：区分改行为、政策、评价器与研究过程。H：学生自评信号仅选核验，独立物理证据才能做教师 |
| [STOP v3](https://arxiv.org/pdf/2310.02304v3) | p.1 Abstract；§2优化器自应用；实验与附录 | P：固定LM、改scaffolding improver。原文称“this is not full recursive self-improvement”（7词），限制不能删。H：可以只改有限选择过程，但要自称有限；模型权重更新不是唯一工程对象 |
| [DGM原始v1](https://arxiv.org/html/2505.22954v1) | 自修改coding agent、archive、实测基准；原文与abs匹配 | P：代码能力用于改代理；基础模型本体不是自主变强。H：保留候选/回滚思想；不搬入任意代码搜索 |
| [Hyperagents v1](https://arxiv.org/html/2603.19461v1) | §3任务/meta代理；§4.1冻结meta等对照；§5.2跨域meta transfer；§5.3跨run累计 | P：明确任务表现和修改机制可不同；包含机器人奖励设计，但在仿真RL中评估，非视觉物理Monitor。H：共同学生起点的改进过程对照，不能用任务准确率代替 |
| [MetaRSI v2](https://arxiv.org/html/2609.06396v2) | §4.2三种改写面，§4.5 scheduler；§5.4同一S₁分叉；§6.5物理世界边界 | P：固定评价/释放规则，不同改写面；共同后继、同预算比較旧/新improver。短引文：“the only difference between the branches is which improver ran”（11词）。H：第二轮M₁/w₀与M₁/w₁；不照搬其所有可写字段 |
| [RSI-Anything v1](https://arxiv.org/html/2610.13912v1) | §2.1固定任务标准，§2.3反馈选择，§2.4/2.5更新与保留，§3.1代码修复，Discussion与Table4各域更新范围 | P：预测可指导外部评估，观测反馈用于更新；不同域验证协议的不同部分。Discussion要求joint multiround validation，实验不是一套所有域均完全互相提升的闭环。H：预测提议和真实性分开；首版无世界模型，不涉生物实现 |

这些来源有实际代码/方法/受限实验，但不自动为本项目新颖性或“爆炸式”收益提供证据。完整能力增长曲线、后继选择改善、元过程改善和收益加速是不同主张。

## 5. Monitor核验定位与归因

本轮重新读取Runtime、Sirius、ConditionNET、ARS、WVN、RoboMonitor、Dopamine2、Terrain原文，对表中机制作核查。GCR/HiRE/Thrifty原文补强奖励与主动选择基线。旧背景文中的选读源码hash不改，未把旧核查冒充本轮重新运行。

| 主张 | 精确支持入口 | 界限 |
|---|---|---|
| 部署数据更新下一轮monitor | Runtime §III-D；Sirius §3.1.2/3.2.2 | 接管/风险代理监督不同于几何/指定支撑真值 |
| 更新预测器影响反馈请求已有 | Sirius §3.2.2 adaptive criteria；Thrifty §4.2–4.5 | 是我们的强近邻，不宣称只有我们改善反馈采购 |
| 冻结视觉主体训练条件模型已有 | ConditionNET §III-C/D/F | pre/effect分类、core暂停与多条件C/V/R接口不同；条件概念本身不新 |
| 自适应看证据、区间核验与退步已有 | ARS §3.2–3.6、AppendixB | 是离线全录像推理；不用奖励模型额外训练。不能误称它不挑证据 |
| 后来物理反馈关联过去视觉/在线小头已有 | WVN §3.3–3.5；Terrain §III-B/D/IV | 对应范围、控制器、位置假设要保留；未走不是可靠物理负例 |
| 因果视觉Monitor已有 | RoboMonitor §IV-A/B | predictive预训练与学生当时输入权限分开 |
| 有符号退步与阶段范围已有 | Dopamine2 Method、Structured OOD appendix | 不能以首次退步/首次区间传播立项 |
| 参数/记忆评价器更新都有 | GCR §V；HiRE §3/A.3 | 失败末段和终局仍不等于所有条件负标签 |

全部P；设计中的实体绑定、拒绝跨失效与局部任务作用为H适配。尚无同预算比较结果。没有核实所有论文的全部源码、引用图和新工作，不写“领域无人做过”。

## 6. 本轮实际只读源码

**RSI-Anything**：官方仓库 `Gen-Verse/RSI-Anything`，commit `2582a0f11495af595d41bab3babec57d2c3fb80e`。读取README、code_repair README、world.py、cure_wm.py、evaluation.py、incumbent.py。C：world.py的ExecutionWorld分离预测/score与training_loss，标签来自记录status，保存checkpoint；cure_wm.py有实际执行的返回结果；evaluation.py包含预测排名、反馈与最终hidden评估相关入口。这里只核接口，未验证整套预算/数据划分/论文结果一致性，也未执行任何测试或下载模型。[官方入口](https://github.com/Gen-Verse/RSI-Anything)。

**HyperAgents**：官方仓库 `facebookresearch/HyperAgents`，commit `59a68f672dfb92c74aeb7e61535d776fb36e172d`。读取README、meta_agent.py、generate_loop.py。C：MetaAgent提出修改代码库；generate_loop处理继承patch、评估与val/test资料清理；README链接实验日志。未下载日志，未执行容器、代码或RL。[官方入口](https://github.com/facebookresearch/HyperAgents)。

**awesome-rsi**：`theseus-labs-rsi/awesome-rsi`，commit `74ee83ec39ae5653d1ff3a151f78042a7774c9a4`。它是文献/资源清单，不是路线图论文的可运行统一RSI实现；只读README。没有把代码链接存在当作实验已复现。

MetaRSI正文没有在本轮核实到官方完整代码，报告因此只写P，不写C。

## 7. 当前仍缺的证据

独立正负核验来源、真实分钟成本、冻结特征能否绑定指定几何/实体、足够分组数据、旧任务非劣验证、w代理目标与真实下一轮增益是否一致，全部待验证。是否值得实施必须看原范围主线与预算可行性；本轮只完成文献判断和可否证设计。

完整元数据附表由原始citation meta生成，列在本文件末尾；日期是首次提交，具体版本日见上表与abs历史。


## 8. RSI文献完整作者与首次归档元数据

### 2609.36054

题名：What if automating AI R&D triggers an intelligence explosion?。首次日期：2026/09/28。

完整作者：Chan, Alan；Winter, Christoph；Barto, Andrew；Pachocki, Jakub；Hinton, Geoffrey；Horvitz, Eric；Bengio, Yoshua；Song, Dawn；Clark, Jack；Greaves, Hilary；Korinek, Anton；Hammond, Samuel；Graepel, Thore；Bariach, Ben；Torr, Philip H. S.；McIlraith, Sheila A.；Clune, Jeff；Manning, Sam；Sastry, Girish；Davidson, Tom；Eth, Daniel；Mindermann, Sören。

原始链接：[arXiv](https://arxiv.org/abs/2609.36054)。

### 2609.11873

题名：The Last AI Built by Humans: Toward Genuine Recursive Self-Improvement。首次日期：2026/09/10。

完整作者：Duan, Yi；Liu, Ying；Tang, Zirui；Chen, Haodong；Zhou, Jun；Liu, Yumou；Xu, Bangrui；Wu, Yukai；Chen, Sidi；Zhou, Yuhan；Wang, Haoyu；Yu, Xiaoyou；Han, Shaokun；Zhu, Xuzhou；Zhou, Le；Lu, Bolin；Zhou, Wei；Liu, Jiachen；Fang, Nuozhou；Tian, Jiaxin；Chen, Ruoyu；Li, Yuxuan；Zuo, Kai；Zhang, Kaiyan；Yang, Qianyu；Wang, Zijie；Qiu, Jiantao；He, Conghui；Li, Guoliang；Zhou, Bowen；Liu, Zhiyuan；Wen, Zhoufutu；Kang, Jihua；Zhou, Xuanhe；Wu, Fan。

原始链接：[arXiv](https://arxiv.org/abs/2609.11873)。

### 2607.07663

题名：Recursive Self-Improvement in AI: From Bounded Self-Refinement to Autonomous Research Loops。首次日期：2026/07/08。

完整作者：Chen, Mingguang；Wang, Licheng；Qu, Bo。

原始链接：[arXiv](https://arxiv.org/abs/2607.07663)。

### 2609.06396

题名：MetaRSI / RSI2: A Meta-Recursive Self-Improving System for Recursive Self-Improving Systems Themselves。首次日期：2026/09/06。

完整作者：Tan, Zihan；Sun, Leixin；Shi, Zitong；Liu, Yitao；Wu, Jiajun；Brooks, Nathaniel；Qian, Jiaru；Shang, Xiaoran；Huang, Suyuan；Ding, Yi；Liao, Yangxu；Li, Mukai；Sun, Qiushi；Liu, Shudong；Rong, Xuankun；Yu, Xiaohang；Chen, Zhuo；Geng, Hejia；Li, Chenxin；Wang, Aozhou；Tu, Zengji；Tang, Robert；Zhan, Yuxin；Jiang, Eric；Wu, Yuxin；Zhang, Jianqing；Liang, Xiao；Wu, Fang；Zhang, Haochi；Marlow, Alexander；Wan, Guancheng。

原始链接：[arXiv](https://arxiv.org/abs/2609.06396)。

### 2610.13912

题名：RSI-Anything: Unlocking Recursive Self-Improvement with World Models。首次日期：2026/10/09。

完整作者：Cui, Taoyong；Zeng, Pinxian；Xu, Wanghan；Xiao, Hao；Xue, Shuhan；Gao, Qiang；Ouyang, Wanli；Heng, Pheng Ann；Yin, Zhenfei；Wu, Yingcheng；Yang, Ling。

原始链接：[arXiv](https://arxiv.org/abs/2610.13912)。

### 2310.02304

题名：Self-Taught Optimizer (STOP): Recursively Self-Improving Code Generation。首次日期：2023/10/03。

完整作者：Zelikman, Eric；Lorch, Eliana；Mackey, Lester；Kalai, Adam Tauman。

原始链接：[arXiv](https://arxiv.org/abs/2310.02304)。

### 2505.22954

题名：Darwin Godel Machine: Open-Ended Evolution of Self-Improving Agents。首次日期：2025/05/29。

完整作者：Zhang, Jenny；Hu, Shengran；Lu, Cong；Lange, Robert；Clune, Jeff。

原始链接：[arXiv](https://arxiv.org/abs/2505.22954)。

### 2603.19461

题名：Hyperagents。首次日期：2026/03/19。

完整作者：Zhang, Jenny；Zhao, Bingchen；Yang, Wannan；Foerster, Jakob；Clune, Jeff；Jiang, Minqi；Devlin, Sam；Shavrina, Tatiana。

原始链接：[arXiv](https://arxiv.org/abs/2603.19461)。

