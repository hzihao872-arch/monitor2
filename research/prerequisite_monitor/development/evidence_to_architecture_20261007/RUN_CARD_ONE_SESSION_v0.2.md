# 现有实例单次上机运行卡 v0.2

状态：**本地准备中；未上传、未调用模型、未产生新结果。** 这张卡执行[开发实验预登记](./ONE_SESSION_EXPERIMENT_FREEZE_v0.2.md)，不是 G2。现有实例的端点、租期、持久目录和权限由用户提供后填写。不得另租实例、下载/替换权重、上传真值或更改 TOPReward/Robometer 原生代码。

## 本地交付与隔离

| 项目 | 当前文件 |
| --- | --- |
| 许可输入加模型侧运行代码 | [`one_session_model_side_v0.2.0.zip`](./one_session_model_side_v0.2.0.zip)；SHA 见同目录 [`one_session_package_manifest.json`](./one_session_package_manifest.json)。包内没有审读索引/条件映射/真值。 |
| 九阶段 Qwen 调用、原答日志、续跑 | [`one_session_suite_v0_2.py`](./one_session_suite_v0_2.py)，固定 18×9 调用，其中 V0 是不看目标的视觉事实诊断；同配置重复调用只跳过已完整写入行。 |
| 无真值的原始封存 | [`seal_one_session_v0_2.py`](./seal_one_session_v0_2.py)；失败或租期中断可封部分输出。 |
| TOPReward 文字诊断与封存 | [`build_text_probe_inputs_v0_2.py`](./build_text_probe_inputs_v0_2.py)、[`seal_text_probe_v0_2.py`](./seal_text_probe_v0_2.py)；已封存 P0/P4 不覆盖。 |
| 本地揭盲和人审模板 | [`audit_one_session_v0_2.py`](./audit_one_session_v0_2.py)、[`audit_text_probe_v0_2.py`](./audit_text_probe_v0_2.py)；**不在上传包内**，只在下载验封后使用。 |
| 一步运行脚本 | [`run_existing_instance_v0_2.sh`](./run_existing_instance_v0_2.sh)；同版脚本在模型侧包内，先只读核 GPU/磁盘/权重/官方提交。 |

现有旧 P0/P4/P5/P6、逐案证据、文献与构念问题分别见 [`evidence_atlas.md`](./evidence_atlas.md)、[`hypothesis_register.md`](./hypothesis_register.md)和[`prior_work_to_design.md`](./prior_work_to_design.md)。G2 仍只有[制样与准入计划](./G2_sampling_plan.md)，没有制成或运行。

## 在提供实例前必须填写

- 现有实例的 SSH/其他端点、租期结束 UTC 时间、持久工作目录、可执行 Python、已存在的 Qwen3-VL-8B checkpoint 与官方 TOPReward checkout 路径。
- 实际可用 GPU 显存、磁盘及账号权限。脚本要求至少 21 GB 空闲显存、5 GiB 空闲磁盘；旧实例的 Qwen config/四分片 SHA 和 TOPReward commit 必须匹配。若身份不同，停下核实，不换权重。
- 这次完整矩阵计划 **pilot 18 + 开发 162 = 180 次 Qwen 视觉调用**（开发中 18 次 V0 只收视觉事实，144 次是方向候选）；随后 **TOPReward pilot 1 + 开发 72 = 73 个原生视频作业，即最多 1,095 个原生前缀**。这些是调用量上限，输出失败也计入实际调用；每段实际 token/耗时在 raw 中逐次记账。

历史 P5/P6 的 Qwen 短问单次约 3–5 秒，本次长结构 JSON 和最多 896 token 可能更慢。预留较保守的 **Qwen pilot+主矩阵 45–60 分钟、四套 TOPReward 约 30–40 分钟、身份检查/封存/下载至少 15 分钟**；若希望一次跑齐，建议现有租期剩余**约 2 小时**。这不是保证时长；pilot 后必须用真实耗时重估。若剩余租期短，脚本按阶段门槛停止并封存已跑内容，报告哪些对照未运行，不挑个别 E 的好结果充数。

## 收到端点后顺序

1. 在本地复验包 SHA 和模型侧白名单，再把这个包传到用户现有实例的持久目录。传输只包含许可输入、提示、代码和哈希。不要传 `evidence_case_index.jsonl`、本地分析、评分脚本、truth、条件表或 G2 审读材料。
2. 用只读命令确认租期、GPU/磁盘、权重 config/四分片 SHA、官方 TOPReward commit、旧模型环境；身份不合即停。运行脚本会再次核验。
3. 从上传包解出运行脚本（或另传同 SHA 的本地脚本），在 `tmux` 中启动并保存终端日志。参数顺序：包 ZIP、一个**不存在的新持久输出目录**、既有 Qwen 权重目录、租期结束 UTC、官方 TOPReward 仓库、既有 Python 解释器、包 SHA。例如：

   ```bash
   unzip -p /persistent/one_session/one_session_model_side_v0.2.0.zip run_existing_instance_v0_2.sh > /persistent/one_session/run_existing_instance_v0_2.sh
   tmux new-session -d -s monitor-v02 'bash /persistent/one_session/run_existing_instance_v0_2.sh /persistent/one_session/one_session_model_side_v0.2.0.zip /persistent/one_session/results_v02 /existing/qwen/checkpoint 2026-10-08T12:00:00Z /existing/TOPReward /existing/python EXPECTED_PACKAGE_SHA > /persistent/one_session/run_v02.log 2>&1'
   ```

   上述路径和结束时间是**占位示意**，必须用用户现有实例的实际值替换；不要照抄虚构路径。
4. 脚本先对 18 段做无模型帧/hash dry run，再做两段全阶段 pilot（18 调）；随后完整 162 调。所有 raw 每条 fsync，pilot 单独保存，不把它并进主表。实际耗时/显存若超出剩余租期，按预登记规则停止并封部分输出。
5. 完整 Qwen 原答封存后，脚本从 TP1 **原答本身**生成自动关系文字，运行四套独立 TOPReward 文字诊断，每套全九条件、两个匿名组；每个原生作业有 15 点曲线和哈希。任一文字变体运行不全则标 partial，不只挑改善的 E。
6. 先下载 `evidence.tar.gz` 与 `.sha256`，并另存终端 `run_v02.log`；本地逐文件核对 Qwen/TOPReward seal 和包 SHA，再执行本地 `audit_one_session_v0_2.py` 与 `audit_text_probe_v0_2.py` 生成全案表、配对表、读出消融、文字曲线对照和空白语义审读表。人审完成前，不称“证据正确”或“架构胜出”。

## 结果判读门槛

- 同调用层内比较 D1/T1/P1/TP1、D2/TP2、D3/H3；actual token、延迟和显存一起报告。H3 若只因大量 unknown 提升正确率即拒绝。
- 必须有 18 案完整表、六类配对胜/平/负/未知、E/H/G/R 控制和 Robometer 承托板 E 3/3 正反例。P4 的 A G 失配单列，不能仅凭 E 增益接受文字注入。
- first error 只在可审读证据支持时标为可见事实、绑定/端点、目标相关性、续行/替代路线、进度读出或证据不足；原生数值曲线不可凭黑箱分数定位内部模块。
- 先封存再揭盲；开发胜者选出后另建 `METHOD_FREEZE`。现有 A/B 和旧场景永远不作为 G2。真正未见 G2 要通过独立可观察性和替代路线准入，不能因为租期剩余而临时凑样。
