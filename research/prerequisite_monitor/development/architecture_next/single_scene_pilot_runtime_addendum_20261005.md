# 单场景试验运行附录（2026-10-05 至 2026-10-06）

此处补记 `single_scene_pilot_preparation.md` 后的执行；预注册的 protocol 和 runbook 均未改写。

1. **本地门槛。** 输入 ZIP 九文件、六个视频 SHA、解码后 90 帧 SHA 通过。真实模型烟测的四条原文用 JSON 布尔代替契约字符串枚举，含 `null` 路线/反证和单项引用，旧解析器将它们全判无效。保留烟测原文，建立 `monitor_contract_v2.py`、`monitor_relation_endpoint_v1_contract_v2.py`、`run_relation_endpoint_pilot_contract_v2.py` 和代码 ZIP v3。新层只记录并归一等价语法，保留缺失主张；提示词字节相同，不填补语义字段。v3 SHA-256 `244ef6bdbeb93bc3360149a9801d929dc10c793345e443192bd77141290ea5c5`。版本化测试与无模型 dry run 通过。
2. **服务器预检。** 使用用户给出的已租实例，预检只读且通过：已有 RTX 5090 32 GB、约 48.2 GB 可用磁盘、既有环境和权重、TOPReward 源码提交 `4877a0ee5098cbec18485125466631b1dcc4a573`、Robometer 兼容分支基础提交 `352d160389daa964788de1ec933d1925f3a6de4f` 与补丁。8B、基础 4B、Robometer 4B 共八个权重分片的现场 SHA-256 均与 `experiments/prerequisite_probe/artifacts/model_results/official_weight_hashes.json` 匹配。一次本地核对脚本仅用文件名作键，两个 4B 模型分片同名导致误报；改用仓库名加文件名键后 8/8 通过，权重没有不匹配。
3. **首次运行与故障。** `/root/autodl-tmp/monitor2/single_scene_pilot/flat_red_v1` 完成配对 24 次视觉调用与 TOPReward 六段；Robometer 六段因子进程找不到已有 `HF_HOME` 缓存失败。先封存原始树，SHA-256 `8ce686e1515b9eba6e445c5945e716db7d8cb414db03bff925dd5c3522a45116`，错误 stdout/stderr 和六条失败均保留。排障中一次直接烟测因 `PYTHONPATH` 指向严格旧包触发既有 `BFloat16/Float` LayerNorm dtype 故障；改指向 PR #33 兼容包并设置已有缓存根路径后，15 点进度与 15 点成功双头烟测通过。严格未修改原版在本次正式试验中标**未运行**；没有将兼容版改称原版。
4. **修复后完整运行。** `/root/autodl-tmp/monitor2/single_scene_pilot/flat_red_v1_cache_fix` 重新核输入与 dry run，复用首次成功的配对与 TOPReward 16 个哈希匹配文件，仅重跑失败的 Robometer 兼容版。完整树封存 SHA-256 `09edaceac2d967740692e6cfd6e1f10c5aa1da6ae3c225aedf253adbeb176676`；本地取回归档后复核封存，再打开 truth/。保存 15 点原生曲线、配对每次原文、实际 token/时间、帧哈希、环境、代码哈希、失败和弃答。候选六次弃答是逻辑判定，不是解析或运行故障。
5. **事后诊断。** 主原文封存后，分别运行基础 8B 与基础 4B 的聚焦事实探针，各六段一次，单独封存 SHA-256 `c0265099d8a46f8359a19b22e55a6f86fe9cc7c1d44f4c05766f184a813c12ab` 与 `67d17f4fc74883390b4b54a81f0d8d89257d97bb9a19281775b5be10681de2a9`。探针仅用于额外事后定位，不计入原生方法或 D2/候选的主预算。

全部本地文件位于 `single_scene_pilot_results_20261005/`。没有创建 `METHOD_FREEZE.json` 或将开发包当盲测。下一步入口见 `single_scene_pilot_result_20261005.md`。
