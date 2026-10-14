# EvoNav 来源记录

检索及续接日期：2026-10-02（Asia/Shanghai）。**用户已回复 A，唯一阅读对象确定为 Dai 等的 CVPR 2026《History to Future》。** 下方初次候选记录保留为消歧历史；材料最新状态以“确认后核验”节为准。

## 检索记录

已搜索 `EvoNav navigation paper`、`"EvoNav" architecture`、`"History to Future" "Evolving Agent" arxiv`。搜索结果用于定位；以下身份记录以会议、作者机构仓储和 arXiv 页面为依据。第三方解读未用作方法或结果证据。

## 候选 A：零样本视觉语言导航推理

**作者事实 / 书目信息**：*History to Future: Evolving Agent with Experience and Thought for Zero-shot Vision-and-Language Navigation*。Guangzhao Dai, Shuo Wang, Zihan Wang, Guo-Sen Xie, Yang Yang, Jinshan Pan, Qianru Sun, Xiangbo Shu。CVPR 2026，pp. 15177–15187，2026 年 6 月。

一手依据：

- [CVF 会议记录](https://openaccess.thecvf.com/content/CVPR2026/html/Dai_History_to_Future_Evolving_Agent_with_Experience_and_Thought_for_CVPR_2026_paper.html)：搜索索引可返回书目、摘要及 pdf/supp 入口，但本次直接打开返回 403，不能写成全文已读。
- [SMU 作者机构仓储](https://ink.library.smu.edu.sg/sis_research/11199/)：可访问；Publication Type、Version、Publication Date、Citation 栏确认已发表版本、作者、会议信息和页码。
- [CVF 正文 PDF 入口](https://openaccess.thecvf.com/content/CVPR2026/papers/Dai_History_to_Future_Evolving_Agent_with_Experience_and_Thought_for_CVPR_2026_paper.pdf)：搜索索引可见正文片段，直接打开本次报错；尚未取得可通读全文。
- [作者同名 GitHub 仓库](https://github.com/daiguangzhao/EvoNav_CVPR2026)：页面可访问；README 标题与论文一致。当前可见根目录为 README、三张图片和 index.html，README 说代码将发布；尚未核查提交树及论文对该仓库的反向链接，因此不声称可运行官方实现已公开。

**作者事实 / 身份区别**：摘要将 EvoNav 描述为借助历史经验 H-CoE 和未来思考 F-CoT 改善零样本 VLN-CE 决策的方法。依据：SMU 页面 Abstract。

**证据缺口**：尚未核验 DOI、arXiv 编号、补充材料内容或精确版本差异。README 作者栏缺少 SMU/CVF 书目中的 Shuo Wang；当前书目以会议记录和作者机构仓储一致的八人名单为准，不推断差异原因。

## 候选 B：导航奖励函数演化设计

**作者事实 / 书目信息**：*EvoNav: Evolutionary Reward Function Design for Robot Navigation with Large Language Models*。Zhikai Zhao, Chuanbo Hua, Federico Berto, Zihan Ma, Kanghoon Lee, Jiachen Li, Jinkyoo Park。

- [arXiv 摘要与版本记录](https://arxiv.org/abs/2605.11859)：已访问。当前显示 v1，提交时间为 2026-05-12 09:43:21 UTC。
- 标识：arXiv:2605.11859v1；[arXiv DOI](https://doi.org/10.48550/arXiv.2605.11859)。此 DOI 是预印本标识，不代表已核实会议录 DOI。
- **作者事实 / 身份区别**：摘要介绍使用 LLM 演化设计机器人导航奖励函数，通过由低成本代理评估到完整策略训练的三阶段过程评估候选。依据：arXiv Abstract。
- **证据缺口**：当前只核验摘要页与版本记录；PDF、附录、官方代码及正式发表信息尚未核验。不能据此评价实验或消融是否充分。

## 候选 C：相近名称的终身导航基准

**作者事实 / 书目信息**：*EvoNav-Bench: Benchmarking Lifelong Navigation in Evolving Environments*。Xilin Wang, Guoxi Zhang, Hongming Xu, Zhuofan Zhang, Tianxu Wang, Lifeng Fan。

- [arXiv 摘要与版本记录](https://arxiv.org/abs/2609.08292)：已访问；v1 为 2026-09-08，当前 v2 为 2026-09-14 03:32:43 UTC。
- 标识：arXiv:2609.08292v2；[arXiv DOI](https://doi.org/10.48550/arXiv.2609.08292)。
- **作者事实 / 身份区别**：摘要描述环境变化条件下的终身导航基准，以暴露旧观察不再可靠时的失效问题。
- **证据缺口**：当前只核验摘要页与版本记录；尚未读全文、附录或核查代码。

## 消歧状态

**我们的解释**：A 与交接中的冻结模型及推理架构语境更接近，但用户明确是借鉴研究流程而非迁移方法，因此不能据此排除 B。C 名称带 Bench，但作为近名候选一并呈现。

**初次决定（已被后续选择解决）**：向用户发出 A/B/C 选择问题，在答案到达前不开展阶段 1—2。用户随后明确回复 A；B、C 仅保留为排除记录，不纳入本轮分析。

## 确认后核验：分析版本与材料清单

### 身份与版本

- **作者事实**：CVF HTML 元数据、正文首页、SMU 仓储和 CVPR 官方会议页面均对应同一标题及八位作者；固定采用 CVF 的 CVPR 2026 Open Access accepted version，正文 11 页，印刷页 15177–15187（内容与结论为前 8 页，后 3 页为致谢/参考文献）。CVF 声明除水印外与接收版本一致，最终出版版本在 IEEE Xplore。不能将这个声明扩大为已核对 IEEE 文件。
- **作者事实**：[会议页面](https://cvpr.thecvf.com/virtual/2026/poster/39872)确认标题/作者并回链 CVF，页面元数据 datePublished 为 2026-04-16、dateModified 为 2026-06-04；这是网页日期，不是 PDF 修订日期。会议信息按 2026 年 6 月记录。
- **证据缺口**：全文及会议页未提供可核实的本文 arXiv 编号或论文 DOI，按全名和作者补充检索仍未定位；不填猜测值，不将 B 的 arXiv/DOI 移植到 A。未进行未取得版本间的差异比较。

### 实际访问与阅读

| 来源编号 | 一手入口与本地文件 | 最新访问及审查状态 |
|---|---|---|
| P | [CVF 正文](https://openaccess.thecvf.com/content/CVPR2026/papers/Dai_History_to_Future_Evolving_Agent_with_Experience_and_Thought_for_CVPR_2026_paper.pdf)；[本地 PDF](sources/evonav_main.pdf) | Python 标准库直接下载成功，11 页已通读；视觉复核 PDF p.3–4 的 Fig.2/Eq.7 和 p.6–8 的 Tables 1–6/Fig.5 |
| S | [CVF 补充 ZIP](https://openaccess.thecvf.com/content/CVPR2026/supplemental/Dai_History_to_Future_CVPR_2026_supplemental.zip)；[解出的补充 PDF](sources/evonav_supp.pdf) | 链接取自实际下载的 CVF HTML；PDF 共 4 页，A–C 节、提示词图及参考文献已读，p.3 的 Fig.3/C.3 已视觉复核 |
| W | [CVF 书目页](https://openaccess.thecvf.com/content/CVPR2026/html/Dai_History_to_Future_Evolving_Agent_with_Experience_and_Thought_for_CVPR_2026_paper.html)；[快照](sources/evonav_cvf.html) | 网页工具报 403，但直接下载成功；确认补充材料实际是 ZIP，先前试探的 .pdf URL 为 404，不代表补充材料不存在 |
| I | [SMU 仓储](https://ink.library.smu.edu.sg/sis_research/11199/) | 书目与摘要已读；其 Download 链接经网页工具返回 403，未用作正文分析版本 |
| C | [CVPR 官方页面](https://cvpr.thecvf.com/virtual/2026/poster/39872)；[快照](sources/evonav_poster.html) | 直接下载成功，确认书目及 CVF 回链；页面另有海报和 YouTube 入口，未分析这两项内容 |
| R | [项目仓库](https://github.com/daiguangzhao/EvoNav_CVPR2026)；[README 快照](sources/evonav_readme.md)、[项目页 HTML](sources/evonav_project.html) | README/项目页及递归目录已读；截至快照仅 README、index.html 和 3 张图，没有可核查的评测/推理源码 |

**视频范围说明**：补充 ZIP 为 110,625,461 字节，内含 `Supplementary Material.pdf` 和 `Real_world video.mp4`。本次下载归档、只提取并分析 PDF，没有播放视频，不能把视频内容写成已观察事实。正文和补充 PDF 的静态真实机器人案例已读。该归档不是训练环境或导航代码。

### 来源冲突与选择规则

1. **已核对差异**：仓库 README 少列 Shuo Wang，但同仓库 index.html、论文首页、CVF、SMU 和会议页面均列八位作者；书目采用一致的八人名单。
2. **已核对差异**：项目 index.html 把两张模拟实验表的数据集标题对调：其标为 R2R-CE 的 24→30 SR 实际对应正文 Table 2 NavRAG-CE；标为 NavRAG-CE 的 23→43 对应正文 Table 1 R2R-CE。研究结论一律以正文图像为准，不使用项目页表名。
3. **代码边界**：仓库所属账号与第一作者同名、项目页自署 EvoNav Team 且回链该仓库；会议页/论文未找到到仓库的反向链接。将其记录为作者名下项目展示仓库，不把这种归属证据夸大为已认证的完整官方实现。
4. **快照固定**：API 核验 main commit 为 `d5858990a89ccc012b6eabb91483458c9672b1c0`（2026-03-18 10:22:29 UTC）；[固定提交](https://github.com/daiguangzhao/EvoNav_CVPR2026/tree/d5858990a89ccc012b6eabb91483458c9672b1c0)。递归目录未截断。没有源码可用于解决实验配置疑问，故未克隆或运行。

### 可追溯性

所有下载文件的来源、字节数和 SHA-256 见 [source_manifest.json](sources/source_manifest.json)。正文 SHA-256 为 `482fa22bc5fee6999276ef6c7040bb6166b4814f42a26a8a1d02062b946e3cc9`。阅读文本由已存在的 `pdftotext -layout` 提取，PNG 由已存在的 `pdftoppm` 渲染；工具有字体告警，关键表格已人工视觉核对，不以乱码推断公式或数值。无新增依赖安装。

引用约定：后续 P 表示此正文，S 表示此补充材料；每条证据继续标明章节、表/图、印刷页或 PDF 页，并附直接链接。核验书目保存在 [references.bib](references.bib)。
