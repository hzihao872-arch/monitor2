# v0.2 单次上机执行偏差与失败记录

本文件保留失败和中途决策；完整输出以原始 JSONL 与 seal 为准。租期由用户提供为上机时约一小时，未记录凭据。

| 阶段 | 发生情况 | 对数据的影响及处理 | 可追溯文件 |
| --- | --- | --- | --- |
| 包与身份 | 本地和远端 ZIP SHA、匿名成员、18 段媒体核对；已有 Qwen config/四分片与官方 TOPReward 提交符合冻结要求。 | 未上传真值、条件索引、评分代码；没有换权重或修改原生方法。 | `chain_verification.json`、`qwen_evidence/identity.txt`、`qwen_evidence/dry_run.jsonl` |
| 原运行脚本的时长门 | dry run 和 18 调 pilot 完成。脚本于 04:01:12 UTC 读取剩余 2,928 秒，按保守门槛“主实验需 2,568 秒，另保留 600 秒”停止，没有启动主表。pilot 实测 18 调 167.114 秒，13 valid、4 schema/evidence failure、1 direction conflict。 | 保存原始 pilot，未并入主实验。按实测比例，162 调约 1,504 秒；在余时扣除 600 秒缓冲后仍有 2,328 秒。随后直接调用**同一已上传冻结 suite 代码、原参数和原包**，以 2,200 秒硬超时执行完整主表，并逐阶段下载检查点。没有现场改提示、真值或评分规则。保守门槛的早停不应误记为模型失败。 | `supplement_evidence/run_initial.log`、`qwen_evidence/pilot.jsonl`、`qwen_evidence/full.log`、三个 checkpoint archive |
| Qwen 主表 | 162/162 原答，133 valid、15 schema/evidence failure、14 direction conflict。0 运行异常、0 OOM、0 输出 cap。 | 全部 29 条校验/读出失败保留在 `raw.jsonl` 与分母，未修复 JSON 或自报方向。阶段明细在结果报告；seal complete。 | `qwen_evidence/raw.jsonl`、`qwen_evidence/qwen_seal.json`、`audit_qwen/case_results.jsonl` |
| 文字准备命令 | 第一次单独执行构造文字的 shell 包装因未导出脚本使用的环境变量而立即报变量未绑定；未发起原生模型调用。 | 补齐环境变量后运行冻结构造脚本；以主原答 SHA 生成并封存 72 条输入。失败命令没有形成可混入数据集的结果。该即时终端报错未在最终 `text_prep.log` 中保留，故只作操作记录，不当作模型证据。 | `text_evidence/text_inputs/text_probe_manifest.json`、`text_evidence/text_seal.json` |
| 自动关系可识别性 | TP1 的 18 条原答只有 3 条含非空谓词，三条均未过整条 JSON/schema 校验；自动文字构造规则拒收。 | `auto_relation` 和 `auto_counterclaim` 都对全部 18 段使用同一回退句；72/72 原生作业仍完成。相同曲线仅说明处理文字相同，真假关系比较在本轮**不可识别**。 | `text_evidence/text_inputs/text_probe_manifest.json`、`audit_text_probe.json` |
| TOPReward 原生探针 | pilot 1 作业成功；主 72/72 作业成功，15 点曲线齐全，0 原生运行失败。 | 原结果、每文件 SHA、输入文字 SHA 和 72 条额外 tokenizer 计数封存。历史 P0/P4 文件未被覆盖。 | `text_evidence/text_raw/`、`text_evidence/text_seal.json`、`supplement_evidence/text_instruction_token_counts.jsonl` |
| 本地揭盲与语义审读 | 自动审计产生 180 条案例阶段记录（含 V0、派生 H3）、108 条 Qwen 配对关系、129 条读出消融。先查看原答和帧、写下语义笔记，再查自动汇总。 | 语义审读者为 Codex AI，尚无独立人类复核；报告明确限制。所有已下载压缩包和内部 seal 通过本地核查。 | `semantic_review_notes.md`、`core_case_semantic_review.csv`、`chain_verification.json` |

`schema_or_evidence_failure` 包含格式、枚举、时间引用或所需证据校验失败；`direction_conflict` 指模型自报方向与冻结确定性字段读出不合。两种失败都不能用肉眼觉得“答对”来重新归为 valid。派生 H3 的 8 个 unknown 是一致性门拒收，非运行故障。晚期判断应回查具体原答与逐案语义复核，而非只读聚合方向数。
