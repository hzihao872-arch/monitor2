# 现有资产的只读核查

日期：2026-10-13。只读了代码、文件列表与少量文本，没有运行仿真、模型或实验。

## 可以直接复用什么

- 已有Qwen3-VL推理接口：`experiments/qwen_backend.py`。此次仅确认文件入口；没有重跑或确认运行配置。
- 入口与支撑开发场景的源码快照：`research/prerequisite_monitor/fresh_scenes_20261006/access_gate/dev_v2/validation/source_snapshot/`。
- `contract.py:evaluate_terminal` 使用至少0.5秒窗口，检查方块完整足迹、底面高度、指定支撑接触、无其他支撑、夹爪释放且不触物、速度与位移阈值。它是任务特定终局证书，缺证据按该合同失败，不能升级为整个任务的通用不可行证据。
- `generate.py:_record_one` 已记录 state 与 terminal_observation 到 `truth/sim_states/*.jsonl`；不是只有metadata。
- 实际核查该dev_v2目录含9个mp4、9个逐帧sim_states jsonl（每个约0.73MB）、对应truth json及condition_map。它们均是已有开发资产，不是本轮新测试或大规模训练集；与被反复看过的八例关系不据文件数量猜测。
- `geometry.py` 有46mm方块与0/30/110mm入口宽度的任务特定几何判据；支撑判据附有接触必须排除其他支撑的条件。

## 不能假定什么

`routes.py:simulate_condition` 在循环中调用 set_prerequisite_pose，并写明 actuation_mode 为 prescribed_kinematic_slider_with_synchronized_robot_route。部件运动由脚本驱动。虽然 run_continuation 有center/offset两条IK路线和可复位入口，不能据此认定已拥有可扩展、多任务、冻结且可靠的机器人技能库。

旧入口scene_card写明只有一个合法顶入口；没有提供替代侧口成功反例。方块已经正确落在盒内后再关盖，终局目标仍可成立；‘盖变关闭’本身不能统一标为任务撤销。必须区分当下尚需的前提与已经用过、不再需要的准备。

`experiments/data_manifest.json` 对RoboCasa365写明 individual large MP4/trajectory blocks not fetched；对RoboFAC等也是清单/QA为主。不能把这些表项算成本地现成大量动作对齐轨迹。

未确认真实机器人硬件、强冻结策略、数据标注预算、可用训练显存。新想法的最小实现只能写为未来设计与条件需求，不能声称现有资产已保证成立。

## 对本轮选题的约束

已有完整仿真状态时，直接逐状态几何/接触标签是更简单且应保留的基线。为了省标签而在这些状态上绕远路做事后回溯没有理由。后验监督的研究意义只能落在真实/外部数据证据稀疏、视觉学生部署仅看前缀的设置。新增数据若需场景变化或人审，必须明确列账。

