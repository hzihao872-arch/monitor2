# P0–P6 逐案例证据图谱（开发材料，非 G2）

2026-10-07；只读重算与人工审读，不产生新模型输出。机器索引是 [`evidence_case_index.jsonl`](./evidence_case_index.jsonl)，每行保存原答、15 点曲线、源文件路径和 SHA-256、视频 SHA-256、解析状态、token/耗时及预期。用 `python research/prerequisite_monitor/development/evidence_to_architecture_20261007/build_evidence_index.py` 重建；[`evidence_index_manifest.json`](./evidence_index_manifest.json) 固定本次索引和分析文件哈希。**此索引含本地揭盲条件与预期，仅供审计，不得进入监测器输入或上传。**

## 身份、范围与复验

- 运行原有 [`verify_final.py`](../../fresh_server_20261007/local_results/verify_final.py)：3 个原生 seal、3 个 P1 seal、20 条文件哈希通过；P2 对 P0 的 540/540 原始逐点差为零，24 对无方向翻转。运行 [`verify_additional.py`](../../fresh_server_20261007/local_results/verify_additional.py)：P4/P5/P6 的 5 个 seal、5 个包、221 条文件哈希通过，90 条追加输出、0 模型失败。索引构建又逐案断言 P4 与 P0 的视频 SHA-256 和 TOPReward 模型路径一致。
- P0 原生 `raw_seal.json` SHA-256 为 `63eb941801fc64098a79185cd21b0e1c6d1357169fc8dd9f68ca06c96477f363`；P2 为 `88b8434632633feb7b66ad2497bffe6d37a6c6e23222e0110c4e09986f783966`；P3 为 `9a2bde3ea93f4f0c8515b623d4a2a963c42209466c92903da2c8cc339455aa89`。P4/P5/P6 各封存身份在 [`TAIL_DIAGNOSTICS_FINAL_zh.md`](../../fresh_server_20261007/local_results/TAIL_DIAGNOSTICS_FINAL_zh.md) 和索引中。P6 的 [`preflight.txt`](../../fresh_server_20261007/local_results/p6/direct/preflight.txt) 记录 TOPReward 提交 `4877a0ee...`、Qwen3-VL-8B 配置及四分片 SHA；Robometer 是另名的 PR #33 dtype 兼容运行，不能称为严格原版。
- P0 是冻结最终目标文字；P4 在**同视频同权重**上改任务文字；P5 提供结构名及指定秒数；P6 是单次直接问答。P1 是另一提示下的 Qwen 原答，P3 是末态静帧重复，均不代表原生方法内部推理，也不并入 P0 主指标。旧六段/旧场景有替代路线和构念限制，见 [`stage_A_error_map.md`](../architecture_next/stage_A_error_map.md)。
- P0/P4 的读出保持原指标 `median(12:14)−median(0:2)`；下表中的 TOPReward 与 Robometer 数值不可跨方法比较。`E/S/I_b/N_b/R/H/I_o/N_o/G` 分别为有效解除、假动作、无效受阻、受阻静止、解除后复原、新增受阻、开放无效、开放静止、真正完成。A 是盒顶入口，B 是承托板。

## 18 段逐案交叉表

表中数列依次为 **P0 TOPReward / P0 Robometer / P4 neutral / P4 causal_fact** 的窗口差值；`V` 是 P5 定点视觉初末状态，`×` 表示解析失败，`N` 是 P5 续行回答，`D` 是 P6 方向。`V` 有效并不表示状态正确，理由须查索引原答与[两张实际帧审读图](../../fresh_server_20261007/local_results/p1/P1_UNBLINDED_zh.md)。

| 案例/视频 | 预期初→末；续行 | 四个窗口差值 | V 初→末 | N | D | 最早可支持的输出问题或反例 |
| --- | --- | --- | --- | --- | --- | --- |
| A E/0007 | blocked→ready；yes | −3.500 / +.047 / −3.250 / −2.500 | × | no | unchanged | 末帧开口可见；P5 necessity/P6 均错过有用解除，P5 visual 原文还把开口判 blocked。 |
| A S/0003 | blocked→partial；no | −2.875 / +.036 / −3.125 / −2.500 | × | no | unchanged | 标签正确但视觉无有效结构化状态；不能据此证实前置理解。 |
| A I_b/0006 | blocked→blocked；no | −3.125 / +.056 / −2.125 / −3.750 | ready→ready | yes | unchanged | P5 把封闭入口读成 ready，并由此错误允许续行。 |
| A N_b/0009 | blocked→blocked；no | −2.625 / +.095 / −2.250 / −1.375 | × | yes | unchanged | P5 原答把封闭盖称可进入，视觉/续行都不可靠。 |
| A R/0005 | blocked→blocked；no | −3.375 / +.026 / −3.125 / −2.625 | ready→blocked | no | unchanged | 末态可见复原，V 初态错；D 净标签对但称无相关变化。 |
| A H/0008 | ready→blocked；no | −3.750 / +.026 / −3.375 / −2.875 | × | no | unchanged | 新增盖阻挡可见；D 漏报 harmful，理由偏向蓝块未动。 |
| A I_o/0004 | ready→ready；yes | −2.625 / +.044 / −1.500 / −2.750 | × | yes | unchanged | N 正确；P1 同案却答 no，提示措辞/判断不稳。 |
| A N_o/0001 | ready→ready；yes | −1.750 / +.095 / −2.375 / −1.250 | × | yes | unchanged | N 正确，但 visual JSON 无效；不能从标签反推视觉状态稳定。 |
| A G/0002 | ready→ready；already_done | +2.750 / +.733 / +.875 / −1.500 | × | yes | completed | P6/P0 正向；P5 把已完成答成可续行，P4 causal 的 G>N_o 变 −.25。 |
| B E/0008 | blocked→ready；yes | −1.875 / +.274 / −1.250 / −1.375 | ready→ready | no | unchanged | B 的 Robometer E 三对全对；P5 初态误读、N/D 均错过部署价值。 |
| B S/0006 | blocked→partial；no | −.625 / +.115 / −.500 / −1.000 | ready→ready | no | unchanged | V 把未到位承托读为 ready；N/D 标签虽对，理由不能证明机制。 |
| B I_b/0004 | blocked→blocked；no | −1.625 / +.080 / −1.375 / −1.875 | ready→ready | no | unchanged | V 双端错，N/D 标签对。 |
| B N_b/0007 | blocked→blocked；no | −1.750 / +.169 / −1.000 / −1.750 | ready→ready | yes | unchanged | P5 把远端黄板读为可承托，续行亦错。 |
| B R/0009 | blocked→blocked；no | −1.500 / +.063 / −.750 / −.875 | ready→ready | no | unchanged | 中段部署、末段收回；D 净标签对而理由称无相关变化。 |
| B H/0005 | ready→blocked；no | −1.750 / +.121 / −.875 / −2.375 | ready→ready | no | unchanged | 末帧失去承托；V/D 漏报 harmful。 |
| B I_o/0002 | ready→ready；yes | −1.875 / +.073 / −.625 / −2.125 | × | no | unchanged | P5 N 错把未搬蓝块/固定结构当不能续行。 |
| B N_o/0003 | ready→ready；yes | −1.500 / +.143 / −1.125 / −1.625 | ready→ready | yes | unchanged | 开放静止正例；不因 E 改善牺牲此锚点。 |
| B G/0001 | ready→ready；already_done | +3.000 / +.670 / +1.875 / −.875 | × | yes | completed | P0/P6 识别完成；P5 已完成枚举错，P4 causal 仍 G>N_o +.75。 |

上述 P5 `V` 的 9/18 有效、初态精确 2/18、末态精确 3/18；这三项是冻结解析器对**全部 18 段**的计数，解析失败不人工补值。P5 necessity 18/18 可解析、10/18 精确，E 两段都错，G 两段均把 `already_done` 答 `yes`。P6 18/18 可解析、14/18 标签匹配，但这 14 个恰为 12 个 unchanged 与 2 个 G，E/H 为 0/4。P1 两问独立，其六个开放未完成 E/I_o/N_o 均答 `no`，多数以未搬蓝块为由；所以 P1/P5 的表面正确率都不能充当可靠机制解释。

## 成对判别与 P4 的 G 保护

| 机制/方法文字 | E>S | E>I_b | E>N_b | H<I_o | H<N_o | G>N_o |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A TOPReward P0 | L −.625 | L −.375 | L −.875 | W −1.125 | W −2.000 | W +4.500 |
| A Robometer P0 | W +.010658 | L −.009157 | L −.048707 | W −.017741 | W −.068623 | W +.638271 |
| B TOPReward P0 | L −1.250 | L −.250 | L −.125 | L +.125 | W −.250 | W +4.500 |
| B Robometer P0 | W +.158877 | W +.194029 | W +.104757 | L +.048405 | W −.021881 | W +.526648 |
| A P4 neutral | L −.125 | L −1.125 | L −1.000 | W −1.875 | W −1.000 | W +3.250 |
| B P4 neutral | L −.750 | W +.125 | L −.250 | W −.250 | L +.250 | W +3.000 |
| A P4 causal_fact | T 0 | W +1.250 | L −1.125 | W −.125 | W −1.625 | **L −.250** |
| B P4 causal_fact | L −.375 | W +.500 | W +.375 | W −.250 | W −.750 | W +.750 |

`neutral` 说短录像可能止于放置前，要求对最终目标判断可见变化；`causal_fact` 在 A 明写“只能经盒顶、入口先通畅”，B 明写“黄板部署才承托”。相对于 P0，neutral 的 E 优势仅 1/6；causal_fact 为 3/6 加 1 平局，**同时 A 的 G 对照失配**。九条件都在索引中，没有仅挑 E。两种文本的长度、语法和语义也同时变化；P4 只证明原生数值对任务文字敏感，不能证明文字促成自主关系发现，亦不能把 P4 算作原生 P0。TOPReward 的[论文定义](https://arxiv.org/html/2602.19313)是前缀下 `True` 完成陈述的分数；本地 `qwen.py:205–279` 和原答每前缀 `prefix_token_counts=1` 与此相符。该读出目标与“未来合法续行变易”不同，但黑箱曲线不足以定位内部感知步骤。

## 四种问题的可定位边界

1. **看错状态**：P5 的 A E/I_b/N_b、B E/N_b/H/R 等原答与相应 0/7/8/14 帧矛盾；即使 JSON 有效也存在事实错。P6 E/H 的“无相关变化”理由亦与可见结构变化冲突。这是*输出证据*错误，不能归给 TOPReward/Robometer 的隐藏状态。
2. **判断错续行价值**：P5 的 E 两段 `no`、B I_o `no`，以及 G 的 `yes` 而非 `already_done`，体现该独立问答在“能继续”和“已完成”上不稳。但 P5 visual 与 necessity 分开起问，无法证明其必要性错是先看对了状态再推错。
3. **进度读出不合适**：P0 TOPReward 两机制 E 优势 0/6，G 都强正向；P4 同视频改文字使 E 部分恢复却伤及 A G；P3 静态 G−N_o 四组均正，N_o−N_b 不稳。这些支持检验“完成相容性读出≠准备价值”的假说，不证明内部没有关系表征。Robometer B E 3/3 是反例。
4. **证据不足/无法归因**：原生分数无关系原答；P5 9 个 visual JSON 失败；旧 s01/s02 等未排除替代路线。对这些只能记 `not_localizable`、`unknown` 或构念争议，不能把分数失配写成确定的视觉/因果内部失败。R 需与各自静止锚点比较，中段绝对峰值不可单独视为成功撤销。

## 输入隔离

只有匿名视频与目标文字可给监测器。条件代号、期望关系、续行真值、审读图、旧输出/分数、本索引及本地视频 SHA 映射属于审计侧。所有 A/B、P1/P3/P4/P5/P6 和旧场景都已暴露，只是开发材料。没有本轮 G2 结果。
