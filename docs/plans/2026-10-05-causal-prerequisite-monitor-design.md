# 隐含前置条件 Monitor：候选设计与对照（待证伪）

日期：2026-10-05。状态：**研究设计草案，不是获批架构或有效性结论**。目标、输入权限和真值边界以[研究计划](2026-10-05-causal-prerequisite-monitor-research-plan.md)与[机制规格](../../research/prerequisite_monitor/mechanism_spec.md)为准。旧六段和六个已评分族只作开发诊断。

后续具体化见[架构与比较协议 v2](2026-10-05-causal-prerequisite-monitor-architecture-v2.md)：短事件输出＋共同进度渲染、命题级 H、强 D2、旧服务器 8B 权重边界及两个全新机制制样候选；仍是待证伪设计。

## 1. 科学问题与三路线

候选 P 只检验目标相关关系在视频动作前后的状态；F 只对同一视频问“若此时继续完成目标，与之前相比是更易、更难还是不变？有没有替代路线？”，必须指出帧证据；H 让 P 与独立上下文 F 相互质疑，仅一致且证据充分时给确定事件信用。D 是同底座直接输出相同结构与逐时进度。用户倾向 H，但只有当它相对 P、F 及同预算 D 有可重复增益时才选它。多代理、补看、事件验证、步骤图、先推理再给分本身均已有 ARS/ROVER/ProcVLM/R²VLM/PRIMO R1/ReKep 先例；CoINS 已研究反事实移障必要性。因此现阶段无“首次提出反事实前置条件”的新颖性主张。

| 候选 | 数据流 | 可证伪风险 |
| --- | --- | --- |
| D | 指令＋采样视频→同一输出接口 | 若 D 已正确，复杂结构无必要 |
| P | 目标/画面→候选关系→前/后状态及证据→事件信用 | 只认某颜色/托盘，或把关系满足误当固定控制器可达 |
| F | 动作前/后可行性问答→替代路径挑战→事件信用 | 幻觉后续视频、顺序偏置、把红块移动当改善 |
| H | P 记录→独立 F 尝试推翻→冲突时弃答，匹配时映射 | 额外 token/帧/弃答解释全部收益；F 只是复述 P |

## 2. 权限、输出和失败处理

单次方法输入仅 `instruction` 与当前编号视频的主视角帧。允许按同一视频时间窗/裁剪重看，任何工具只能读取 `model_input/<number>.mp4`；不把 `truth/`、六类标签映射、续行视频、旧分数或后验评分放入模型上下文。研发人员可在模型原始输出固定保存后，用真值层分析。复核证据帧要附原始索引/时间、可见区域、该帧支持的具体关系；提到视频外结果视为无效解释。状态为 `supported_positive/zero/negative/uncertain`，逐时进度与事件级 before/after/alternative/confidence/unknown_reason 同报。给 uncertain 时不得偷删样本或伪造零分，覆盖率与有效率分开统计。

伪代码：

```text
input(l, v[0:T])
sample a fixed low-cost frame set, retain decoded hashes
for each time t in requested grid:
    D: ask direct full-interface judgment on v[0:t] or full video with t marked
    P: infer goal entities and possible prerequisite from l plus seen scene
       verify relation before/after on cited visible frames; allow unknown
    F: independently compare before/after task continuation using same video
       ask for alternate route and what visual evidence would refute the claim
    H: compare P relation-change with F challenge
       if evidence incomplete/contradictory -> uncertain
       else assign bounded event credit and piecewise progress
save raw text, parsed event, every frame/time/hash, calls, tokens, failures
evaluate only after outputs are immutable
```

“反事实”是对**可能续行的质疑**，不是产生或观察物理反事实视频。模型不得报告精确 `C`。积分映射先只固定符号和有限上限，不用开发真值逐例拟合数值。G+ 直接目标完成必须给正向，N0 保持平稳；B0/U0 无根据的正向、H− 正向都算错误，未知计覆盖损失。

## 3. 同预算对照和低成本门槛

同一 Qwen3-VL-2B 本地权重作为**接口/诊断骨干**，不把其结果当主有效性实验。第一步只对两个已知开发族做小样烟测，固定统一帧索引（例如 0/3/6/9/14）、分辨率、贪心解码、schema 与 token 上限；记录输入/输出 token、视觉帧数、耗时、VRAM 和原始回答。P/F/D 各一次调用；H 用 P 和独立 F 两次。增加 D2：直接回答→同视频同 schema 的直接复核，两次调用，给与 H 相同的最大视觉/文本预算。预算不同的比较单列，不把 H 额外计算当方法优势。若 2B 在 G+/N0 上也大面积解析失败或幻觉，就停在接口诊断，不为凑完整结果耗时。

若烟测可解析，扩至所有 36 个开发视频和旧六段，记录全量正确、错、弃答、失败；做顺序交换/同义措辞敏感性和采样帧审计。开发结果只决定是否值得进入新集制样。正式强方法比较用届时仍可用的已租服务器及**已经可用的权重**；检查 ProcVLM、R²VLM、PRIMO R1 是否确能运行，不因列名就下载大权重。不可将 2B 与专用 7B/ARS 27B 的分数当架构差异；ARS 若官方源码仍不可用，标未运行。

## 4. 预注册预测与停机判据

1. 对可见的托盘占位，P 应把 B+ 判断为“占位→空”，B0“仍占位”，U0“前后空”，H−“空→占位”；若不能，是感知/关系错误而非信用映射不足。
2. 抓取入口只凭单目主视角可能不能验证夹爪路径；若 P/F/H 都高弃答，这是信息边界，不靠真值强迫模型猜。
3. H 应在**新机制完整六段**的 B+>B0/U0 与 H−<N0 上优于同预算 D2，同时 G+ 正向、证据帧有效、覆盖率相近。若只是用更多 token 或以高弃答换少错，否证 H 的有用性。
4. 如果 P 或 F 与 H 同样正确且预算更低，选简单者；如果 D2 已足够正确，停止复杂架构；如果 ARS 原版在新集正确，不宣称它不足。
5. 若视觉上无足够前置证据或可靠两种质不同机制不能完整制样，只报告开发诊断，不称盲测验证。

## 5. 新测试冻结和云端门槛

仅在开发诊断完成、提示/输出/预算/排序规则冻结后，制作**至少两种质不同新机制**、每个机制收齐 B+/B0/U0/H−/G+/N0。保持同初态、等时长空动作、固定续行策略与逐种子 `q_action/q_control/C`；评测文件与编号模型输入分离。先核可见性和解码帧哈希，再一次性冻结配置/门槛/提示/代码/权重/视频哈希。云端先只读检查现有租机可达性、剩余时间/GPU/磁盘/权重；一段 smoke 后整组六段运行，保存原始及失败，及时回收。主报告按场景配置/机制，不按帧或种子当独立样本。

**2026-10-05 诊断更新**：[本地 2B 记录](../../research/prerequisite_monitor/development/local_2b_diagnostic_20261005.md)已对开发族六段完成五帧烟测，以三段做15帧密度复核，并预登记同六段 512×384 原比例输入审计。P/F/H 仍未区分 B+/B0/U0/H−；高分辨率 D2 仅 1/6 格式有效。**阶段门槛未过**：ARS 原版无源码；可解析且同预算的较强骨干对照缺失；新场景未冻结。下一步唯一入口：先从通用视觉关系读取和结构化输出可靠性着手，登记新版本，再在**全部开发族**比较 P/F/H 与 D/D2；通过后才制样新机制。未解决反例：简单 D2、PRIMO R1、ProcVLM、R²VLM 或 ARS 可能已足够；抓取入口可能不可从单视频判定。
