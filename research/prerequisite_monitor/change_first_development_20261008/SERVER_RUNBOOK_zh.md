# S1 上机运行卡：只在用户开机并确认当前连接后执行

> 历史运行卡；S1 已执行，详见 `S1_PILOT_REPORT_20261009_zh.md`。以下 120 分钟示例是原方案，本次实际按用户最初的一小时窗口收紧并在获准延时后完成，总请求仍未超过 96。

## 身份和硬上限

- 本地包：`D:\monitor2\research\prerequisite_monitor\change_first_development_20261008\packages\pilot_v6.zip`
- SHA-256：`5a5c7070ee8673fde793cf2dfc4c0669367f99eca915158f0b8d1eaff4dd7306`
- 匿名已暴露开发视频：A/B 各 E、H、R、G，共 8 查询，固定截至 14 秒。三臂 D4/K4/C4，96 个名义槽；正常共享 V1 时预计 80 次真实请求。**硬上限 96 次请求，远端预检起累计不超过 120 分钟，至少留 15 分钟封存。**
- 不使用旧 SSH 地址或端口。用户开机后核对当前 SSH 别名/地址、端口及可用窗口；无需在聊天发送密码。若卡被占用，不杀进程、不加载模型。

## 只读预检和本次变量

用户给当前连接信息后，上传包至新建远端目录。以下变量只在已核实的当前远端会话中赋值；不要粘贴旧模型路径当事实：

```bash
cd <NEW_EMPTY_RUN_DIRECTORY>
sha256sum pilot_v6.zip
mkdir bundle
unzip -q pilot_v6.zip -d bundle
cd bundle
RUN_PY=<VERIFIED_EXISTING_PYTHON>
RUN_MODEL=<VERIFIED_EXISTING_QWEN3_VL_8B_SNAPSHOT>
"$RUN_PY" research/prerequisite_monitor/change_first_development_20261008/verify_bundle.py --bundle ../pilot_v6.zip
"$RUN_PY" research/prerequisite_monitor/change_first_development_20261008/server_preflight.py --model "$RUN_MODEL" --workspace . --output preflight_s1.json
```

先审阅 `preflight_s1.json`：当前 GPU 型号和其它计算进程、空闲显存建议至少 24 GiB、结果盘至少 15 GiB、Python/torch/transformers 版本、已有 config/processor 与四个权重分片 SHA。和历史身份记录比较时只作身份核对；型号、路径、空闲量须以当前只读结果为准。条件不足停止，保留预检输出。

## 首块、检查、再续完整块

确认预检合格后从预检文件读取**同一个**窗口起点。第一条真实视觉请求属于 96 次上限，不额外 warmup。先运行一个完整三臂查询块，检查十条原答、各槽 schema、输入/输出 token、图像句柄、GPU 占用与耗时；出现系统性故障停止并封存。满足条件才用同一输出目录和同一窗口续跑剩余七块：

```bash
RUN_START=$("$RUN_PY" -c 'import json; print(json.load(open("preflight_s1.json"))["window_start_epoch"])')
bash research/prerequisite_monitor/change_first_development_20261008/run_server_pilot.sh \
  --python "$RUN_PY" --model "$RUN_MODEL" --input ./model_input/pilot_v5 \
  --output ./runs/s1_v1 --preflight-report ./preflight_s1.json \
  --window-start-epoch "$RUN_START" --max-requests 96 --max-queries 1 \
  --max-wall-minutes 120 --seal-buffer-minutes 15

# 只读检查 runs/s1_v1/requests.jsonl、results/、progress.json、GPU 占用。
# 若无系统性故障且剩余窗口允许，才运行：
bash research/prerequisite_monitor/change_first_development_20261008/run_server_pilot.sh \
  --python "$RUN_PY" --model "$RUN_MODEL" --input ./model_input/pilot_v5 \
  --output ./runs/s1_v1 --preflight-report ./preflight_s1.json \
  --window-start-epoch "$RUN_START" --max-requests 96 --max-queries 8 \
  --max-wall-minutes 120 --seal-buffer-minutes 15
```

每次脚本退出均生成一个带时间后缀的 `runs/s1_v1_results_*.tar.gz`，保留第一块封存与续跑封存；脚本 `timeout` 保证为封存预留窗口。当前输出存在已发无原答的 ambiguous 请求时不能自动重发；先查是否任务仍在运行，仍不明则作为可能已消耗请求处理。

## 下载、复核与释放

记录服务器 `sha256sum runs/s1_v1_results_*.tar.gz`，通过**当前已核对 SSH 端口**下载到新的本地 `runs/` 子目录。逐包执行：

```powershell
& 'D:\monitor2\.venv\Scripts\python.exe' 'D:\monitor2\research\prerequisite_monitor\change_first_development_20261008\collect_and_seal.py' --verify <DOWNLOADED_ARCHIVE> --expected-sha256 <SERVER_REPORTED_SHA256>
```

本地核对封存成员、请求数、失败/未执行、原答及成本；检查本任务没有残留运行进程后，才告知用户服务器可释放。不要擅自关闭共享实例。S1 后在本地写 `S1_PILOT_REPORT_zh.md`，把接口可用与方法有效严格分开；S2及更大实验不自动启动。
