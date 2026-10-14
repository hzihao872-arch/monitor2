# 上机前 2B 开发诊断（不是新方法效能证明）

日期：2026-10-05。所有模型调用只使用已公开给研究者的旧 `unseen_offset_cell` 开发族或其单段拷贝；两个新制样机制没有交给任何 Monitor 模型。六族其余编号视频均完成只解码、核哈希的 dry-run，日志为本目录 `unseen_*_input_dry_run.jsonl`。本机唯一完整可运行的 Qwen3-VL-2B 与拟上机的 8B 不同，以下只用于发现接口、解析和提示失效。

| 版本/原始文件 | SHA-256 | 观察 | 后续处置 |
| --- | --- | --- | --- |
| 初始 compact 单段 `pre_server_2b_compact_smoke.jsonl` | `3155ae59326c84dc342e7b49a152cd6724d65679c782edfa1dce444e2aff129b` | D/P/F 曾被旧解析器判 valid，却把未完成目标写成已完成；独立重核在 `pre_server_2b_compact_smoke_revalidation.json` 将三者改记 `completion_without_transition` | 在共同校验器加不可能完成转变检查，保留旧原文和旧判定 |
| v2 全六段 `pre_server_2b_offset_full_retry.jsonl` | `49b5d9e71fc384690761483f8409e6199ac5bb62fca84d86fb90342d84356faa` | 除 G+ 的 D 外，D/P/F 大多数因目标完成自相矛盾而无效；H0 六段全无效 | 加通用“准备条件≠最终目标完成”解释，未按类别写答案 |
| v3 全六段 `pre_server_2b_v3_offset_full.jsonl` | `1035d76523ce27fb98bfa781375753455938f777422dc8a6ad32089958895606` | B+：D 零、P 负、F 零、H0 弃答；B0：P/F 负、H0 错误负；U0：P/F 负、H0 错误负；H−：D 零、P 负、F 正、H0 弃答；G+：P/F 正、H0 正；N0：P/F 负、H0 错误负。D2 多段 JSON 解析失败。P 多次挑“蓝块在桌面”作为关系，未抓住准备动作影响 | P 增加通用动作关联要求，H0 明确保留结构一致但语义未审 |
| v4 B+/B0 两段 `pre_server_2b_v4_bplus_bzero_smoke.jsonl` | `0c3503b1a892ac51282be65944f20262d3a13fd2248254f214c40289cc1e1282` | B+ D/P/F 均输出零，H0 错误零；B0 D/P 输出零、F 负、H0 弃答；P 仍挑“蓝块在桌面”这一静态事实，D2 两段 JSON 失败 | 停止围绕 2B 开发例改提示；先固定共同接口，未来 8B 只在旧样本 smoke 检查可运行性 |
| v3 G+ 单段 `pre_server_2b_v3_gplus_smoke.jsonl` | `ebb8b8a5de754173fdc9939e41671b6c93c16f96c49e626bd3b2380d1c88b4cb` | P/F 可解析且方向正，D/D2 缺动作后证据 | 保留失败；不能用 G+ 成功掩盖 B+ 失效 |
| v6 首末目标字段 B+ 单段 `pre_server_2b_v6_schema_bplus_smoke.jsonl` | `10a84cc2b14812aa4940d2a52062ff70f09914dc905b62e30cbc0db18f7fc2d6` | 2B 把两个三态枚举写成句子，四路均无效 | 在共同提示明确枚举值，不用场景答案补全 |
| v7 枚举提示 B+ 单段 `pre_server_2b_v7_enum_bplus_smoke.jsonl` | `2af4b7931c302ef607fe380e2b5a36a3fca2c3a1fb5f1ce73350c79972679d4e` | 枚举格式改善，但 D/P/F 均臆称目标首末已完成，D2 判负；当时解析器将前三路判为缺完成转变 | v8 纠正“目标状态”和“新增进度”的混同；`pre_server_2b_v7_revalidation_v8.json` 保留重核后前三路结构有效但错误判零的事实，不覆盖旧原文 |

一次初跑误用了系统 `python`，没有 `torch`，只留下 `pre_server_2b_offset_full.jsonl` 配置头和终端导入失败；重试独立文件保留，未覆盖。v4 的 H0 逐秒曲线生成修订发生在该模型进程启动后，故旧 JSONL 中可能无 H0 曲线；云端冻结版脚本会在结构一致时写入该曲线，不回填旧结果。

**阶段判断**：2B 没有证明 P/F/H0 优于同预算直接提示，甚至给出明确反例。更重要的是，结构有效也无法排除两路共享的视觉幻觉；证据帧核验必不可少。8B 上若 D/P/F 仍不能形成有效且证据真实的输出，就停止新测试推理，报告候选方案未通过接口门槛；不因已制样而强跑付费测试。
