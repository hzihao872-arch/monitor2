# 官方实现静态追踪与可运行性

检查日：2026-10-05。除既有 TOPReward/Robometer 六族运行记录外，本轮仅静态追踪，未安装新权重、未调用付费 API。行号以固定 commit 下的本地文件为准。每仓工作树在检出后 `git status --short` 为空；大模型权重未随本轮代码克隆。

## ARS：官方入口不存在

- 论文：`https://arxiv.org/html/2609.34484`，v1。给出 `https://github.com/midea-ai/ars`；本轮 `gh repo view midea-ai/ars --json ...` 返回 `GraphQL: Could not resolve to a Repository`。
- 论文描述的调用链：视频/指令→事件子代理补看/裁剪→主代理独立核查→逐帧曲线工具；附录 A 是摘要式提示，而非可执行的完整 prompt/harness。**没有可固定的官方 commit、许可、原生入口或运行结果。状态：未运行 ARS。**
- 可复用的是比较标准：有用准备、证据覆盖/二次确认、短片消融与同骨干直接提示。不能按论文摘要手写版本并冒称官方。

## ROVER

- 路径 `research/sources/rover-vlm`；commit `fd9da0752477ad24abf5af958147fceac6f6af98`。README 宣称 MIT，但检出根目录没有 `LICENSE` 文件，许可文本需上游核实。README Quick Start 用 `OpenAI(api_key=...)`，`rover_model.py` 支持外部模型请求；代码不是本地权重模型。
- 原生入口：README 的 `from rover_model import rover,process_rover_output` 或 `run_eval.py` 第195–217行。`run_eval.py` 第168–186行从预解码 JPEG 抽至 30 帧，并**另读 `task_progress.txt` 真值用于评测**；模型入口不应收到该路径。
- 调用图：`run_eval.py:195`→`rover_model.py:37 rover`→`prompt/prompting.json` 的拆解/当前帧提示→`rover_model.py:19 encode_image`→外部 VLM 回复→第83–87行解析帧描述及完成百分比→第125–170行递归子任务→第175–224行组合逐帧数值→`eval.py` 相关/距离指标。视觉证据是已有图像帧列表，无仿真状态；但 `camera_view` 是额外文本字段，应固定为画面可见视角而不含标签。
- 静态疑点：`rover_model.py:142` 的递归调用 `rover(new_subtask, camera_view, frame_file_list, current_idx-1)` 与第37行签名 `rover(model_name, task_description_i, camera_view, frame_file_list, ...)` 不匹配；`process_rover_output` 第177行引用未作为参数传入的 `frame_file_list`。这只说明该 commit 的示例路径需 smoke/修复，不能推断论文系统失败。由于需要外部 VLM API 且用户不购买，本轮未运行。若修复须标适配版并保存 patch。
- 可复用：帧清单/中间子任务及解析失败记录。不可复用假设：已给详细任务描述/视角及外部 API；不能把其评测真值读入本项目 Monitor。

## TOPReward

- 路径 `research/sources/TOPReward`；commit `4877a0ee5098cbec18485125466631b1dcc4a573`；根目录 MIT `LICENSE`。既有 Qwen3-VL-8B-Instruct revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`。本地入口 `experiments/prerequisite_probe/run_topreward_official.py:22–50`，原版推理 `topreward/clients/qwen.py`。
- 调用图：适配器 OpenCV 顺序解码15帧（第30–38行）→`QwenClient.compute_instruction_rewards_for_prefixes`（第40行）→官方 `qwen.py:355–371` 均匀前缀1..15→`compute_instruction_reward:157–290` 将帧转 PIL、组 `video`/指令与 `True` 模板（第188–234行）→模型 forward 对目标 token 损失→`prefix_rewards` 与另列归一化。`topreward/utils/inference.py:200–245` 是项目通用数据集入口；第262–265行 `true_progress` 仅用于评测 VOC，不能当模型输入。
- 权限：当前项目适配器只给编号视频与固定指令，禁用视频描述、chat template 开关固定为既有配置。原始前缀对数似然可复用；每条视频 min–max 仅展示不可作主结果。
- 状态：已在旧六段与六族运行，实际帧哈希一致；这些是开发结果。`reports/prerequisite_unseen_six_families_20261005.md` 与 `unseen_analysis_native.json` 保留全部分数。

## Robometer

- 路径 `research/sources/robometer`；commit `352d160389daa964788de1ec933d1925f3a6de4f`；当前检出未见 LICENSE/COPYING 文件，需上游核实。权重 revision `beef63bc914c5c189329d49c6d712d96d632aa34`。入口 `scripts/example_inference_local.py` 的 `--video --task --model-path --fps 1 --out`。
- 调用图：`example_inference_local.py:32–59 load_frames_input`→`robometer/evals/eval_viz_utils.py:128 extract_frames`（1 FPS；现有视频实际15帧）→脚本第71行 `load_model_from_hf` (`robometer/utils/save.py:806`)→第87行 `Trajectory`/`ProgressSample`→第88行 collator `rbm_heads.py:349–449`。该 collator 第378行将任务+视频写成“每帧完成0–1”的原生提示；第357–375行转换帧，评估/推理时不做训练 shuffle→`eval_server.py:520–595 compute_batch_outputs`→逐帧 `progress_pred` 与独立 sigmoid `success_probs`→脚本第114–129行返回数组。不要把 success head 当作 progress。
- 严格原版在既有 RTX 5090 环境因 BF16/FP32 混合报错，无有效输出。`experiments/prerequisite_probe/patches/robometer_pr33.patch` 在 `robometer/utils/save.py:923` 之后把浮点参数转配置 `torch_dtype`，不修改数据/提示/帧数；修后身份固定为 `robometer_pr33_compat`，不是未改原版。旧六段及六族有有效兼容版输出、日志/命令/帧哈希。
- 可复用：原生视频入口与逐帧数组。不能复用：训练时进度标签、真值路径；此模型的原生 progress 与 TOPReward 对数分数不同量纲。

## ReKep（关系/前置方向）

- 路径 `research/sources/ReKep`；commit `63c43fdba60354980258beaeb8a7d48e088e1e3e`；检出无许可文件，需核实。README 明说这是 OmniGibson demo，**实物感知流水线未包含，直接读仿真信息**。
- 原生入口 README `python main.py --use_cached_query` 或不带缓存的 live query；前者固定缓存约束，后者需 OpenAI API。`main.py:60–72` 从环境取 RGB、3D points、seg→`keypoint_proposal.py:18–46` 视觉特征/掩码聚类→`constraint_generation.py:120–155` 调 VLM 生成阶段 `subgoal/path` Python 约束→`main.py:93–100` 加载→第111–145行取 3D keypoints/碰撞，核查违反并回退→第163–182行阶段推进→子目标/路径优化器执行。它不是单主视角离线评分器。
- 可借鉴关系真值与回退表示；不能将 points/seg、碰撞体、约束代码、真实抓取状态送入本项目推理。未运行：环境依赖重、输入边界不符，且 live query 是外部服务。

## ProgressLM（补充强进度推理源码）

- 路径 `research/sources/ProgressLM`；commit `c5f1ebca07e9dec9be1a2b53b57bc910e6301a49`；检出 MIT `LICENSE`（仓内另含 LLaMA-Factory，需分别遵循其许可）。
- 原生可见入口 `eval/qwen3vl/codes/run_visual_demo.py:967 main`→第557行数据与多进程推理→`visual_demo_dataset.py:47` 载入**成功演示图/标注**＋当前帧→`visual_demo_prompt.py:58–127` 将每个演示图及 0–100% 阶段值明确写进提示→Qwen3VLChat→`run_visual_demo.py:26–115` 解析 `<ref>/<score>` 或 n/a→第117–300行评估。它的 mental simulation 是在演示锚点之后的文字推理，不是物理世界模型前向。
- 状态未运行。成功示范与数值阶段违反本项目输入合同；不能原样给本项目视频作公平基线。它对弃答/误拒的记录设计可复用。

## ProcVLM（新发现的强同输入基线）

- 路径 `research/sources/ProcVLM`；commit `377523a31f05bab9c0db5ac8b9edfa7b7f03968a`，检出干净；根目录无 LICENSE 文件，许可需上游核实。README `Progress Reward Inference` 给 `python evqa/inference.py --model_path ... --video_path ... --task ... --window_size 8`，**原生输入只需单视频与目标指令**，不需要演示或状态。
- 调用图：`evqa/inference.py:409 main`→第263行 `infer_progress_from_video`→第77行 `load_prompt_template` 将目标填入 `evqa/templates/procedural_c.txt`（要求先推剩余原子动作再给 `<progress>`）→第158–176行 moviepy 全帧 JPEG 提取→第129–155行最多512帧均匀采样→第119–126/339–345行每时点最近8帧窗口（早期复制首帧填满）→第223–260行 `batch_chat_with_vllm` 或可选 value head→第83行解析标签→第374–392行形成逐帧记录。
- **运行有效率陷阱**：解析不到 `<progress>` 时第377–381行沿用上一值，记录第198–200行的 `parsed_progress=None` 与 `progress_source=previous`。新对照主表须同时报解析成功率；不能把填充曲线当全部模型原生预测。窗口与本项目15帧输入对应时仍可能为8帧回看，需保存 `window_frame_indices` 和 JPEG 实际像素哈希。
- 可用许可输入、可复用原生 JSONL 接口；不能复用训练伪标签或向提示加成功示范。**未运行**：本地没有 ProcVLM checkpoint，现阶段不下载新权重或占用已租服务器；待冻结新测试前核算权重/磁盘/时间和实际可达性。

## R²VLM（递归步骤记忆）

- 路径 `research/sources/R2VLM`；commit `3b5c09ff1baea40301a790a0c15048df3fc81a5b`，工作树干净；根目录未见许可证文件。训练框架子模块未初始化，未下载权重。
- 原生单样本入口 `code/script/Alfred/infer_vllm_single.py:126 main`，需本地 OpenAI 兼容的 vLLM 模型服务，`--data_path` 样本列有 `question` 和逐轮 `turns.images`。第64行 `run_single_sample` 初始化 CoT；第88–104行每轮发送历史 CoT＋新帧＋目标问题，第113–120行解析 `<think>` 作下一轮记忆、`<answer>` 作百分比，保存每轮原始输出。Ego4D 版固定每段四张图（`code/script/Ego4D/inference_example.py`）。
- 训练使用专家视频的步骤边界，进度真值为已完成步骤比例加当前步骤段内线性时间；推理只要任务和视频片，不需训练时步骤真值。若适配固定摄像头15帧视频，必须固定分段与合计解码帧数并单列为输入适配，不能把训练标注或数据集的 `turns` 真值送入模型。
- **未运行**：7B 专用权重不在本地，且未启动服务。本轮只静态核对原生入口；不能用普通 Qwen 提示自称 R²VLM。

## PRIMO R1（目标条件过程 Critic）

- 路径 `research/sources/PRIMO-R1`；commit `f746e1f83af001337dabffafa948129353ac962e`，工作树干净；根目录未见独立许可证文件，内置第三方 `transformers-main` 等不能代表项目许可。未下载 7B 权重或 6.58 TB 媒体。
- **入口辨析**：`src/inference_example.py:17–19` 明确自称 *video-only baseline*，提示引用 `QUESTION_TEMPLATE_BASELINE` 且写死作者绝对路径、双 GPU、任意示例问题；直接运行它不是发布的 PRIMO R1。发布权重须参照 `src/eval/eval_interleave.py` 的 interleave 路径及 `src/primo_prompts.py` 的 `SYSTEM_PROMPT/QUESTION_TEMPLATE/TYPE_TEMPLATE`。
- 调用图：`eval_interleave.py:35–56` 配模型/vLLM→第138–177行读样本/目标→第227行先插初态帧→第230–245行视频和末态帧→`primo_video_utils.py:38–90` 从**同一视频**解码首末帧，`choose_nframes` 限抽帧数（发布结果实际上限22，见文件第30–31行）→第248–262行加问题/格式提示→第425–446行 processor 与 vLLM→第283–295行解析思维及答案→第348行评分。原生格式有规划、观察、推理、最终数值；没有本题要求的逐帧证据区域和不确定性字段。
- 输入边界：首末锚点来自许可视频，可在本项目按前缀生成，不需要仿真真值或后续成功视频。官方基准 JSON 含目标进度，仅供评分，不能进入 prompt。**未运行**：需要未有的 7B 专用权重和 vLLM 环境；若后续服务器可用，先保留原生数值输出/格式，不偷换为本项目的结构化 P/F 提示。

## 思想回讲

TOPReward 问“到目前为止像不像已经完成目标”，Robometer 训练来读已完成进度；它们可以正确识别蓝块入托盘，却不一定把清空托盘视为提升未来机会。ROVER/ProcVLM/R²VLM 会把动作拆步骤，PRIMO R1 已用目标和视频首末状态进行显式过程推理，ARS 已会再次看片核对事件；所以这些单独都不是可宣称的新方法。关系方法直接问“现在是否满足下一技能的条件”，CoINS 已将“拿掉这个障碍，路径会不会通”用于导航。研究剩下的可检验问题，是在**只给本视频**时能否辨认清障的因果相关关系，并在单目证据不充分时弃答；P/F/H 的优势必须超过相同骨干、相同实际帧和 token 预算的直接提示以及可运行的专用强方法。

下一步唯一入口：见 `development/local_2b_diagnostic_20261005.md` 的失败诊断，先找到可自洽读取关系与输出的同骨干对照，再决定是否值得冻结新配对测试。`mechanism_spec.md` 与设计草案已完成手算。未解决反例：ARS/简单 D 可能已经正确；抓取入口的阻挡关系可能从主视角不可判。
