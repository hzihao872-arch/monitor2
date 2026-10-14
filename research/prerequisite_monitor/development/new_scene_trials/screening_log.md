# 全新机制物理筛选记录（均未交给 Monitor）

此处只记录仿真制样与排除，不用任何新方法分数选场景。正式完整六类冻结之前，所有场景均为候选。

## source_stack：源蓝块上方叠放红色挡物——排除

2026-10-05 使用本地 ManiSkill、冻结的 `blue_only_joint_ik_v1` 后续控制器，分别由 blocked/open 初始快照做等时长 15 秒 N0 对照，再做 B+/B0/U0/H− 准备动作。每条件先试配对种子 0–2；原始逐条件状态/坐标/IK 最大误差在 `source_stack_trial.jsonl`（SHA-256 `d1fef7d9b3e9a9bdba52f1eff5b51f8e6e93023c12bba757efbb25cace8696d1`），保存全部四条件。B+ 红块确实从蓝块顶部移到桌面，B0 顶部仍有红块，H− 红块移到顶部；但四条件和相应 N0 的后续蓝块放置均为 **3/3 成功**，故 `C=0`（初筛），不满足有效/有害门槛。固定控制器能从该几何配置继续完成任务，不能把视觉上的“压挡”擅自标成必要前置。此机制**排除**，不制正式视频、不加入新测试；不因视觉故事看似合理修改物理标签。

## tray_crossbar：托盘口可移走横杆——制样门槛通过，待方法冻结

横杆横跨托盘入口，挡住蓝块下降位置；它与旧族「红方块填满托盘」的接触/阻挡几何不同。`tray_crossbar_trial_seed0.jsonl` 保留单种子尝试；`tray_crossbar_trial_20seed.jsonl`（SHA-256 `6844f73f8ee55d2e3b67ec92739b5bf7a67a04a22f791dee690f466bcc8ae9f1`）保留四条件、对照及逐种子坐标和运行结果。B+ 对照 0/20、动作后 20/20；B0 为 0/20→0/20；U0 为 20/20→20/20；H− 为 20/20→0/20。主视角初帧 `tray_crossbar_initial.png` 已保存；完整六段在 `research/prerequisite_monitor/new_test_candidates/tray_crossbar/`，实际解码及 11 项结构/物理检查全过。可见性逐类记录于 `new_test_candidates/visual_audit.md`，但只有一名非盲审核者。方法与输入哈希冻结前仍称候选。

## source_bridge：源蓝块上方可移走支架横梁——制样门槛通过，待方法冻结

横梁由两根静态柱支撑，跨在蓝块上方以限制从上方抓取；与失败的 `source_stack` 直接叠压不同，也与旧族蓝块旁的侧向抓取入口不同。`source_bridge_trial_seed0.jsonl` 保留单种子尝试；`source_bridge_trial_20seed.jsonl`（SHA-256 `5da19701c0b493e141a79a465e44f7a6cba9cd32155d708bc7ab8f6488ca0448`）保留四条件与全部配对种子。B+ 为 0/20→20/20；B0 为 0/20→0/20；U0 为 20/20→20/20；H− 为 20/20→0/20。主视角初帧 `source_bridge_initial.png` 已保存；完整六段在 `research/prerequisite_monitor/new_test_candidates/source_bridge/`，实际解码及 11 项结构/物理检查全过。蓝块部分被遮挡但可辨，后续应把相关模型混淆保留为错例。方法与输入哈希冻结前仍称候选。
