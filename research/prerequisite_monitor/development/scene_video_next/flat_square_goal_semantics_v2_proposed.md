# 平面目标语义卡 v2 提案（评测侧；未审定）

v1 两个关键负例出现分歧：倾斜落位 E 和夹爪仍接触 F 被答作完成。本次仅据原答中明确的歧义修正普通语言，不据任何模型得分调句子或阈值。新句仍只规定最终蓝块状态，不提红物、移障或步骤次序。

> Place the blue cube entirely inside the single green square with one whole face flat against the tabletop. Open the gripper and move it clear, then let the cube settle and stay still.

作者事前预期（交 v2 包前封存）：A、C 完成；B、D、E、F、G、H、I 未完成。E 不满足“one whole face flat against the tabletop”；F 不满足“move [the gripper] clear”；H 末态出框且移动；I 两时点都在框内，却没有“settle and stay still”。允许蓝块偏心但完整入框；不要求红物保持或离开某位置。句子是否自然、是否让读者一致判定，**尚无 v2 原答**。

本提案不替换 `flat_square_dev.py:INSTRUCTION`，也未进入任何视频或 Monitor 输入。若通过独立审读，才给整批开发六段统一冻结新协议与指令哈希。

**下一步唯一入口：**发送 `reader_only_flat_v2/` 中两份文件作独立审读；封存原答并检查 E/F 与 A/C 等全部八图。
