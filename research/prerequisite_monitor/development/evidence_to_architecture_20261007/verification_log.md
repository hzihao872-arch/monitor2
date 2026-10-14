# 本地复验记录

2026-10-08（Asia/Shanghai）；工作目录 `D:/monitor2`。本文件前两节记录**上机前**本地检查，当时没有 GPU 模型调用、服务器连接、上传、租赁或权重变动。文末另记本次现有实例实测和下载核验。`D:/monitor2` 无 `.git`，项目级 `git status` 返回 `not a git repository`；本记录用封存 seal、逐文件 SHA 和本地脚本输出作身份链。

| 复验命令 | 新鲜输出/结果 | 可支持的范围 |
| --- | --- | --- |
| `python research/prerequisite_monitor/fresh_server_20261007/local_results/verify_final.py` | `native_seals_verified=3; p1_seals_verified=3; hash_rows_verified=20; report_links_verified=23; p2_points_identical=540; p2_pair_flips=0`；退出 0 | P0–P3 及 P1 封存身份和同输入逐点复测。 |
| `python research/prerequisite_monitor/fresh_server_20261007/local_results/verify_additional.py` | `stages_verified=5; archive_sha_verified=5; manifest_file_rows_verified=221; model_outputs=90; model_failures=0`；退出 0 | P4–P6 追加输出、包、逐文件哈希；P5 visual 解析失败仍为失败。 |
| `python research/prerequisite_monitor/development/evidence_to_architecture_20261007/build_evidence_index.py` | 18 行；索引 SHA-256 `781f674b9ae86a03589764987bac0905df2b5fb7fa2bd02fcd28541a1891f320`；退出 0 | 每案 P0/P4 视频 SHA、TOPReward 模型路径相等；P2 540 点零差、24 对无翻转；原答/曲线/源哈希合并。 |
| `python research/prerequisite_monitor/development/evidence_to_architecture_20261007/run_local_dry_run.py` | 18 段、162/162 实际解码帧哈希相符、10 个抽象协议例；报告 SHA-256 `ae0c77af86349aca4c029163e3e51d85a9417e1d740622580d93286f82ae6ccd`；退出 0 | 输入包与证据索引、完成优先、R 撤销、unknown、解析/证据错误处理的程序通路；**不验证模型能力**。 |
| `python research/prerequisite_monitor/development/evidence_to_architecture_20261007/create_machine_preflight_bundle.py` | 4,863,093 字节；SHA-256 `c4671c5d0ac0e23126d85ccbe98da7ec282dd1918d4f5834140c6dfa5df7b12d`；退出 0 | 可复建的匿名输入预检包；外层 5 件，内层各 9 视频＋目标/清单/媒体哈希，无 truth/condition/answer/score 文件名。 |
| `python -m py_compile` 四个本地 Python 文件 | 退出 0 | 语法检查。 |
| Markdown 链接/JSON 示例/包成员即时检查 | 新目录 9 个 Markdown 文件本地相对链接缺失 0；示例 `spec_version=0.1.1`、`mid_second=7` 可解析；两内包 SHA 与清单一致；本地检查点 19 个文件哈希无变动。 | 文件可定位，当前 JSON 示例和包结构可解析；不是模型输出评分。 |

**已知限制。** (1) 本地实测模型输出仍全是已暴露开发材料；没有 D2/T/P/F/H 的新同预算模型结果。(2) TOPReward/Robometer 的原生曲线没有对象关系原答，内部失败环节无法定位。(3) P5 两问独立且 9 个 visual JSON 解析失败，不能当作感知与续行瓶颈的干净因果分解。(4) 旧场景有替代路线/构念争议。(5) 接口 0.1.1 的合成 dry run 不提供物理可行性证明。`METHOD_FREEZE`、真实服务器运行及 G2 仍待后续阶段。

## 2026-10-08 单次上机开发包补充复验

用户要求把候选、同预算直接法、失败诊断和文字敏感性在下一次现有实例上尽量跑全。新增[预登记](./ONE_SESSION_EXPERIMENT_FREEZE_v0.2.md)和[运行卡](./RUN_CARD_ONE_SESSION_v0.2.md)，只冻结**开发实验**，不提前选架构。

| 复验 | 本地新鲜结果 | 边界 |
| --- | --- | --- |
| `python -m py_compile` 八个新脚本及 `bash -n run_existing_instance_v0_2.sh` | 全部退出 0 | Python/壳语法；未加载权重。 |
| `python build_one_session_package.py` 重复两次 | 同一包 SHA-256 `7d6608846c07eb9eeedfb3c4b72c3c6aeebcdea69b4a01961b693e4362814cd8`，4,881,897 字节；模型侧 10 个成员逐一核 SHA，内层各九段；未含本地评分脚本、真值或条件映射 | 确定性构包和输入隔离。 |
| 从该包解出运行 `one_session_suite_v0_2.py --dry-run` | 18 个视频、162 条提示、0 个模型调用/运行失败；JSONL SHA-256 `974f4784137151df485bce6ea982a8ffeb9984980dd4f38ed8b4bcbb71d3f3ab`。V0 的 18 条提示 SHA 相同且不含目标文字；9 帧解码/像素哈希逐案核验。 | 视频身份、提示路由、帧和调用位齐全；不说明模型准确率。 |
| 全失败 **MOCK** Qwen 原答 → seal → 本地 audit | 模拟 162 条运行失败全部保留；seal complete=162/162、审计 180 行（含派生 H3），108 对配对结果；V0 不进入方向得分。 | 只验证失败留存、揭盲连接与分母，不是假装模型实测。 |
| 四文字构建器 → native dry run → 全失败/全零 **MOCK** 曲线 → seal → 本地 audit | 72 个文字输入行、原生 dry 解码通过；模拟 72 作业封存，7 变体（含已封存 P0/P4）126 案例曲线、84 对配对。另用一条抽象候选测试 `auto_relation`/`auto_counterclaim` 分支。一般提醒与中性句均 171 字符，原生 token 数待上机记录。 | 只验证文字变体的输入/输出/曲线审计通路；模拟零曲线不是实验结果。 |
| 单独抽象视觉事实 JSON 与错误秒数 | V0 有效样例通过；错误秒数失败；P5 旧 `7/8` 字符串不会被新提示当作值示例。 | 仅 schema 逻辑。 |

截至上述**上机前**检查时仍没有新模型推理、TOPReward 新文字曲线或真正未见 G2。旧 `local_preflight_v0_2*` 目录内大写 `MOCK` 文件只用于无模型通路复验，不参与论文结果或上传包。

## 2026-10-08 现有实例实测与回本地核验

用户随后提供其已有实例及约一小时剩余租期。本次只使用该实例已有权重、环境和官方 TOPReward checkout。身份、dry run、pilot、162 次 Qwen 主调用、72 次原生文字作业、封存及下载的过程和失败细节见[执行日志](./remote_one_session_v0_2_20261008/execution_failure_log.md)；结论见[结果报告](./remote_one_session_v0_2_20261008/RESULTS_REPORT_zh.md)。这不是 G2。

| 核验 | 结果 |
| --- | --- |
| `python remote_one_session_v0_2_20261008/verify_local_chain.py` | 退出 0；ZIP SHA `7d6608846c07eb9eeedfb3c4b72c3c6aeebcdea69b4a01961b693e4362814cd8`；18 段视频；Qwen 162/162、运行失败 0；原生 TOPReward 72/72、各 15 前缀；文字 token 72 行。完整字段在 [`chain_verification.json`](./remote_one_session_v0_2_20261008/chain_verification.json)。 |
| Qwen 主 seal | `complete=true`；18×9；133 valid、15 schema/evidence failure、14 direction conflict；raw SHA `64826041121f876c190a0be218e0648a80a7a300f0df3ce036de0c8199f5ee08`。 |
| TOPReward 文字 seal | `complete=true`；四种文字×18 段＝72 原生结果，无原生失败；7 种文字（含三种历史封存）形成 126 条完整 15 点曲线、84 条成对结果。自动关系与反主张因无可用 TP1 命题，逐段退化为同一回退输入。 |
| 本地审计 | Qwen 180 条阶段/派生 H3 案例记录、108 条成对记录、129 条离线读出消融；先记录原答与可见帧语义审读，再看方向汇总。语义复核为 Codex AI，**未获得独立人类审读共识**。 |

压缩包哈希、下载文件及逐案例输出均位于 [`remote_one_session_v0_2_20261008`](./remote_one_session_v0_2_20261008/)。本次没有胜出方法：E/H 证据链均未修复；D2/D3 同预算覆盖与 G 保持优于 TP/H；P4 的文字敏感性得到进一步证据，但自动真假关系比较不可识别。`METHOD_FREEZE` 和真正未见 G2 仍未完成。
