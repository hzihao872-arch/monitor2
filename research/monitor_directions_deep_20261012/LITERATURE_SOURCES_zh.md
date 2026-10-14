# 文献、版本与公开来源清单

核查日：2026-10-12（北京时间）。首次公开日期主要指最早核到的arXiv提交，ConditionNET另核正式出版更早日期；不保证它是全网所有渠道最早公开。编号月份不能代替提交日。“当前版本”是当日查得状态，**本次读版本**才对应具体方法结论。预印本不代表同行评审已接受；公开链接、仓库、模型条目不代表资产完整或结果已复现。

本清单包含56项论文、方法或官方资源，并非56篇均全文深读。每行标明阅读层级；SAFE/SuSIE/SayCan/DoReMi及综述等只承担发现或支持性用途。未确认发布、读取失败、已发布三者分开记录。

| ID / 名称及主来源 | 最早核查公开；本次读版；当日最新查得 | 状态 / 阅读层级 | 正文定位及开放边界 |
|---|---|---|---|
| S01 / [ARS](https://arxiv.org/abs/2609.34484v1) | 2026-09-28；v1；v1 | arXiv预印本 / 正文+源码 | §3/4、Fig.2、App.B；evidence_root.md；推理/审计/采集等源码已公开；全部BC流水线/原始评测数据未确认；固定commit 0b61a5de0c39af1788d960ea8dd996aa76b27f7f [官方入口](https://github.com/midea-ai/ars/tree/0b61a5de0c39af1788d960ea8dd996aa76b27f7f) |
| S02 / [RoboMonitor](https://arxiv.org/abs/2609.30715v1) | 2026-09-25；v1；v1 | 预印本/投稿中 / 正文/附录 | evidence_a.md；evidence_c.md；未确认官方可下载完整代码/权重/数据；四监测评测、两闭环 |
| S03 / [Robometer](https://arxiv.org/abs/2603.02115v2) | 2026-03-02；v2；v2/2026-05-13 | RSS2026 / 正文+源码 | evidence_a.md；代码、4B模型及processed_datasets可见；项目Coming Soon文字不等同全资产未公开 [官方入口](https://github.com/robometer/robometer) |
| S04 / [RoboReward](https://arxiv.org/abs/2601.00675v2) | 2026-01-02；v2；v2/2026-01-08 | arXiv预印本 / 正文+资产元数据 | evidence_a.md；HF数据和8B模型条目公开；未下载模型 [官方入口](https://huggingface.co/datasets/teetone/RoboReward) |
| S05 / [WARP-RM](https://arxiv.org/abs/2606.28320v4) | 2026-06-26；v4；v4/2026-09-06 | arXiv预印本 / 正文+源码 | evidence_a.md；官方源码与示例模型数据公开；默认双向但有causal代码 [官方入口](https://github.com/uynitsuj/WARP-RM) |
| S06 / [ReTVL / Beyond Monotonic Progress](https://arxiv.org/abs/2606.24633v2) | 2026-06-23；v2；v2/2026-07-06 | arXiv预印本 / 正文/附录 | §3/App.C.1；evidence_a.md；未确认官方完整代码/权重/数据；明确排除复杂/失败retry等 |
| S07 / [ConditionNET](https://arxiv.org/abs/2502.01167v1) | 2024-12-23 IEEE；2025-02-03 arXiv；v1；v1 | IEEE RA-L；DOI 10.1109/LRA.2024.3520916 / 正文+项目 | evidence_a.md；项目数据入口可见；实现/权重未确认 [官方入口](https://dsliwowski1.github.io/ConditionNET_page/) |
| S08 / [RAFAIL](https://arxiv.org/abs/2609.18324v1) | 2026-09-16；v1；v1 | arXiv预印本 / 正文/附录 | §III/消融；evidence_a.md；未确认官方代码/权重/数据 |
| S09 / [Robot Critics that Sweat the Small Stuff](https://arxiv.org/abs/2606.21572v1) | 2026-06-19；v1；v1 | arXiv预印本 / 正文+项目/代码入口 | evidence_a.md；evidence_c.md；官方代码入口公开；没有复现想象候选选择 [官方入口](https://github.com/SruthiSudhakar/robocritic) |
| S10 / [LRM / Large Reward Models](https://arxiv.org/abs/2603.16065v3) | 2026-03-17；v3；v3/2026-09-30 | arXiv预印本 / 正文+源码 | evidence_a.md；官方实现与adapter模型条目可见；仿真训练仅一训练checkpoint，不能把评测seeds当训练重复 [官方入口](https://github.com/physical-superintelligence-lab/Large-Reward-Models) |
| S11 / [CounterAlign](https://arxiv.org/abs/2608.21740v1) | 2026-08-22；v1；v1 | arXiv预印本 / 正文 | evidence_a.md；项目读取失败，资产未确认，不能断言无代码 [官方入口](https://counteralign.airoa.io/) |
| S12 / [CriticHack](https://arxiv.org/abs/2610.02527v1) | 2026-10-01；v1；v1 | arXiv预印本 / 正文/附录 | §5–8/App.E；evidence_a.md；evidence_root.md；未确认官方仓库；真实40次/条件不能外推显著改善 |
| S13 / [SARM](https://arxiv.org/abs/2509.25358v4) | 2025-09-29；v4；v4/2026-04-27 | ICLR2026（分支核查）；arXiv无venue注释 / 正文+代码入口 | evidence_a.md；先深读v2，再补核v4实现/消融/RA-BC/RA-QL；无逐字diff；opensarm含SARM2，后者未独立审计 [官方入口](https://github.com/xdofai/opensarm) |
| S14 / [ReWiND](https://arxiv.org/abs/2505.10911v2) | 2025-05-16；v2；v2/2025-09-19 | arXiv预印本 / 正文+源码入口 | evidence_a.md；官方代码公开；本轮未运行 [官方入口](https://github.com/rewind-reward/ReWiND) |
| S15 / [Relational Learning for Skill Preconditions](https://arxiv.org/abs/2012.01693v1) | 2020-12-03；v1；v1（本轮确认） | CoRL2020/PMLR2021 / 正文 | evidence_a.md；代码完整性未审计 [官方入口](https://proceedings.mlr.press/v155/sharma21b.html) |
| S16 / [Position: Good Embodied Reward Models Need Bad Behavior Data](https://arxiv.org/abs/2606.01036v1) | 2026-05-31；v1；v1 | ICML2026 Position Paper / 正文 | evidence_a.md；世界模型造数据部分是建议，不能转述为均有实测 |
| S17 / [LfVoid](https://arxiv.org/abs/2307.07837v1) | 2023-07-15；v1；v1（本轮确认） | NeurIPS2023 / 正文+项目 | evidence_a.md；初始图→目标图编辑与discriminator RL已有；不代表本项目编辑必可靠 [官方入口](https://lfvoid-rl.github.io/) |
| S18 / [HiRE](https://arxiv.org/abs/2609.27068v1) | 2026-09-22；v1；v1 | arXiv预印本 / 正文+源码 | §4/6/附录；evidence_b.md；源码和3项MimicGen BC checkpoint公开；ToolHang BC未发布；支持库配置须区分 [官方入口](https://github.com/HiRE-Project/HiRE) |
| S19 / [Demo2Reward / From Demonstrations to Rewards](https://arxiv.org/abs/2606.00083v1) | 2026-05-22（按arXiv提交历史）；v1；v1 | arXiv预印本 / 正文+源码 | §3/4/5、Suppl.A/C；evidence_b.md；prompt与RL代码公开；示范原数据未直接包含 [官方入口](https://github.com/cgumbsch/Demo2Reward) |
| S20 / [eVTA0 / RLER](https://arxiv.org/abs/2609.33653v1) | 2026-09-27；v1；v1 | arXiv预印本 / 正文+源码/资产元数据 | §3/Alg.1/App.B–E；evidence_b.md；训练/评价/GRPO overlay、HF模型数据条目公开；软失败标签使用冻结V-JEPA2特征 [官方入口](https://github.com/duowuyms/eVTA0) |
| S21 / [GCR](https://arxiv.org/abs/2410.19989v2) | 2024-10-25；v2；v2/2025-05-14 | ICRA2025 / 正文+项目；外链附录未全读 | §V/VI；evidence_b.md；项目可读；官方代码/权重本轮未确认 [官方入口](https://gcr-robot.github.io/) |
| S22 / [PACT](https://arxiv.org/abs/2606.03949v2) | 2026-06-02；v2；v2/2026-07-07 | arXiv预印本 / 正文/附录 | §3–6/App.C,E,F；evidence_b.md；作者匿名仓库读取失败，权重/数据未确认；不是空仓证据 [官方入口](https://anonymous.4open.science/r/HILRL-A1X-BC05) |
| S23 / [SOLE-R1](https://arxiv.org/abs/2603.28730v2) | 2026-03-30；v2；v2/2026-05-26 | arXiv预印本 / 正文+源码/资产入口 | §3/App.J,K；evidence_b.md；官方model仓库有模型和训练数据链接；未下载；训练脚本完整性未核尽 [官方入口](https://github.com/Philip-MIT/sole-r1-model) |
| S24 / [RUDDER](https://arxiv.org/abs/1806.07857v3) | 2018-06-20；v3；v3/2019-09-10 | NeurIPS2019 / 正文 | §3/A2.8；evidence_b.md；论文链接官方代码，本轮仓库抓取失败 [官方入口](https://github.com/ml-jku/rudder) |
| S25 / [TAMER](https://www.cs.utexas.edu/~bradknox/TAMER.html) | 2009 K-CAP；原作者方法说明；本轮未作版本史审计 | K-CAP2009 / 作者方法说明/论文入口 | evidence_b.md；反馈延时/信用分配的成熟前例；不是当前VLM方法 |
| S26 / [PEBBLE](https://arxiv.org/abs/2106.05091) | 2021-06-09；正式/指定正文；ICML2021版本 | ICML2021 / 正文 | §4/Alg.2/Fig.5；evidence_b.md；PMLR正文与官方代码入口；未复现 [官方入口](https://proceedings.mlr.press/v139/lee21i.html) |
| S27 / [Eureka](https://arxiv.org/abs/2310.12931v2) | 2023-10-19；v2；v2/2024-04-30 | ICLR2024 / 正文+项目 | §3/G.1；evidence_b.md；官方项目/代码；未执行reward搜索 [官方入口](https://eureka-research.github.io/) |
| S28 / [ProgAgent](https://arxiv.org/abs/2603.07784v1) | 2026-03-08；v1；v1 | arXiv预印本 / 正文 | §3/4/6；evidence_b.md；未确认官方实现；真实部署证据需进一步核，不作已成熟真实系统结论 |
| S29 / [Test-Time Training](https://arxiv.org/abs/1909.13231) | 2019-09-29；正式/指定正文；ICML2020版本 | ICML2020 / 正文 | §2/3；evidence_b.md；PMLR Software入口；用于术语边界 [官方入口](https://proceedings.mlr.press/v119/sun20b.html) |
| S30 / [Tent](https://arxiv.org/abs/2006.10726) | 2020-06-18；正式/指定正文；ICLR2021版本 | ICLR2021 / 方法/官方代码 | evidence_b.md；通用视觉适应，不等同机器人局部reward监督 [官方入口](https://github.com/DequanWang/tent) |
| S31 / [CoTTA](https://arxiv.org/abs/2203.13591) | 2022-03-25；正式/指定正文；CVPR2022版本 | CVPR2022 / 正文方法/官方代码 | §3；evidence_b.md；长期适应/防遗忘前例；未运行 [官方入口](https://github.com/qinenergy/cotta) |
| S32 / [ContactGuard](https://arxiv.org/abs/2608.13438v1) | 2026-08-13；v1；v1 | arXiv预印本 / 正文/附录 | evidence_c.md；未确认官方可下载代码/模型/数据 |
| S33 / [Foresight](https://arxiv.org/abs/2606.23085v1) | 2026-06-22；v1；v1 | arXiv预印本 / 正文 | evidence_c.md；项目读取失败，资产未确认；动作predictor及failure Transformer训练 |
| S34 / [FARM](https://arxiv.org/abs/2609.11445v1) | 2026-09-10；v1；v1 | arXiv预印本 / 正文+仓库状态 | evidence_c.md；官方repo当前README Coming Soon；0.2256ms为head-only，非端到端 [官方入口](https://github.com/HaoranPei-casia/FARM) |
| S35 / [FoMo-FD](https://arxiv.org/abs/2607.27511v1) | 2026-07-29；v1；v1 | arXiv预印本 / 正文 | evidence_c.md；未确认官方完整资产；observed endpoint异常不能称pre-action预警 |
| S36 / [Foundational World Models for Failure Detection](https://arxiv.org/abs/2603.06987v1) | 2026-03-07；v1；v1 | arXiv预印本 / 正文 | evidence_c.md；代码/权重/数据未确认；真实7 nominal/9 failure，小样本证据边界 |
| S37 / [STRIPS-WM](https://arxiv.org/abs/2606.06832v1) | 2026-06-05；v1；v1 | arXiv预印本 / 正文/附录 | §3/App.RQ4；evidence_c.md；evidence_root.md；未确认官方完整资产；graph/高层action权限不得隐藏 |
| S38 / [Code as Monitor / CaM](https://arxiv.org/abs/2412.04455v1) | 2024-12-05；v1；v3/2025-03-21 | 预印本；本次未核最终venue / 正文+项目 | evidence_c.md；本次深读v1，最新v3只查版本；多视角3D权限 [官方入口](https://zhoues.github.io/Code-as-Monitor/) |
| S39 / [RoVer](https://arxiv.org/abs/2510.10975v1) | 2025-10-13；v1；v2/2025-10-14 | arXiv预印本 / 正文 | evidence_c.md；本次深读v1，最新v2只查版本；policy候选action输入 |
| S40 / [World-Gymnast](https://arxiv.org/abs/2602.02454v1) | 2026-02-02；v1；v1 | arXiv预印本 / 正文+源码入口 | evidence_c.md；公开setup/scripts可读；4GPU示例不等于最低预算 [官方入口](https://github.com/world-gymnast/world-gymnast) |
| S41 / [GenRL](https://arxiv.org/abs/2406.18043v2) | 2024-06-26；v2；v2/2024-10-30 | NeurIPS2024 / 正文+代码/资产元数据 | evidence_c.md；官方code/HF模型数据；InternVideo2依赖访问；未下载 [官方入口](https://github.com/mazpie/genrl) |
| S42 / [Sirius Runtime Monitor](https://arxiv.org/abs/2310.17552) | 2023-10-26；正式/指定正文；本轮未核全部版本史 | 2023预印本 / 正文+项目 | evidence_c.md；项目链接后续sirius-fleet，不能等同2023完整实现 [官方入口](https://ut-austin-rpl.github.io/sirius-runtime-monitor/) |
| S43 / [SAFE](https://arxiv.org/abs/2506.09937) | 2025-06-11；正式/指定正文；NeurIPS2025版本 | NeurIPS2025 / 摘要/项目；非全篇深读 | evidence_c.md；用于近邻发现；policy内部信息权限，具体实证不作全文核查结论 [官方入口](https://vla-safe.github.io/) |
| S44 / [FAIL-Detect](https://arxiv.org/abs/2503.08558v2) | 2025-03-11；v2；v3/2025-06-20 | 预印本；本次未核最终venue / 正文 | evidence_c.md；深读v2；最新v3只查版本；success-only OOD/conformal |
| S45 / [Farid et al. Failure Detection](https://arxiv.org/abs/2202.05894) | 2022-02-11；正式/指定正文；RSS2022版本 | RSS2022 DOI 10.15607/RSS.2022.XVIII.042 / 正文 | evidence_c.md；历史传感/PAC-Bayes监测前例，非当前RGB语义任务 [官方入口](https://www.roboticsproceedings.org/rss18/p042.html) |
| S46 / [B2FF](https://arxiv.org/abs/2606.09258v1) | 2026-06-08；v1；v1 | arXiv预印本 / 正文 | evidence_c.md；恢复性与触发迟延前例；资产未确认 |
| S47 / [UniGoal](https://arxiv.org/abs/2503.10630v1) | 2025-03-13；v1；v3/2025-03-18 | 预印本；本次未核最终venue / 正文 | evidence_root.md；evidence_a.md；深读v1；最新版只查版本；posed RGB-D/scene graph权限 |
| S48 / [ImagineNav++](https://arxiv.org/abs/2512.17435v3) | 2025-12-19；v3；v3/2026-04-30 | arXiv预印本 / 正文 | evidence_root.md；另读v1；v3视图选择Where2Imagine；novel view synthesis不等同物理动力学 |
| S49 / [ProgressLM](https://arxiv.org/abs/2601.15224v2) | 2026-01-21；v2；v2/2026-05-21 | arXiv预印本 / 正文 | evidence_root.md；evidence_a.md；另读v1；mental simulation不等于动作条件WM [官方入口](https://github.com/ProgressLM/ProgressLM) |
| S50 / [Vision-Language Models for Robot Success Detection](https://ojs.aaai.org/index.php/AAAI/article/view/30552) | 2024-03-24；正式出版页面；2024正式版本 | AAAI Undergraduate Consortium2024 / 正式短文/页面 | evidence_a.md；小规模VLM成功检测微调的成熟前例；短文证据范围 |
| S51 / [SuSIE](https://rail-berkeley.github.io/susie/) | 未独立核首次公开日；官方项目；本轮未核全部版本史 | 支持性工作；不据此判定venue / 项目机制；非全篇深读 | evidence_a.md；图像编辑/goal相关机制入口；不作详细实证结论 |
| S52 / [SayCan](https://say-can.github.io/) | 未独立核首次公开日；官方项目；本轮未核全部版本史 | 支持性工作 / 项目机制；非全篇深读 | evidence_c.md；skill/value选择前例；不将可执行性等同局部事实 |
| S53 / [Criticality World Model](https://arxiv.org/abs/2607.28251v1) | 2026-07-30；v1；v2/2026-10-03 | 预印本；当前v2题名涉及RSI / 排除项/风险近邻 | evidence_c.md；只核v1风险相关机制；v2 Policy-Level Recursive Self-Improvement，不推荐、不进入候选路线 |
| S54 / [Robot monitoring survey](https://arxiv.org/abs/2607.21655v1) | 2026-07-22；v1；v1（本轮确认） | arXiv综述预印本 / 综述分类/文献发现 | evidence_root.md；只作检索和接口分类，主要实证结论引用原始论文 |
| S55 / [Qwen3.6-27B official model card](https://huggingface.co/Qwen/Qwen3.6-27B) | 本轮未核首次发布时间；2026-10-12模型卡/API快照；在线状态2026-10-12 | 官方模型资源 / 模型卡/资产元数据 | evidence_root.md；确认模型名称和视觉支持；未下载权重/实测，强底座效果仍待试验 |
| S56 / [DoReMi](https://arxiv.org/abs/2307.00329v4) | 2023-07-01；v4；v4/2024-09-14 | IROS2024 / 摘要/正式arXiv页面；非全篇深读 | REPORT_zh.md§4；sources/DoReMi_abs.txt；LLM产生约束、VLM持续检测违反并恢复的早期接口前例；不作细节/定量机制结论 [官方入口](https://sites.google.com/view/doremi-paper) |

## 固定源码与可追溯文件

- ARS：`0b61a5de0c39af1788d960ea8dd996aa76b27f7f`；本轮38个代码/文本文件只读审查。10月10日早先空仓快照仍是历史记录。
- HiRE：`bea7dfb15d1d279bc8f76ff0e8e44b838f696acc`；eVTA0：`8017928d59bc1d3d9051eba43011bd140bf76f54`；Demo2Reward：`2b5082465a4ce7151f479e715df7ab7881807f27`；SOLE-R1：`1c4f3f8340b45fbee5bd5c303fc41ed53072fbbf`。这些是读取快照，不是运行验证。
- [根来源快照manifest](SOURCE_MANIFEST_root.json)保存URL、读取UTC、HTTP状态、SHA256和大小；[A版本记录](a_materials/sources_a_manifest.json)、[C版本核查](c_sources/version_check.json)、B证据笔记§10保存分支版本和仓库状态。
- [机器可读清单](literature_sources.json)保存本表元数据；[A](evidence_a.md)、[B](evidence_b.md)、[C](evidence_c.md)、[跨主线](evidence_root.md)保留机制、局限和全文定位。

## 检索方式与遗漏边界

使用机制关键词的公开网页搜索、arXiv正文/附录、官方项目/源码/模型元数据，并以Undermind分别检索可撤销任务条件、执行反馈适应、动作条件预测与恢复，各返回20项。原始语义结果在sources/undermind_*.txt；[语义检索工作区](https://app.undermind.ai/projects/7e38292f-2b5e-4e86-95bc-9afc5fca5ba5)可追查。仅元数据发现的MURAL/GIFT/SpaTiaL等未被当作完整方法证据。

没有注册系统综述协议或覆盖所有数据库，也不以“未检到”证明不存在。该清单支持当前选题比较，不能保证新颖性。对未读的新版本、匿名仓库失败及不可访问附录已保留不确定性。没有下载权重、租算力、训练或执行机器人。
