# 隐含前置动作：第一阶段开发探针实际结果

日期：2026-10-04。结论状态：**六段 TOPReward 原版结果已取得；Robometer 严格未修改原版因推理 dtype 错误尚无结果，另取得六段官方权重加 PR #33 dtype 兼容版结果。单模板开发探针不能证明普遍问题。**

## 接续执行：原版基线排障（2026-10-04）

先只看六个编号视频的实际解码画面并记录于[视觉观察](../experiments/prerequisite_probe/artifacts/blind_visual_observations_20261004.json)和[编号帧表](../experiments/prerequisite_probe/artifacts/blind_model_input_sheet.png)，随后才打开 `truth/` 中的逐条记录。0001 红块离开托盘、0002 操作后仍留在托盘、0003 红块在托盘外搬移、0004 红块进入托盘、0005 蓝块进入托盘、0006 静止，均能从主画面辨认。由于按要求先读了本报告、其中已披露条件映射，这不是盲审，也不补足缺失的第二名独立复核者。再次运行 `audit_inputs`，六个编号输入均通过。按 Robometer 官方 `extract_frames` 的 Decord 0.6.0 逻辑读取 1 FPS MP4，六段均为 15 张 640×480 RGB 图；[逐帧 SHA-256](../experiments/prerequisite_probe/artifacts/model_results/robometer_decoded_frames.json)与此前 OpenCV 解码记录六段逐帧完全一致。

官方捷径核查：

- [TOPReward README](https://github.com/TOPReward/TOPReward/blob/main/README.md)提供本地单视频入口；[官方 QwenClient](https://github.com/TOPReward/TOPReward/blob/main/topreward/clients/qwen.py)的 `compute_instruction_rewards_for_prefixes` 才是本次固定的原生逐前缀评分。QwenClient 初始化固定使用 `flash_attention_2` 和 `device_map="auto"`，评分输入固定 `.to("cuda")`。官方 Qwen3-VL [模型卡](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct)把 FlashAttention 2 列为推荐，而非骨干本身的唯一注意力实现；但本次调用要保持该官方客户端代码原样。[LeRobot 的 TOPReward 端口](https://huggingface.co/docs/lerobot/main/topreward)称其提示和单次 log-prob 与上游匹配，属于另一个实现；若使用须单列端口结果。
- [Robometer README](https://github.com/robometer/robometer#-inference)、[官方本地脚本](https://github.com/robometer/robometer/blob/main/scripts/example_inference_local.py)及[模型卡](https://huggingface.co/robometer/Robometer-4B)确认同一个视频入口会保存逐帧 progress 和 success 概率。固定 checkpoint 的 `config.yaml` 为 BF16、无量化、`use_unsloth=true`，原脚本最终将完整模型 `.to(device)`。官方演示 Space 的前端在调用服务端前还构造占位 `target_progress` 与 `success_label`，且只返回图与终值，不适合作本次“只有视频与指令、保留原始数组”的捷径。[LeRobot 的 Robometer 端口](https://huggingface.co/docs/lerobot/main/robometer)有独立转换权重及默认 8 帧上限，不能冒称本次固定的原仓库/原 checkpoint/15 帧入口。
- Robometer 仓库还有[未合并的推理 dtype 修复 PR](https://github.com/robometer/robometer/pull/33)及[相关公开问题](https://github.com/robometer/robometer/issues/38)：其他使用者报告原 checkpoint 的 Unsloth 加载后出现 BF16/FP32 混合导致 forward 崩溃。本次严格原版运行也复现该错误；原版失败日志和单列的 PR #33 兼容版见下文。

本机排障历史：已建立独立 Python 3.10.19 环境 `.venv-robometer`；CUDA 2.8.0 的 Windows wheel 下载长时间未完成，曾改用 CPU wheel 检查导入路径。Hugging Face 常规全文件/Xet 下载停滞且一度清零约 1.59 GB 的 `.incomplete` 文件；后来用[固定 revision、HTTP Range 续传并按 SHA-256 校验的下载脚本](../experiments/prerequisite_probe/download_official_weights.py)，最终在云机完成三套权重。[本机 TOPReward 下载日志](../experiments/prerequisite_probe/artifacts/topreward_http_resume.log)、[Robometer 下载日志](../experiments/prerequisite_probe/artifacts/robometer_http_download.log)及[Qwen3-VL-4B 基座日志](../experiments/prerequisite_probe/artifacts/robometer_base_qwen_download.log)保留了早期失败。本机 RTX 4060 Laptop 8 GiB，检查时仅约 6 GiB 显存和 2.4 GiB 物理内存空闲；未把它推断为唯一失败原因。

Python 3.10 的 CPU 环境现已装入 PyTorch 2.8.0、Unsloth、Transformers 4.57.6 和原仓库。原脚本 `--help` 导入链逐一排除了 matplotlib、uvicorn、tensorboard、codetiming、sentence-transformers 等缺包。`torchao==0.18.0` 与 PyTorch 2.8 产生 `ScalingType` 导入错误；按[仓库未合并的依赖修复 PR](https://github.com/robometer/robometer/pull/39)将环境依赖限制到 `torchao==0.17.0` 后，原脚本继续到 Unsloth，最终明确报 `Unsloth cannot find any torch accelerator? You need a GPU.`，见[完整导入尝试](../experiments/prerequisite_probe/artifacts/robometer_py310_import_attempt7.log)。这说明 CPU wheel 可用于路径诊断，但不能给出原版 Robometer 分数；GPU 版本仍需可用 CUDA 安装和足够显存。

用户最后选用 SeetaCloud RTX 5090 32 GB（页面标价 ¥3.03/小时），而非早期讨论的 Runpod A40 报价。上传的[编号视频和无标签清单压缩包](../experiments/prerequisite_probe/artifacts/model_input_only.zip) SHA-256 为 `a17e0bb91f649a5ca514c9231cd01aba4fc9331a0bbf75bba598f5603b918c88`；权重、推理命令、日志与结果均已取回本机，专用 SSH 公钥已从云机移除。云服务计费是否停止以租机平台实例状态为准。

## 场景决定与视频

先在 ManiSkill 3.0.1 / SAPIEN 3.0.3 中实现窄口隔间、固定侧壁和栅格顶盖。其[主视角首帧](../experiments/prerequisite_probe/artifacts/narrow_initial.png)看不到蓝方块，未过预定可见性门槛；在读取任何模型输出前切换为单格绿色托盘被红块占据的备选场景。[备选首帧](../experiments/prerequisite_probe/artifacts/cell_initial.png)和[模型输入帧接触表](../experiments/prerequisite_probe/artifacts/truth/contact_sheet.png)显示蓝块、红块、托盘及动作终态。另存[辅助视角](../experiments/prerequisite_probe/artifacts/truth/auxiliary/)；重放终态与原录像的最大物体位置差小于 0.002 m。只有 Codex 完成了一次视觉判读，[第二名独立复核者仍待完成](../experiments/prerequisite_probe/artifacts/truth/visual_review.json)，因此这些样本仅作开发探针。

六段视频各为 15 秒、640×480：[30 FPS 母版](../experiments/prerequisite_probe/artifacts/raw/)各 450 帧；[模型输入](../experiments/prerequisite_probe/artifacts/model_input/)各 1 FPS、15 帧。全部从母版固定抽取原始帧索引 `0,30,...,420`；[实际解码帧哈希](../experiments/prerequisite_probe/artifacts/truth/actual_frames.json)和视频 SHA-256 已存。[无语义场景清单](../experiments/prerequisite_probe/artifacts/scenario_manifest.jsonl)只有编号、视频哈希、帧索引及唯一指令 `Put the blue cube in the green tray.`，没有条件代号或真值。准备动作视频在红块动作结束后停止，蓝块未被触碰。B+ 和 B0 的动作前状态 SHA-256 同为 `12cf2c43c3a2ad608dfd110977658921fda91f6f66e2f4b3d12a3901ef3274df`，由同一保存快照分叉。[冻结参数与代码哈希](../experiments/prerequisite_probe/artifacts/truth/frozen_config.json)已保存。

## 物理基线

固定 Panda 关节位置控制器仅继续操作蓝块，15 秒后续预算，20 个相同扰动种子；动作分支和等时长 15 秒空动作分支共享扰动，从原快照起总预算均为 30 秒。`q` 为继续放置成功率，`C=q_action-q_control`。完整逐种子记录见[oracle_checks.jsonl](../experiments/prerequisite_probe/artifacts/truth/oracle_checks.jsonl)。

| 条件 | 视频编号 | q_control | q_action | C | 物理解释 |
|---|---:|---:|---:|---:|---|
| B+ | 0001 | 0/20 | 20/20 | +1.00 | 红块移出托盘，蓝块可放入 |
| B0 | 0002 | 0/20 | 0/20 | 0.00 | 红块移动后仍占据放置位 |
| U0 | 0003 | 20/20 | 20/20 | 0.00 | 红块本来就在托盘外 |
| H− | 0004 | 20/20 | 0/20 | −1.00 | 红块进入托盘阻碍放置 |
| G+ | 0005 | — | 视频内直接成功 | — | 蓝块已进入托盘的正向锚点 |
| N0 | 0006 | — | 视频内无进展 | — | 静止锚点 |

这证明的是**相对于该冻结继续控制器和预算**的条件效应；20 个微扰种子共用一个场景和几何模板，不是 20 个独立场景。仿真空间与碰撞提供标签证据，但没有多抓取姿态的完整全局可达性证明。[物理动作时段曲线](../experiments/prerequisite_probe/artifacts/truth/physical_action_curves.png)只画物体位置，绝非模型分数。[验证记录](../experiments/prerequisite_probe/artifacts/truth/validation.json)的 11 项检查通过；自动测试 8 项通过。

## 两种方法的实际执行与数值

经用户租用 SeetaCloud RTX 5090 32 GB 云机（页面标价 ¥3.03/小时），只上传六段编号视频及无标签输入清单。TOPReward 的 Qwen3-VL-8B-Instruct 四个权重分片（17,534,339,512 字节）、Robometer-4B 两个分片（8,900,663,842 字节）及 Qwen3-VL-4B-Instruct 基座均下载完毕并按官方仓库 SHA-256 完整校验；见[权重清单](../experiments/prerequisite_probe/artifacts/model_results/official_weight_hashes.json)与[下载/环境日志](../experiments/prerequisite_probe/artifacts/model_results/cloud_logs/)。TOPReward 使用官方 FlashAttention 2.8.3 预编译 wheel（SHA-256 `f25da18657a87fc83dc1bfb8b7751b82246e9db355510226b674fd437c34b5fb`）、Torch 2.8.0+cu128、Transformers 4.57.1、QwenClient 原代码；最高观察到约 17.8 GB GPU 占用。[完整运行日志](../experiments/prerequisite_probe/artifacts/model_results/topreward/cloud_run.log)记录六次成功评分。

Robometer 用官方提交 `352d160389daa964788de1ec933d1925f3a6de4f`、官方 checkpoint revision `beef63bc914c5c189329d49c6d712d96d632aa34`、官方 `example_inference_local.py --fps 1`。Unsloth 将 Qwen 基座名映射到自身的同名仓库；[官方仓库哈希对照](../experiments/prerequisite_probe/artifacts/model_results/unsloth_qwen4_weight_equivalence.json)证实两个权重分片逐个 SHA-256 相同，配置和分词元数据来自 Unsloth 固定 revision。**严格未修改原版在第一段前向计算报 `float != c10::BFloat16`，尚无该模型结果**；见[原版完整失败日志](../experiments/prerequisite_probe/artifacts/model_results/robometer/0001.official_dtype_fail.log)。这是环境/加载路径失败，绝不计为模型漏判。随后复制官方仓库，单独应用[未合并的 PR #33 补丁](../experiments/prerequisite_probe/patches/robometer_pr33.patch)（提交 `19562e8fe0e63f74b64aa06f8e8fbfaf76127ea7`），只将加载后浮点参数恢复为 checkpoint 的 BF16；使用 Python 3.10.22、Torch 2.8.0+cu128、Transformers 4.57.6、Unsloth 2026.8.18、Unsloth Zoo 2026.8.17。这一**兼容版**六段均成功写出官方原生 progress 和 success head；不冒称严格未修改原版。较新 Unsloth 2026.9.14 的 PR #33 尝试还遇到 `hidden_states=None`，[失败日志](../experiments/prerequisite_probe/artifacts/model_results/robometer_pr33_compat/0001.unsloth_2026_9_14_fail.log)保留。

两种入口每次外部输入只有编号视频与 `Put the blue cube in the green tray.`。[TOPReward 批运行命令](../experiments/prerequisite_probe/cloud_run_topreward_official.sh)固定 `num_samples=15`、`reduction=mean`、`fps=1`、`use_video_description=False`、`add_chat_template=False`；[六份原始 `prefix_rewards`](../experiments/prerequisite_probe/artifacts/model_results/topreward/)按编号保存。[Robometer 兼容版命令](../experiments/prerequisite_probe/cloud_run_robometer_pr33_compat.sh)、[逐视频实际命令与完整日志](../experiments/prerequisite_probe/artifacts/model_results/robometer_pr33_compat/)和 `.npy` 原始数组均保存。[云端 TOPReward 解码帧](../experiments/prerequisite_probe/artifacts/model_results/cloud_topreward_decoded_frames.json)及[云端 Robometer 解码帧](../experiments/prerequisite_probe/artifacts/model_results/cloud_robometer_decoded_frames.json)各为六段 × 15 张 RGB，逐帧 SHA-256 与冻结[实际帧记录](../experiments/prerequisite_probe/artifacts/truth/actual_frames.json)完全一致。模型未接触类别、步骤、真值或后续控制器结果。

以下均为**原生尺度**的稳定后 12–14 秒中位数减动作前 0–2 秒中位数；TOPReward 为结尾 `True` token 对数评分，Robometer 为原生 progress，数值不能跨方法直接比较。[完整 15 点原始数据、窗口及成对差值](../experiments/prerequisite_probe/artifacts/model_results/analysis_native.json)和[动作时段曲线](../experiments/prerequisite_probe/artifacts/model_results/native_action_curves.png)可复核，不使用逐视频 min–max。

| 条件 | 视频 | 物理事实 | TOPReward 原版 Δ | Robometer PR #33 兼容版 Δ |
|---|---:|---|---:|---:|
| B+ | 0001 | 准备动作有效，`C=+1` | −5.875 | +0.1022 |
| B0 | 0002 | 移动后仍阻挡，`C=0` | −2.500 | +0.2693 |
| U0 | 0003 | 原本畅通，`C=0` | −1.750 | +0.1479 |
| H− | 0004 | 动作造成阻挡，`C=−1` | −1.500 | +0.5606 |
| G+ | 0005 | 视频内直接完成目标 | +10.375 | +0.7490 |
| N0 | 0006 | 静止锚点 | −1.125 | +0.1954 |

TOPReward 原版对 G+ 给出明确正向锚点，B+ 对 B0 的增量差为 −3.375、对 U0 为 −4.125（两组排序均逆向）；H− 相对 N0 的增量差为 −0.375，方向正确。B0/U0 的稳定后净增量未上升，但 B0 动作中有一次 +4.5 的原生相邻点跳升；不能把单点波动直接算作超过冻结阈值的误奖。Robometer 兼容版对 G+ 的增量比 N0 高 +0.5536；B+ 比 B0 低 0.1670、比 U0 低 0.0456，H− 比 N0 反而高 0.3651，方向均与物理对照不符。B0/U0/H− 的稳定后进度也上升，但 N0 自身漂移 +0.1954；只有一个 N0 开发片段，无法冻结可靠噪声阈值，因此**不报阈值化漏判率或误奖率**。[success head 原始概率](../experiments/prerequisite_probe/artifacts/model_results/analysis_native.json)另作诊断：G+ 稳定后中位数 0.9453，H− 0.1426，B+ 0.0016；它不替代 progress 指标。

[机器可读状态](../experiments/prerequisite_probe/artifacts/model_results/status.json)与[成对排序](../experiments/prerequisite_probe/artifacts/model_results/paired_sorting.json)为严格 Robometer 原版保留 `null`，不把运行失败写成零分或平局。第二名独立视觉复核者仍缺失，只有一个几何模板、每类一段视频、20 个物理种子共享场景；这些观察可用作下一阶段诊断，**不能证明一般性问题、方法缺陷机制或新方法必要性**。

## 复现命令

在 `D:\monitor2` 执行：

```powershell
D:\monitor2\.venv\Scripts\python.exe -m experiments.prerequisite_probe.produce --all
D:\monitor2\.venv\Scripts\python.exe -m experiments.prerequisite_probe.audit_inputs
D:\monitor2\.venv\Scripts\python.exe -m experiments.prerequisite_probe.save_aux_reviews
D:\monitor2\.venv\Scripts\python.exe -m experiments.prerequisite_probe.validate
D:\monitor2\.venv\Scripts\python.exe -m unittest discover -s experiments\prerequisite_probe\tests -v
```

TOPReward 原版接口尝试（仅把编号视频和最终目标指令送入官方 QwenClient，调用原生 15 个前缀；`add_chat_template=False`、`use_video_description=False`，没有结果驱动的改提示）：

```powershell
$env:PYTHONPATH='D:\monitor2;D:\monitor2\research\sources\TOPReward'
D:\monitor2\.venv\Scripts\python.exe -m experiments.prerequisite_probe.run_topreward_official --model-path C:\Users\HANWANG\.cache\huggingface\hub\models--Qwen--Qwen3-VL-8B-Instruct\snapshots\0c351dd01ed87e9c1b53cbc748cba10e6187ff3b --video D:\monitor2\experiments\prerequisite_probe\artifacts\model_input\0001.mp4 --out D:\monitor2\experiments\prerequisite_probe\artifacts\model_results\topreward\0001.json
```

Robometer 官方自有视频入口尝试：

```powershell
$env:PYTHONPATH='D:\monitor2\research\sources\robometer'
$env:WANDB_MODE='disabled'
$env:HF_HUB_CACHE='D:\monitor2\.cache\huggingface\hub'
D:\monitor2\.venv-robometer\Scripts\python.exe D:\monitor2\research\sources\robometer\scripts\example_inference_local.py --model-path D:\monitor2\.cache\huggingface\hub\models--robometer--Robometer-4B\snapshots\beef63bc914c5c189329d49c6d712d96d632aa34 --video D:\monitor2\experiments\prerequisite_probe\artifacts\model_input\0001.mp4 --task 'Put the blue cube in the green tray.' --fps 1 --out D:\monitor2\experiments\prerequisite_probe\artifacts\model_results\robometer\0001.npy
```

上述 Windows 命令是早期未成功的本机尝试。实际云端复现使用 [TOPReward 批运行脚本](../experiments/prerequisite_probe/cloud_run_topreward_official.sh)、[Robometer 严格原版脚本](../experiments/prerequisite_probe/cloud_run_robometer_official.sh)和单列的 [PR #33 兼容版脚本](../experiments/prerequisite_probe/cloud_run_robometer_pr33_compat.sh)；每段兼容版的完整命令在对应 `.command.txt`。在本机从已取回的原生数组重算表格与曲线：

```powershell
D:\monitor2\.venv\Scripts\python.exe -m experiments.prerequisite_probe.analyze_native_scores
D:\monitor2\.venv\Scripts\python.exe -m experiments.prerequisite_probe.write_model_status
```

评分没有逐视频 min–max 归一化；本报告所有 Robometer 数值仅指 PR #33 兼容版。
