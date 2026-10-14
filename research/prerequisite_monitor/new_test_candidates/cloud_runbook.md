# 既有租机快速验证执行卡（当前未连接服务器）

日期：2026-10-05。只在用户决定重新进入**之前已租**实例、且它仍可访问时执行；不创建新租机、不购买 API、不下载权重。旧状态只证明该实例过去有 RTX 5090 32 GB 和固定 Qwen3-VL-8B、Robometer 权重；当前状态未知。任何连接地址、密钥、令牌均不写入本文件或日志。

## 本地已就绪

- 两个完整新机制各有 B+/B0/U0/H−/G+/N0 六段，合计 12 段。各自 `truth/validation.json` 的 11 项全过、20 个配对续行种子方向全过、主视角可见性见 `visual_audit.md`；`truth/frozen_test.json` 已在新方法评分前冻结。
- `method_freeze_v8.json`（SHA-256 `d4af85dd5aa2b012dc156f5e36373ed208d4b9fc9e69924ed414c3f89acaed39`）固定了 v8 提示、共同解析、H0、采样、512 token/调用、主判读和模型 revision。当前 H0 只做结构一致性，不是完整命题级反事实审核。
- 仅传 `monitor_input_only_v8.zip`（SHA-256 `8e557fe06f37454f2c73586468eaaf0fc5ac6cff51d1b0ae94e31bb1fd1bf593`，约 3.1 MB，19 项）。包内为两份匿名 `s01/s02/model_input`、Monitor 代码和云端脚本；**没有** `truth/`、条件映射、后续视频、旧模型分数或本地评分器。`monitor_input_only_v8.private_audit.json` 只留本地，不上传。
- 所有旧开发视频的 manifest/实际帧可解码；2B 全类诊断已保留，B+ 和 B0 仍有错误，不将其称为方案有效证据。

## 实际上机顺序

1. 核对既有实例的 SSH、剩余租期和可用状态。若已停/失效，停止，保留所有本地产物；不新租。上传上述 ZIP **单个文件**到旧实例 `/root/autodl-tmp/monitor_input_only_v8.zip`，先在云机 `sha256sum` 对照上面的值，再解压到原有 `/root/autodl-tmp/monitor2`。解压前可用 `unzip -l` 核对 19 个成员；不上传本地 `truth/`。这一步的连接命令使用用户现有的登录方式，不能把凭据写入脚本。
2. 在旧实例依次运行 `bash /root/autodl-tmp/monitor2/experiments/prerequisite_probe/cloud_preflight_new_monitor.sh`。它只检查 GPU/磁盘、现有权重哈希、包内文件哈希和 12 段解码，不调用模型或下载。8B 不完整则停。TOPReward/Robometer 栈缺失则单列“未运行”，不阻挡仍可进行的 Monitor 测试。
3. 先运行 `bash .../cloud_run_new_monitor.sh smoke`，仅在**旧开发单段**调用 8B 的 D/P/F/D2。脚本要求 D/P/F 至少结构和逻辑有效才创建当前代码哈希的 smoke 标记。若未过，读取保留的原文和日志，停止新测试；只用旧开发例修共同接口、重新冻结版本后再说。
4. smoke 通过后运行 `bash .../cloud_run_new_monitor.sh development`，用旧开发完整六段检验 D/P/F/D2 的各类解析、错误与预算，并先取回保存。若多数核心输出仍无效或锚点/前置关系明显失真，停止新测试，记录失败；不拿新样本调提示。只有开发接口足以比较时才运行 `bash .../cloud_run_new_monitor.sh monitor`。按完整机制批次 s01→s02 运行同骨干 D/P/F、D2 与程序 H0；每次调用即写盘，保留原文、无效、弃答、失败、token、时延、峰值显存。每批结束立即核 JSONL 哈希并取回本地。之后分别运行 `... topreward` 与 `... robometer` 阶段，前提是预检确认其既有源码/权重仍在；Robometer 只能标 PR #33 dtype 兼容版。ARS 官方入口若仍不可访问，记“未运行 ARS”。
5. **在全部原始输出取回并封存后**，用本地 `score_saved_monitor.py` 和 `score_native_new.py` 读取隔离真值，按每机制完整六段报告配对排序、有效/错/弃答/运行失败分母与实际预算；再逐条核对模型引用的证据帧。不得用新测试得分改提示后继续称同一盲测。TOPReward/Robometer 为原生不同语义曲线，不跨模型数值直接比较，只比较预定排序。

## 停止与保留

若旧实例不可访问、权重缺失、8B smoke 未通过或租期不足，记录具体阶段与失败原文，停止付费推理并保留本地冻结集。源物体叠压候选 `source_stack` 已因 `C=0` 排除，不能回填。两种正式新场景分别测试源取物端和目标放置端的上方净空，但共用红色横杆视觉原型；即使结果理想，也只支持这两个受控机制，不推广为所有隐含前置条件任务。




