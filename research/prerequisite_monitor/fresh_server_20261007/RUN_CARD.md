# 2026-10-07 全新前置条件场景：现有服务器执行卡

本目录只完成了本地预制；服务器尚未开启。G1 已批准使用用户开启的现有服务器。不得另租、下载或替换权重、修改官方方法，且真值与条件映射只保留本地。整个运行按 P0→P1→P2→P3，所有额外诊断均为探索性，不称 G2。

## 已冻结的传输件

| 文件 | SHA-256 | 用途 |
| --- | --- | --- |
| `fresh_scenes_20261006/access_gate/dev_v2/model_input.zip` | `3e57af3072091bafbc10b81eea17d8ebd597337458cae5edd6b8433ab5842e78` | A 九段匿名模型输入 |
| `fresh_scenes_20261006/support_surface/dev_v2/model_input.zip` | `3124b5117820707f3458696d4a553f0fee27d41aa969d45eca78bfd84b6cfc9d` | B 九段匿名模型输入 |
| `model_side_code.zip` | 见同目录 `model_side_code_manifest.json` | 字节一致的原生 runner、导入闭包、九段预检、封存器、一段旧输入 smoke、六个旧权重分片哈希 |
| `optional_p1_code.zip` | 见同目录 `optional_p1_code_manifest.json` | P1 独立 Qwen3-VL 问答与封存器；P0 本地备份后才上传 |
| `p3_static_input/{access_gate,support_surface}/model_input.zip` | 见 `p3_static_input/build_report.json` | P3 各四段匿名静态画面；本地映射不上传 |

冻结总清单哈希 `be2af5aaa8afe8d32a1e5481631f190c6748b825ea7d0c8027a09d873a60534b`。最新本地复验命令、退出码、时间和上述实际哈希保存在 `local_logs/local_preflight.json`。四个 P0 dry run 每个 `9` 个视频输入、`0` 个模型结果；P1 两阶段各 `18` 个输入；四个 P3 dry run 每个 `4` 个输入。原生 runner 副本 SHA-256 `11052370076b99afeb35c84d60805e38540c2dbf739565cdbdfa2a3254351083`，与冻结源字节一致。

## 开机后，上传前的只读门禁

先从服务商界面记录**实际到期时间及剩余分钟**，转换为明确的 UTC 截止时间。只连接用户给出的现有 SSH 端点。保存 `date -u`、`TZ=Asia/Shanghai date`、`hostname`、`whoami`、`nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits`、`df -h /root/autodl-tmp/monitor2`、两环境 Python 路径与版本、两源码仓库 `git rev-parse HEAD`、Robometer `git diff -- robometer/utils/save.py` 的 SHA、两个现存 checkpoint 的 revision 路径、`config.json` SHA 和六个分片的存在/大小。只读结果保存在新的本地 `remote_readonly_preflight.txt`。若模型/输入身份不符、GPU 空闲显存不足约 24 GiB、磁盘不足 5 GiB、或租期不足主实验估时加 10 分钟下载缓冲，停止。

预期身份：TOPReward `4877a0ee5098cbec18485125466631b1dcc4a573`；Robometer 基础提交 `352d160389daa964788de1ec933d1925f3a6de4f`；兼容补丁 diff SHA `b560da190b4dccaa405684beb2e33a5950fefd035983dc98ae9d02406b9d2fac`；8B revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`；Robometer revision `beef63bc914c5c189329d49c6d712d96d632aa34`。配置及六个分片的预期 SHA 在 `model_side/pilot_pkg/preflight_fresh_server.py` 和 `official_weight_hashes.json`，上机详细预检会逐项比较。旧输入 smoke 目录应先只读确认，例如已有 `/root/autodl-tmp/monitor2/single_scene_pilot/flat_red_v1_cache_fix/model_input`；路径变化只记录并调整参数，不替换数据或权重。

## P0 主实验

只在只读门禁通过后建立**全新**远端目录，例如 `/root/autodl-tmp/monitor2/fresh_prerequisite_runs/20261007_dev_v2_01/incoming`。上传 A、B、`model_side_code.zip` 和 `run_remote_p0.sh`，把前三者命名为 `access_gate.zip`、`support_surface.zip`、`model_side_code.zip`。本地与远端均核四个文件 SHA；运行脚本本身的最新 SHA 见 `local_logs/local_preflight.json`。传输件不含 `truth/`、`condition_map.json`、原型视频、旧结果或本地评分器。

在远端执行 `bash run_remote_p0.sh <全新运行根目录> <租期UTC截止时间> <只读核实的旧model_input目录>`。脚本详细只读复核资源/提交/补丁/配置/六个分片及 A/B ZIP，并在模型调用前用 Robometer 原生帧提取函数核对 18 段×15 帧像素哈希；随后对旧输入各做一次原生调用 smoke。A/B 各方法四个 dry run 通过后，顺序执行 36 次原生调用。每个单元独立 stdout/stderr、exit code、原始曲线及失败记录，任何时段都不同时加载两模型。脚本每次 GPU 项目前检查预计耗时加至少 600 秒下载缓冲，不足时停止并保留部分封存。`raw_seal.json` 位于 `raw/` 外；`complete` 或 `complete_with_failures` 才可评分。

**先下载** `raw/`、`raw_seal.json`、`seal_summary.json` 和输入/代码 SHA 日志到全新本地结果目录；保留远端副本。使用本地原冻结 `model_input` 运行：

```powershell
$env:PYTHONPATH='D:\monitor2\research\prerequisite_monitor\fresh_server_20261007\model_side'
& 'D:\monitor2\.venv\Scripts\python.exe' -m pilot_pkg.seal_fresh_batch `
  --raw-root '<本地结果目录>\raw' --seal '<本地结果目录>\raw_seal.json' `
  --access-input 'D:\monitor2\research\prerequisite_monitor\fresh_scenes_20261006\access_gate\dev_v2\model_input' `
  --support-input 'D:\monitor2\research\prerequisite_monitor\fresh_scenes_20261006\support_surface\dev_v2\model_input' --verify
```

只有输出状态为 `complete` 或 `complete_with_failures`、本地逐文件哈希复核通过后，才用**本地** `score_fresh_batch.py` 和两个 `truth/condition_map.json` 评分。评分结果另写 `analysis_p0.json`，不得回写 raw。每单元保留九条 15 点原始曲线、六对原始差值与方向、R 中段/末段、G 控制、平局/失败/不可评分。P0 备份完成后，可将本地核得的 seal SHA 写成远端 `p0_local_verified.sha256` 标记；额外任务脚本会核该值与远端 seal 一致。标记不含真值。

## P1→P2→P3 额外诊断

每项开始前重新读取服务商剩余租期。仅当预计耗时加至少 10 分钟下载/核验缓冲足够时，才上传/运行所需材料。`run_remote_extra.sh` 一次只运行 `p1`、`p2` 或 `p3`，且要求 P0 本地验封标记。

- **P1**：在 P0 本地备份后上传 `optional_p1_code.zip`，远端核 SHA。脚本先对两阶段各做无模型 dry run，然后 A/B 各一段视觉 pilot；pilot 失败立即停止该诊断。随后对全部 18 段视觉事实独立提问并封存，再对全部 18 段必要性独立提问并封存。两轮不会共享模型回答。原文、解析状态、合法九帧哈希、提示词哈希、token、耗时和显存单列。先人工审读原答事实/理由/引用帧，再本地揭盲对照。它只是另行提示的基础 VLM 诊断，不代表 TOPReward/Robometer 内部轨迹。
- **P2**：P1 已结束或无法运行，且租期允许时，在全新 `extra/p2` 目录重跑相同 36 次原生调用；独立封存、下载、本地验哈希。用 `extra_reports.py --mode p2` 比较每段逐点差、六对方向翻转及重复失败。不得挑较好一轮。
- **P3**：仅 P0、P1、P2 各自安全备份并有时间时，上传两个 P3 匿名 ZIP；条件映射 `mapping_local_only.json` 不上传。四个 dry run 后执行两机制×两方法×四段，`--expected-count 4` 独立封存、下载、复核。用 `extra_reports.py --mode p3` 只比较第 15 个原始值的 `N_o-N_b`、`S-N_b`、`G-N_o`；这只是分布外静态画面探查。

P3 脚本另需三个无真值的本地验封标记：`p1_full_visual_local_verified.sha256`、`p1_full_necessity_local_verified.sha256`、`p2_local_verified.sha256`。每个文件只写对应已下载并本地复核的 `raw_seal.json` SHA-256；脚本逐一和远端 seal 核对。若 P1 或 P2 未完成/未备份，跳过 P3。

租期最后 10 分钟不再启动 GPU 单元。优先下载和验封 raw、日志、封存；远端副本至少保留至本地复核通过。最终写明完成、失败、平局、未启动项以及实际耗时。本次仅开发实验，正式 G2 未见验证须另行冻结配置、样本量、指标和停止规则。
