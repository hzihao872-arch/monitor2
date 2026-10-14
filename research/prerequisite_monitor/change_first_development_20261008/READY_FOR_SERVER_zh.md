# W9 本地验收：达到 S1 首次真模型试跑上机条件

> 历史上机门记录。S1 已于 2026-10-09 执行并验封；当前结论见 `S1_PILOT_REPORT_20261009_zh.md`。本页末尾的“开机”请求已失效。

日期：2026-10-08（北京时间）。范围仅限已暴露 A/B 开发视频的小试跑；**没有新 8B 模型成绩**。

## 交付身份

- 白名单 ZIP：`D:\monitor2\research\prerequisite_monitor\change_first_development_20261008\packages\pilot_v6.zip`
- 包 SHA-256：`5a5c7070ee8673fde793cf2dfc4c0669367f99eca915158f0b8d1eaff4dd7306`；180 个成员。
- 冻结哈希与源文件：`protocol_freeze.json`。私有源清单与条件映射位于 `private_eval/`，不在 ZIP。
- 联系表与候选审读：`private_eval/review_v3/`（18 段 CPU-only）；早期检查点 `review_v1/`、`review_v2/` 均保留。
- 运行卡和可复制的预检、首块、续跑、封存命令：`SERVER_RUNBOOK_zh.md`。

## 本地检查证据

1. `D:\monitor2\.venv\Scripts\python.exe -m unittest discover -s experiments/prerequisite_probe/tests/change_first -p test_*.py -v`：36/36 通过，退出码 0。覆盖未来替换、时间/路径/引用、V1 目标盲、相机位移与候选溢出、V3 新像素、强对照入口、断点恢复、硬请求预算、私有评价分母、包篡改及封存篡改。
2. `verify_bundle.py --bundle ...pilot_v6.zip`：`valid=true`，退出码 0；正向白名单包含模型侧 Python、协议、匿名 14 秒前缀 PNG 和上机脚本；没有私有标签、仿真真值、原始完整视频或历史凭据。
3. 在 `packages/unpacked_v6/` 从解压代码独立运行 mock：首块 1 查询/10 请求，续跑至 8 查询/80 请求，第三次启动仍 80；80 个阶段载荷校验无效数 0。mock 后端只返回脚本化 unknown，**不计视觉准确率**。
4. 解压目录里的 `collect_and_seal.py` 对 mock 结果生成 archive，`--verify` 逐文件哈希通过；归档 SHA 由运行时另记。
5. CPU 审读选择每段首帧、末帧及均匀中段。A/B 的 R 前缀均含 t=8 秒；候选合同另记相机整体位移风险、稳定端点和溢出。真实板/入口语义是否被模型识别仍待 S1 原答。

## S1 矩阵、上限与停止

A/B 各 E、H、R、G 一条，统一 `t=14s`。同一合法前缀、同一 Qwen3-VL-8B-Instruct 底座、共同 V1 原答和共同 V1/V3 像素，D4/K4/C4 各 4 个名义槽。总名义 96 槽，正常去重 80 次真实请求，**累计真实请求硬上限 96、从只读预检开始远端占用硬上限 2 小时**；首块十调后检查，至少留 15 分钟封存。建议用户预留 1–2 小时可用窗口。参考估时约 0.6–1.2 小时但新提示长度与实际吞吐未测，2 小时是停止上限而非完成保证。

只读预检需确认现有模型、processor、环境、显存与磁盘；卡被占用或身份不符不加载。任何未来/私有信息越界、OOM、系统性 schema/长度故障、ambiguous 请求或预算风险都停。下载封存后本地分析并通知是否可释放服务器。

## 未验证项

真实 V1 变化召回、L2 关系绑定、V3 净纠错、L4 状态质量、真实 token/延迟/峰值显存、视觉证据语义支持与独立双人审读均未完成。S1 只提供接口与失败定位的小样本；不能把 mock/JSON 通过称为方法有效，也不能自动推进 S2、盲评或策略训练。

**S1 已执行并验封，本页开机门已结束。后续重新上机须按新修订版另行核对资源和预算。**

