# 服务器准入审查包：隐含前置条件全新场景（本地阶段）

日期：2026-10-06（上海时间）。工作目录：`D:/monitor2`。**本文件只提交本地开发证据；未连接服务器，未下载权重，未产生任何新模型结果。** 根目录不是 Git 仓库；版本身份见 [设计合同](design.json)、[运行卡](RUN_CARD.md)、[文件哈希清单](manifest.json)。本包供原对话审查 G1，不自行批准服务器试跑。

## 结论与准入状态

| 机制 | 几何必要性/反例挑战 | 实际蓝块抓放续行 | 九段/哈希/输入隔离 | RGB 作者审查 | 独立盲审 | 当前 G1 |
| --- | --- | --- | --- | --- | --- | --- |
| A 唯一顶入口盒 | 46 mm 蓝块不能过 0/30 mm 入口；110 mm 开口可入。10,000 姿态挑战未反证 | 两条路线 × 三种成对扰动：开放 6/6，阻挡 0/6 | `dev_v2` 9/9；审计 `pass` | 135 帧逐帧可定位 | 首次原答已封存；九段分类与记录全符；读者的单入口、S 不足以通过及 R 撤销判断经用户转述确认 | **A 组候选，待原对话复核** |
| B 必须部署承托板 | 收起时目标高位无中心承托；50,000 姿态搜索未见阻挡态合格承托 | 两条路线 × 三种成对扰动：开放 6/6，阻挡 0/6 | `dev_v2` 9/9；审计 `pass` | 135 帧逐帧可定位，导轨可能被误解为承托 | 首次九行原答已封存，分类与记录全符；无替代路线、S 理由和 R 时间的补充已由用户确认为未揭盲原话 | **B 组候选，待原对话复核** |

A 组已收到读者首次原答及用户转述的无真值接触确认，[封存和逐项比对](access_gate/dev_v2/reviews/first_answer_assessment.md)显示九段的目标、盒口状态、暂时撤销和末态可完成性分类都与记录相符。读者又在未揭盲时通过用户补充了单入口、九段末态的开放/遮挡理由和 R 的第 8/11 秒改变/恢复。执行者曾误读读者对 S 的“不能判断可以通过”，用户明确澄清其意思是开口仍不足以让蓝块通过。原话与用户澄清分开封存，A `dev_v2` 维持 G1 候选资格。B 组也已收到用户转录的[首次九行原答和接触确认](support_surface/dev_v2/reviews/first_answer_assessment.md)：目标、结构状态、暂时撤销、末态可完成性分类均与记录一致。用户又提供“均无替代路线”、S 黄板未到目标区及 R 第 9/12 秒的补充，单独封存，并确认它们是读者未揭盲原话。两组九条件本地证据已备齐，**建议交原对话审查 G1；尚未获原对话批准，仍不得连接服务器。** 作者看过真值后的逐帧审查不能替代独立盲审。若原对话认为必要性仍无法由合法 RGB 判断，只能继续本地审读或修场景，不能用服务器模型输出来替场景判有效。

## 目标语义、物理证据与最强反例

- A：[目标语义卡及合格/不合格终态图](scene_cards/access_gate.md)、[解析与姿态搜索](access_gate/dev_v2/physics/necessity_report.json)、[替代路线挑战记录](access_gate/dev_v2/physics/counterexample_log.md)、[逐种子抓放与末态](access_gate/dev_v2/physics/paired_continuations.json)。封闭时实体盒底、侧壁和顶框只留一个被有碰撞滑盖覆盖的顶孔；姿态改变不能让 46 mm 立方体穿过 30 mm 净空。最强未消除反例是“边抓蓝块边推盖”，它仍须改变入口状态，故不能证明先独立开盖必要；RGB 上小缺口的可判性待盲审。
- B：[目标语义卡及终态图](scene_cards/support_surface.md)、[更正后的几何报告](support_surface/dev_v2/physics/necessity_report_corrected.json)与[保留的原报告/勘误](support_surface/dev_v2/physics/necessity_erratum.md)、[50,000 姿态搜索](support_surface/dev_v2/physics/static_candidate_search.json)、[替代路线挑战](support_surface/dev_v2/physics/counterexample_log.md)、[逐种子抓放与末态](support_surface/dev_v2/physics/paired_continuations.json)。最强反例是蓝块在导轨或边界上搭住；完整足迹须在中心 ±45.5 mm 内，而绿色标记与导轨内缘分别在 ±57/62 mm，低处桌面不满足高位目标。
- 两者的成功谓词均先于视频写入 [contract.py](../../../experiments/prerequisite_probe/fresh_prerequisite/contract.py)；负例测试见 [test_fresh_prerequisite_contract.py](../../../experiments/prerequisite_probe/tests/test_fresh_prerequisite_contract.py)。谓词核全部角点、目标高度和直接承托接触、松爪与半秒稳定窗口；未用旧中心点标签。
- 几何论证支持“完成前必要状态必须改变”，**不支持**“必须先做独立准备动作”。有限搜索不能冒称数学证明。两种准备结构采用同步于机械臂的预设运动学滑动；开放态蓝块抓放是动态接触成功。该限制需要在任何后续结果中持续披露。

## 九条件、匿名输入与原始证据

两机制均按 `E,S,I_b,N_b,R,H,I_o,N_o,G` 完整生成，主配对 `E>S`、`E>I_b`、`E>N_b`、`H<I_o`、`H<N_o`、`G>N_o` 与 R 轨迹单列检查均在 [design.json](design.json) 预先固定。每段 15 秒、30 FPS 原始记录；模型只见固定主视角 640×480、来自原始索引 `0,30,…,420` 的 15 帧 1 FPS 视频与同一机制的最终目标句。首/末稳定窗为 0–2/12–14 秒；`R` 在第 7、8 秒完全开放，10 秒回阻挡。

| 证据 | A | B |
| --- | --- | --- |
| 九条件联系表（**真值隔离**） | [condition_map.json](access_gate/dev_v2/truth/condition_map.json) | [condition_map.json](support_surface/dev_v2/truth/condition_map.json) |
| 原始 30 FPS 视频与仿真状态 | [raw/](access_gate/dev_v2/raw/) · [sim_states/](access_gate/dev_v2/truth/sim_states/) | [raw/](support_surface/dev_v2/raw/) · [sim_states/](support_surface/dev_v2/truth/sim_states/) |
| 匿名模型输入 | [model_input.zip](access_gate/dev_v2/model_input.zip) · [媒体哈希](access_gate/dev_v2/model_input/media_hashes.json) | [model_input.zip](support_surface/dev_v2/model_input.zip) · [媒体哈希](support_surface/dev_v2/model_input/media_hashes.json) |
| 审读包（无真值） | [reviewer_only.zip](access_gate/dev_v2/reviewer_only.zip) | [reviewer_only.zip](support_surface/dev_v2/reviewer_only.zip) |
| 首次盲审原答/声明 | [原答和用户转述的接触声明](access_gate/dev_v2/reviews/first_answer_assessment.md)；[原答 CSV](access_gate/dev_v2/reviews/reader1_first_answer_20261006.csv) | [转录原答、用户转述声明和比对](support_surface/dev_v2/reviews/first_answer_assessment.md)；[首次九行文字](support_surface/dev_v2/reviews/reader1_first_answer_chat_transcription_20261006.txt) |
| 逐帧作者审查 | [135 帧接触图](access_gate/dev_v2/validation/all_sampled_frames/) · [审查记录](access_gate/dev_v2/validation/author_visibility_review.md) | [135 帧接触图](support_surface/dev_v2/validation/all_sampled_frames/) · [审查记录](support_surface/dev_v2/validation/author_visibility_review.md) |
| 动作/遮挡混杂 | [confounds.json](access_gate/dev_v2/validation/confounds.json) | [confounds.json](support_surface/dev_v2/validation/confounds.json) |

模型输入包只含匿名数字 MP4、最终目标句和媒体清单；真值含条件、几何、接触、续行与排除理由，位于独立 `truth/`、`physics/`。两个 [技术审计结果](audit.json) 均为 `status=pass`、`issues=[]`。A ZIP SHA-256：`3e57af3072091bafbc10b81eea17d8ebd597337458cae5edd6b8433ab5842e78`；B ZIP SHA-256：`3124b5117820707f3458696d4a553f0fee27d41aa969d45eca78bfd84b6cfc9d`。全部文件另见清单哈希。

`dev_v1` 两套首版九段均保留，但因 R 的完全开放只占一个模型采样秒而整体排除：[A 排除记录](access_gate/dev_v1/validation/exclusion.md)、[B 排除记录](support_surface/dev_v1/validation/exclusion.md)。`dev_v2` 两套均统一重录，没有只修单段或按模型表现挑片。

## 验证与未解决事项

- [盲审封存后最终测试原始输出](run_logs/tests_after_blind_review.txt)：`python -m unittest discover -s experiments/prerequisite_probe/tests -p 'test_fresh_prerequisite_*.py' -v`，退出码 0，21 tests OK。
- [盲审封存后最终本地审计原始输出](run_logs/audit_after_blind_review.txt)：退出码 0，`status=pass`，`issues=[]`；[首次失败输出](run_logs/audit_dev_v2.txt) 保留，修复的是审计器而非视频。
- 四次原生 runner `--dry-run` 对 A/B 与 TOPReward/Robometer 均退出 0，每次核九段、每段 15 帧和解码哈希；[运行卡](RUN_CARD.md) 给出命令、目录与日志。Robometer 自带 `extract_frames` 的 [18 段逐帧结果](robometer_decode.json) 与清单全同，未加载权重。
- 未解决：A 组接触确认、补充和原意澄清由用户转述而非读者直接交文件，供原对话复核；B 组首次回答、接触确认及补充也经用户转录，其“没有替代路线”未展开逐条排除导轨/边缘的论证，供原对话判断是否足够；运动学准备滑件不能证明自由动力学抓取。上述每一项在审查结论中不得隐去。
- 执行者基于对 A 读者语句的误读，曾启动一次加宽盖板的本地重录；收到用户澄清后立即中断并恢复 `dev_v2` 的原设计和生成代码。[中止目录](access_gate/aborted_dev_v3_due_to_misread/README.md)仅含局部操作痕迹，不是完整候选版本；没有进入模型输入或盲审。

**下一步是将本地证据包交原对话审查 G1。** 若审查认为读者的物理必要性理由还不充分，继续本地补审或整套修场景。如原对话审查并批准 G1，服务器阶段最多依次进行“现有服务器只读预检 → 旧输入格式 smoke → 新开发视频的原生推理”；G1 通过只允许开发性试跑，不能称未见泛化。服务器地址、密钥和租期由用户另行提供，不写入研究包。正式验证 G2 需在看到未见配置的任何模型输出前另行固定规模和规则。
