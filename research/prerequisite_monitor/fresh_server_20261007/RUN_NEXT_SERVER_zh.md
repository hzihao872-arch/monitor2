# 下次开机：P4/P5 即跑运行卡

状态：2026-10-07 本地已准备，**尚未运行 P4/P5 模型**。现有服务器已按用户通知关闭。只使用已经租用的实例和现存权重；不要在日志、脚本或本文写入 SSH 密码。旧 P0–P3 结果已在 `local_results/`，本次新增均为开发诊断。

## 开机前已冻结的材料

- [实验设计](TAIL_WINDOW_P4_PLAN.md)：P4 先跑 TOPReward 的 neutral、causal_fact、credit_rule 三个文字变体；P5 再跑 targeted visual 与 future-route 两个独立问答。结果全部保留，不在中途改提示或主指标。
- `p4_inputs/build_manifest.json`：六个匿名输入包的逐文件 SHA；构建器 `build_p4_inputs.py --verify` 已核六包视频与原视频字节和逐帧 RGB 哈希一致，只有同机制统一指令变了。
- `p4_p5_upload.zip`：**SHA-256 `d9fe7ba669d5f9362facae95fbeb2882ec42d565261dcf7c00491119377e070c`**，仅含六个模型输入 ZIP 和 `p4_p5_model_code.zip`；无 truth、condition_map 或 P0 分数。
- `run_remote_p4_p5.sh`：每次只跑一个完整任务，先核 P0 seal、官方提交、Qwen 配置及四个权重分片、GPU、磁盘及包哈希；每任务独立目录、dry run、pilot、完整原答、seal 和打包。接受服务商实际到期 UTC 参数，至少留 600 秒下载缓冲。上一任务须已在本地验封，下一任务才可开始。
- `collect_p4_p5.ps1`：下载任务包、核压缩包 SHA、本地复验 raw seal 和输入包，再将 seal SHA 标记传回服务器。不会自动评分或读取真值。

## 1. 开机后先读服务商到期时间

确认仍是同一实例与 SSH 端点。把服务商显示的上海时间转换为 UTC，作为下面的 `<到期UTC>`，格式如 `2026-10-07T13:00:00Z`。此处示例不是实际到期时间；脚本绝不可用旧保守截止 `12:40 UTC` 代替。若服务商不显示准确到期时间，先向用户取得，不能猜测时限。

本机 PowerShell，在 `D:\monitor2` 执行上传；SSH 会交互要求密码，不把密码写进命令：

```powershell
$root = 'D:\monitor2\research\prerequisite_monitor\fresh_server_20261007'
$dest = 'root@connect.bjb2.seetacloud.com:/root/autodl-tmp/monitor2/fresh_prerequisite_runs/20261007_dev_v2_01/incoming/'
scp -P 36053 "$root\p4_p5_upload.zip" "$root\run_remote_p4_p5.sh" $dest
```

再登录，只读核 `date -u`、GPU、磁盘、P0 `raw_seal.json` 和 `$RUN/code` 是否仍在。脚本本身会重复检查身份与哈希；任何检查失败即停，保留已有文件。若关机后原运行根目录丢失，不要假装是同一个 P0 后续实验。

## 2. 固定执行顺序

在服务器 shell 中先进入持久会话 `tmux new-session -A -s monitor2_p4_p5`；断线可用同一命令重新接入。把 `<到期UTC>` 替换为**实际**服务商到期 UTC。每行跑完后，立即到本机执行对应收集命令；收到“Verified”后才跑下一行。每次开始前脚本检查余时；若失败或不足，停止并记录未运行项，不跳过条件挑有利结果。

```bash
RUN=/root/autodl-tmp/monitor2/fresh_prerequisite_runs/20261007_dev_v2_01
bash "$RUN/incoming/run_remote_p4_p5.sh" p4-neutral <到期UTC>
bash "$RUN/incoming/run_remote_p4_p5.sh" p4-causal_fact <到期UTC>
bash "$RUN/incoming/run_remote_p4_p5.sh" p4-credit_rule <到期UTC>
bash "$RUN/incoming/run_remote_p4_p5.sh" p5-visual <到期UTC>
bash "$RUN/incoming/run_remote_p4_p5.sh" p5-necessity <到期UTC>
```

本机在每个对应任务后执行，`-Endpoint` 与 `-Port` 仅在服务商更换端点时改；密码仍交互输入：

```powershell
& 'D:\monitor2\research\prerequisite_monitor\fresh_server_20261007\collect_p4_p5.ps1' -Task p4-neutral
& 'D:\monitor2\research\prerequisite_monitor\fresh_server_20261007\collect_p4_p5.ps1' -Task p4-causal_fact
& 'D:\monitor2\research\prerequisite_monitor\fresh_server_20261007\collect_p4_p5.ps1' -Task p4-credit_rule
& 'D:\monitor2\research\prerequisite_monitor\fresh_server_20261007\collect_p4_p5.ps1' -Task p5-visual
& 'D:\monitor2\research\prerequisite_monitor\fresh_server_20261007\collect_p4_p5.ps1' -Task p5-necessity
```

终端断开时，先接回 `tmux` 并查对应 `$RUN/extra/p4/<变体>` 或 `$RUN/extra/p5/<阶段>` 是否有 `raw_seal.json` 与 `evidence.tar.gz`。不要盲目重跑到同目录；原始失败和部分输出应保留。

## 3. 本地揭盲评分

只有对应 raw seal 本地验证通过后，运行本地评分器。P4 每个变体分别传 `score_p4.py --variant <变体> --raw-root <local_results/p4/变体/raw> --seal <.../raw_seal.json> --input-root <p4_inputs/变体> --truth-root <fresh_scenes_20261006> --p0-analysis <local_results/p0/analysis_p0.json> --output <新文件>`。它列出九条件全曲线、六对、与 P0 差值变化，不能只展示转正项。P5 两阶段都完整验封后再运行 `score_p5.py`，报告两机制各九段状态/前瞻答复并人工逐条核引用帧。

P4 只证明原生 TOPReward 对**改变后的任务文字**是否敏感，不能当作原始“仅给最终目标句”的成绩。P5 独立 Qwen 提示的结果不能代表 TOPReward/Robometer 内部推理。两者都不能补作 G2 未见验证；下一次正式跨场景结论须先冻结新几何、盲审、指标和停止规则。
