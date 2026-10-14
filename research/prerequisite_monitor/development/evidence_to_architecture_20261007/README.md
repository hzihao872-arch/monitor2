# 从封存证据到架构比较：本地检查点

当前状态：**阶段 A–C 完成；v0.2 单次现有实例的开发实验已完成并下载验封：162/162 次 Qwen 主调用和 72/72 个原生 TOPReward 文字作业。逐案语义审读及同预算对照见[结果报告](./remote_one_session_v0_2_20261008/RESULTS_REPORT_zh.md)。没有胜出架构、`METHOD_FREEZE` 或真正未见 G2；18 段 A/B 均为已暴露开发材料。**遵守[原研究计划](../../../../docs/plans/2026-10-07-evidence-to-architecture-research-plan.md)。

[本地检查点逐文件 SHA 清单](./local_research_snapshot_manifest.json)由 `python research/prerequisite_monitor/development/evidence_to_architecture_20261007/build_local_snapshot.py` 生成；它只封本地研究产物，不是方法冻结。

## 审阅顺序

1. [逐案例证据图谱](./evidence_atlas.md) → [18 行机器索引](./evidence_case_index.jsonl) → [复建脚本](./build_evidence_index.py)与[索引哈希](./evidence_index_manifest.json)。这里可追 P0–P6 原答/曲线/视频 SHA、P4 同视频改文字和 Robometer B 3/3 反例。
2. [竞争假说登记](./hypothesis_register.md) → [一手文献到设计映射](./prior_work_to_design.md)。每条假说有支持、混淆、最小反证和停用条件；未运行方法明确标未运行。
3. [架构决策记录](./architecture_decision_record.md) → [0.1.1 比较规格](./architecture_spec.md)。目前只固定共同接口、D/D2 公平预算和条件升级门槛，没有提前选架构。
4. [无模型 dry run 结果](./local_dry_run.json)及[运行代码](./run_local_dry_run.py) → [复验记录](./verification_log.md) → [单次上机开发实验预登记](./ONE_SESSION_EXPERIMENT_FREEZE_v0.2.md)和[运行卡](./RUN_CARD_ONE_SESSION_v0.2.md) → [真正未见 G2 制样计划](./G2_sampling_plan.md)。旧[上机前运行卡](./RUN_CARD_PRE_MACHINE.md)保留为 0.1 历史记录。
5. [单次上机结果报告](./remote_one_session_v0_2_20261008/RESULTS_REPORT_zh.md) → [执行失败记录](./remote_one_session_v0_2_20261008/execution_failure_log.md) → [逐文件核验结果](./remote_one_session_v0_2_20261008/chain_verification.json)与[交付哈希清单](./remote_one_session_v0_2_20261008/delivery_manifest.json) → [逐案原答审计](./remote_one_session_v0_2_20261008/audit_qwen/case_results.jsonl)、[15 前缀全曲线](./remote_one_session_v0_2_20261008/text_curve_summary.csv)和[语义复核](./remote_one_session_v0_2_20261008/semantic_review_notes.md)。预登记与运行卡保留上机前原貌，不能按结果改写。

## 复现命令与最新输出

在 `D:/monitor2` 下运行：

```powershell
python research/prerequisite_monitor/fresh_server_20261007/local_results/verify_final.py
# native_seals_verified=3; p1_seals_verified=3; p2_points_identical=540; p2_pair_flips=0
python research/prerequisite_monitor/fresh_server_20261007/local_results/verify_additional.py
# stages_verified=5; manifest_file_rows_verified=221; model_outputs=90; model_failures=0
python research/prerequisite_monitor/development/evidence_to_architecture_20261007/build_evidence_index.py
# rows=18; sha256=781f674b9ae86a03589764987bac0905df2b5fb7fa2bd02fcd28541a1891f320
python research/prerequisite_monitor/development/evidence_to_architecture_20261007/run_local_dry_run.py
# video_count=18; decoded_frame_match_count=162/162; contract_cases=10
python research/prerequisite_monitor/development/evidence_to_architecture_20261007/create_machine_preflight_bundle.py
# current input-only ZIP sha256=c4671c5d0ac0e23126d85ccbe98da7ec282dd1918d4f5834140c6dfa5df7b12d
python research/prerequisite_monitor/development/evidence_to_architecture_20261007/remote_one_session_v0_2_20261008/verify_local_chain.py
# qwen_calls_verified=162; text_native_results_verified=72; source_videos_verified=18
```

`local_dry_run.json` 只检查匿名原始 P0 输入 ZIP 与同字节本地视频、解码帧和抽象 JSON 读出；其合成例不对应 A/B 真值。独立包 [`machine_preflight_input_only_v0.1.1.zip`](./machine_preflight_input_only_v0.1.1.zip) 仅含许可的匿名输入与无模型 schema，不含真值、条件映射、答案、权重或最终方法提示；未上传。

[`one_session_model_side_v0.2.0.zip`](./one_session_model_side_v0.2.0.zip) 含冻结的八条方向路线、独立 V0 视觉事实探针、四种 TOPReward 任务文字诊断构建器和无真值封存器；本地审计脚本**不在上传包内**。上机前无模型 dry run 和全失败模拟仅验证通路；实际模型结果另见本次报告。

## 需要下一阶段回答的问题

本次 E/H 的目标结构事实仍未正确建立，分步链未优于同预算 D2/D3；自动关系文字退化为回退句，真假关系轴未得到检验。需要独立人类复核语义证据，再验证不泄漏答案的实体/区域定位；只有事实正确仍推错时，才评价额外续行复核。旧 Robometer B E 3/3 反例保留，真正未见 G2 另行准入。
