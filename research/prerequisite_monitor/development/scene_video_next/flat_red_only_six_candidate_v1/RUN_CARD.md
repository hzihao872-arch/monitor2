# 无黄块平面六段运行卡（2026-10-05）

**环境/输入。** 在 `D:\monitor2`，使用现有 `D:\monitor2\.venv\Scripts\python.exe`、本地 ManiSkill/SAPIEN/ffmpeg，无权重、无服务器。场景为 `PrerequisiteFlatSquareDev-v1`，物理成功协议 `flat_square_dev_v2`，种子 20261005；匿名文件号来自独立固定随机种子 202610051。B+/B0 使用同一 blocked 状态快照，其余四类使用同一 open 状态快照。源端红盖、黄块和旧 `probe.py`/`produce.py` 均未修改。

**命令。**

```powershell
& 'D:\monitor2\.venv\Scripts\python.exe' -m unittest experiments.prerequisite_probe.tests.test_flat_red_only_video_package -v
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.flat_red_only_video_package --output 'research/prerequisite_monitor/development/scene_video_next/flat_red_only_six_candidate_v1'
```

制样器拒绝覆盖非空目录。上面的六段命令已执行一次，返回 `candidate_pending_independent_review, clips=6`。各视频包含 15 个真实解码帧，对应仿真索引 `0,30,…,420`，原 RGB 与解码 RGB 哈希分开保存。另以独立解码器再次核对全部 MP4 与逐帧哈希，结果 `truth/input_audit.json: status=pass, issues=[]`。

**失败与修订。** 新 U0 契约测试首次因新模块缺失而失败，随后实现通过；六段生成没有物理/IK admission 失败。先前含黄块六段仍独立保存；它们不被本包覆盖。B0 往返造成总动作量较大，见 `truth/motion_audit.json`，作为混杂保留，不删减该负例。

**待审与隔离。** 读者专用 ZIP SHA-256 `9aecb28c71bdbadc67bd5ce14e85577ed1e99e67fd14d3bafe2034cfe84b6faa`，ZIP 九条目逐字节等于 `observer_only/`；仅 `truth/` 含条件映射、物理轨迹、作者联系表及验证报告。独立读者未交原答前不建 `model_input/` 或宣称服务器可用；本包不是冻结后的盲测。

**最终本地测试。** `D:\monitor2\.venv\Scripts\python.exe -m unittest discover -s experiments/prerequisite_probe/tests`：83 项通过，0 失败，耗时 28.959 秒。出现的 SAPIEN/NumPy/Gym 提示为依赖警告，未改变测试判定。

## 独立审读后转为开发输入

首次答卷与同一读者的补答分开封存在 `../reviews/`，分别给出六段关键关系 6/6 和补答完成标签 6/6 与隔离真值相符；来源/时间和不足详见两份收据。没有重拍视频。执行：

```powershell
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.prepare_flat_red_only_dev_input 'research/prerequisite_monitor/development/scene_video_next/flat_red_only_six_candidate_v1' 'research/prerequisite_monitor/development/scene_video_next/reviews/flat_red_only_six_receipt_and_comparison.md'
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.run_monitor_qwen --input-dir 'research/prerequisite_monitor/development/scene_video_next/flat_red_only_six_candidate_v1/model_input' --model-path 'research/prerequisite_monitor/development/scene_video_next/flat_red_only_six_candidate_v1/NO_MODEL_LOADED' --output 'research/prerequisite_monitor/development/scene_video_next/flat_red_only_six_candidate_v1/verification/runner_dry_run.jsonl' --dry-run
```

上面两条是**已执行的制包/无模型核验记录，不可在现有输出目录重复运行**；程序拒绝覆盖。六段实际解码各 15 帧，90 个按秒排序的像素哈希均与清单一致；输入 ZIP 九文件逐字节核对。首次自写兼容审计把运行器按秒数存储的哈希字典直接与制样器的有序列表比较，误报六段不一致；该失败报告保存在 `verification/compatibility_audit_v1_invalid_type_comparison.json`。纠正比较形式后的 `verification/compatibility_audit.json` 为 `status=pass, issues=[]`。`FLAT_DEV_READY.json` 是唯一开发交接索引；只有 `truth/server_alias_map.json` 含条件映射。旧黄块开发输入独立保留，原两机制 `SCENE_READY.json` 仍未签发。
