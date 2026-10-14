# Robometer（Liang et al., arXiv:2603.02115v2）

一手：[论文](https://arxiv.org/html/2603.02115)、[官方代码](https://github.com/robometer/robometer)。输出每帧进度与另一路 success 概率；训练将专家轨迹的帧级进度交叉熵与轨迹比较偏好损失结合。论文附录说对偏好样本只在第一轨迹成功时加进度监督，失败轨迹无可靠绝对进度目标。这种训练能强化成功/失败排序，但不等于学习“动作让固定后续控制器变得可行”的因果差。

路径：视频/任务→1 FPS 抽帧→`Trajectory`/`ProgressSample`→collator 拼视觉与文本→模型 progress/success heads→逐帧数组。官方 `scripts/example_inference_local.py` 32–129 和 `robometer/evals/eval_server.py`。六族开发材料里四个托盘占位族 B+ 对 B0 错，两抓取入口族 B+ 对 B0/U0 对；G+ 全正。必须保留这两个正向反例。严格未改源码因 BF16/FP32 混合失败，无有效结果；PR #33 仅统一浮点参数 dtype 后有效，身份为兼容版。

推演：B+ 应上升，B0/U0 平或未知，H− 相对 N0 降，G+ 上升；训练进度头可能更像当前步骤完成程度，无法单独证明对未来可行性敏感。反证：新机制中兼容版稳定全部正确，则不再据开发集提出普遍缺陷。不要跨 TOPReward 原始分数量纲比较。
