# 上机前运行卡 v0.1（等待现有实例端点/租期）

日期 2026-10-07。**当前只完成本地研究、无模型原型和输入预检包；未冻结胜出方法，未运行新模型，未创建 G2。**本卡不是启动服务器的授权，也不是 `METHOD_FREEZE`。只接用户现有实例，不另租、不下载或替换权重、不上传真值/条件映射/本地证据索引、不改 TOPReward/Robometer 原生代码或 P0 指标。

## 已完成的本地交付物

| 交付 | 路径/复核 |
| --- | --- |
| 18 案例原答/曲线/哈希/预期索引及证据图谱 | [`evidence_case_index.jsonl`](./evidence_case_index.jsonl)，SHA-256 `781f674b9ae86a03589764987bac0905df2b5fb7fa2bd02fcd28541a1891f320`；[`evidence_atlas.md`](./evidence_atlas.md)；[`evidence_index_manifest.json`](./evidence_index_manifest.json)。索引仅本地审计，不上传。 |
| 竞争假说、一手文献、架构决策 | [`hypothesis_register.md`](./hypothesis_register.md)、[`prior_work_to_design.md`](./prior_work_to_design.md)、[`architecture_decision_record.md`](./architecture_decision_record.md)。 |
| 接口规格与无模型原型 | [`architecture_spec.md`](./architecture_spec.md) 0.1.1；[`monitor_contract_v0.py`](./monitor_contract_v0.py)；[`local_dry_run.json`](./local_dry_run.json) SHA-256 `ae0c77af86349aca4c029163e3e51d85a9417e1d740622580d93286f82ae6ccd`。原始输入 18/18 SHA、162/162 解码帧 SHA 和 10 个抽象契约例通过。0.1.1 显式加入 `mid_second`，避免 R 中段索引歧义。 |
| 仅许可输入的可复核预检包 | [`machine_preflight_input_only_v0.1.1.zip`](./machine_preflight_input_only_v0.1.1.zip)，4,863,093 字节，SHA-256 `c4671c5d0ac0e23126d85ccbe98da7ec282dd1918d4f5834140c6dfa5df7b12d`；内部只有匿名两组目标+视频输入 ZIP、schema 代码、README、包清单；已查无 truth/condition/answer/score 文件名。它**不含模型提示或可运行方法**。0.1.0 旧包保留作版本记录，不作为当前包。 |
| 封存源复验 | `python research/prerequisite_monitor/fresh_server_20261007/local_results/verify_final.py` → 原生 seal 3、P1 seal 3、哈希 20、P2 540 点精确一致；`python research/prerequisite_monitor/fresh_server_20261007/local_results/verify_additional.py` → 追加 seal 5、包 5、文件哈希 221、模型输出 90、失败 0。 |

`D:/monitor2` 不是 Git 仓库，因此本轮不能提供项目提交哈希；新文本/脚本由上述文件 SHA、输入 seal 和复建命令定位。原生代码本地固定提交见 [`code_trace_update.md`](../architecture_next/code_trace_update.md)，模型权重身份必须在新实例上重新只读核对。

## 待验证假说和先后门槛

1. H1/H2：自动相关关系的视觉事实是否能在 0/中/14 秒正确，事实正确后能否把 `goal_done` 与 `can_continue` 分开；只要状态仍错，先解决定位/回看。
2. H3/H4：P4 的任务文字效应是否由真实前置语义而非长度/迎合驱动；任何变体须同时保住 G，九条件全报。错误关系只做开发抗误导诊断，不进入正式推理。
3. H5：新增机制是否排除替代合法路线；无法由主视角决定时允许 unknown 并计入覆盖率。
4. H6：R 的中段正向是否在末段被撤销，同时 G 完成优先；需和 N_b 静止锚对照。

先在本地审定一个最小候选及同预算 D/D2 的提示、解析、帧集合、token 上限与停止规则，生成真正 `METHOD_FREEZE` 和哈希后，才能跑模型比较。目前 ADR 只选共同接口，不假装已有架构胜者。

## 预计调用与时间包络（按历史实测估，实例到手后重估）

历史 P6 18 次 Qwen 直问原答中位 2.75 秒、最大 3.59 秒；P5 visual 中位 3.64 秒、最大 4.56 秒，必要性中位 2.78 秒。它们不含新实例加载、封存、传输时间。保守规划按 **每新视觉调用 10 秒 + 每阶段最多 5 分钟加载/初始化**，不是保证上限。

| 阶段 | 新模型调用上限 | 保守操作预算（含加载/封存，未含下载验封缓冲） | 只在何时执行 |
| --- | ---: | ---: | --- |
| 只读实例/权重/媒体身份预检 | 0 | 5–10 分钟 | 用户给端点/租期后第一步；不合即停。 |
| 旧格式输入 smoke 与 1 段开发 pilot | 1–2 | 5–8 分钟 | 读写路径隔离和实际显存/延迟核准后。 |
| D1 与合并 T/P1，一调主层 | 36（18×2） | 约 12 分钟 | 提示与解析已冻结、pilot 过门后。 |
| 若一调不能区分：D2 与 T/P2，同等二调 | 最多 72（18×2×2） | 约 22 分钟 | 先写明此轮能推翻哪条假说；否则不跑。 |
| H4 等长/真假关系开发诊断 | 最多 54 个 TOPReward 原生视频作业（每作业 15 前缀） | 约 15 分钟，需 pilot 重估 | 只有文字机制决定路线时跑；P4 结果已足够则跳过。 |
| 若端点对但价值错：F/H 与同预算 D3 | 最多 36 额外视觉调用 | 约 12 分钟 | 有明确错例且租期充分才跑；否则延期。 |

每项启动前重新以 pilot 外推剩余时间，并**预留至少 10 分钟**给原始输出封存、下载和逐文件验哈希；无法满足即不启动该项。实际视觉/text token、显存、失败率和耗时都入账，不能仅以名义调用次数声称预算完全相等。以上是候选包络，不是要在一个短租期内全部顺序完成。

## 到手实例后的顺序

1. 接收用户提供的**现有**端点、租期与可用工作目录。只读查 GPU/显存、磁盘、框架、TOPReward/Robometer 代码提交和工作树、Qwen/Robometer 权重配置及分片 SHA、旧输入和新上传包 SHA；任一身份不符停下报告。不从网络拉权重或更换模型。
2. 若需传包，仅传不含真值的输入/冻结代码；运行进程不接触本地索引、条件表、审读图和续行真值。上机提示/代码先单独封存哈希，不能边看开发答边暗改。
3. 最小 smoke → pilot 实测时长 → 核算剩余租期/10 分钟缓冲 → 完整阶段。原答、配置、实际帧、token、耗时、失败和空结果先封存，逐文件验哈希后本地揭盲评分；不覆盖 P0。
4. 开发方法确定后才生成 `METHOD_FREEZE`，再独立制样并审查真正未见 G2。现有 A/B 与旧场景永远只算开发材料。

**当前等待的信息：**现有实例的端点、租期、工作目录/权限。收到前不进行任何上机调用或上传。
