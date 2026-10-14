# P4/P5 本地准备核验（2026-10-07）

服务器已由用户关闭，P4/P5 尚无模型结果。本文件记录开机前已完成的本地工作；执行命令见 [下次开机运行卡](RUN_NEXT_SERVER_zh.md)。

另用 P0 已封存曲线做了[末帧读出核查](P0_ENDPOINT_READOUT_CHECK_zh.md)：TOPReward 的 E 在两机制 t14 仍低于 S 与 N_b，说明主要失配不只是原定首末窗口相减造成。它是事后描述性分析，不改 P0 主指标。

## 冻结材料

| 材料 | 结果 |
| --- | --- |
| 原 dev_v2 冻结包 | `freeze --verify`：`status=pass`，`issues=[]`，949 文件，清单 SHA-256 `be2af5aaa8afe8d32a1e5481631f190c6748b825ea7d0c8027a09d873a60534b` |
| P4 六个匿名输入包 | `build_p4_inputs.py --verify`：六包有效；54 个视频引用保持原视频及逐帧像素 SHA；各变体同机制九段指令完全一致 |
| P4 原生 dry run | 三变体 × 两机制六个单元全部通过；每单元九个匿名视频输入，零次模型调用 |
| P4 pilot 输入 dry run | neutral/A 的单视频输入及原生 dry run 通过；远端完整脚本会对每变体两机制都做 pilot |
| P5 dry run | targeted visual 和 future-route 两阶段均含 18 段匿名视频；两阶段均零次模型调用且通过 |
| P4 封存器反例 | 三项测试通过：完整合成 journal 可验封；缺结果、重复结果、坏曲线、结果文件与 journal 不一致均判 incomplete |
| P5 解析烟测 | 结构状态 JSON 和 `already_done` 路线 JSON 均可解析；不能用解析有效代替事实正确 |
| 脚本语法 | Git Bash `bash -n` 和 PowerShell AST 解析均通过 |
| 上传包 | 7 个成员、14,591,955 字节；成员 SHA 全与 manifest 一致；没有 truth、condition_map、评分器或旧模型输出 |

`p4_p5_upload.zip` SHA-256：`d9fe7ba669d5f9362facae95fbeb2882ec42d565261dcf7c00491119377e070c`。`run_remote_p4_p5.sh` SHA-256：`575f0ee49b010a485c8149b7a368aba284ba5ffad26f32732fbe7b8b1d97d8a1`。密码未写入任何新文件。

## 仍须在线确认

实例实际到期时间、SSH 端点是否保持、P0 远端目录和 seal 是否保持、Qwen 配置/官方提交/GPU/磁盘是否保持，以及 P4/P5 的**真实模型输出**。脚本在启动每项 GPU 工作前再次检查。若租期不足，会保留已有原始证据并跳过后续任务。

P4/P5 的任何结论都只限开发诊断。P4 改变了任务文字；P5 独立提示不能代表两原生方法内部推理。正式未见验证 G2 仍需另行冻结新场景与评价协议。
