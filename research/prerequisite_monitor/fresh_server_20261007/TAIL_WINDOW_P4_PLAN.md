# 剩余租期追加实验计划（2026-10-07，探索性）

## 当前事实与目标

P0、P1、P2 已本地封存。P3 的 16/16 次原生调用已完成，`local_results/p3/analysis_p3.json` 已生成；2026-10-07 11:58 UTC 本地重新执行 `seal_fresh_batch --verify --expected-count 4` 返回 `complete`、16/16、0 失败。执行者仍须确认服务商实际到期时间。此前记录的**保守 GPU 截止时间为 2026-10-07 12:40 UTC**，且每次运行还须预留至少 600 秒下载、核验时间；服务商界面时间优先。

P3 的预设静态末态比较（`N_o−N_b`）为：入口盒 TOPReward `+0.625`、Robometer `−0.00423`；承托板 TOPReward `−1.0`、Robometer `−0.02713`。四组 `G−N_o` 均为正。它提示“完成目标”容易被评分，但没有证明前置状态在静态画面中被稳定赋值；P3 是末尾画面重复形成的分布外输入，不是内部诊断。

本计划增加 **P4 原生 TOPReward 文本干预**，若时间允许再做 **P5 独立 Qwen 问答消歧**。两者都只作开发场景上的机制探索，绝不称 G2、未见泛化或内部因果证明。先冻结代码、输入、提示词、评分脚本和 SHA，再上机；不得看早期结果后改文本或挑条件。

## 首先处理 P3

1. 核对服务商剩余分钟和 UTC 到期时间；记录服务器 `date -u`、GPU 空闲显存、运行目录及本地时间。
2. 将 `local_results/p3/extra/p3/raw/`、`raw_seal.json`、日志保留双份。用现有 `pilot_pkg.seal_fresh_batch --verify --expected-count 4` 本地核对；确认 `analysis_p3.json` 的 seal SHA 与 `raw_seal.json` 相同。若失败，先抢救原始数据，停止新实验。
3. 租期最后十分钟不再启动任何 GPU 单元。如果实际剩余时间不足“预计运行 + 600 秒”，跳过对应追加项目；不要为了跑满时间牺牲原始产物下载。

## P4：同一原生 TOPReward 的文本干预（首选追加）

**问题：**当任务文字明确指出前置状态与最终目标的关系时，TOPReward 是否能把“只完成必要准备、蓝块未动”的视频排在阻挡/无关变化之上？这是对 P0 失败原因和可用研究方向的直接探查。它改变了任务文字，**不能**充当原始“只给最终目标句”设定的性能结果。

**输入和运行：**继续使用 P0 已封存的 18 段匿名视频和相同 Qwen3-VL-8B 权重、TOPReward 官方 runner、15 帧、解码与确定性配置。只在隔离复制的 `manifest.jsonl` 和 `instruction.txt` 改任务文字；两机制各九段统一使用同一文本，视频字节及逐帧像素哈希必须与 P0 完全相同。不得把本地 `truth/`、条件名、映射或评分器上传。每个变体独立输入目录与原始结果目录：`extra/p4/{neutral,causal_fact,credit_rule}/{access_gate,support_surface}`。不得覆盖 P0–P3。

固定三种干预；下文每条文字均接在原始目标句之后，并在同机制全部九段逐字一致：

| 变体 | 入口盒追加句 | 承托板追加句 | 作用 |
| --- | --- | --- | --- |
| `neutral` | `This short recording may end before the blue cube is placed. Judge the visible change in relation to the final goal.` | 同一句 | 控制“视频只是一段准备过程”的一般提醒 |
| `causal_fact` | `The box can be entered only through its top opening. That opening must be unobstructed before the blue cube can reach the box floor.` | `The marked elevated landing can support the blue cube only when the yellow sliding board is fully deployed beneath it.` | 给出因果关系，但不直接说如何奖励 |
| `credit_rule` | `The box can be entered only through its top opening. Fully opening it is useful progress toward this goal even while the blue cube remains outside.` | `The marked elevated landing needs the yellow sliding board fully deployed. Deploying it is useful progress even while the blue cube remains unmoved.` | 明示“必要准备也算进展” |

P0 原始目标句为既有基线。三个新变体共 **2 机制 × 9 视频 × 3 变体 = 54 次 TOPReward 原生调用**。P4 只调用 TOPReward，因为它在 P0 的两机制六个 `E` 配对均反向，诊断效率最高；此处不因结果好坏追加 Robometer。运行前必须完成 54 个输入的无模型 dry run、视频/像素哈希核对和每个变体两机制各一条 pilot；pilot 有异常即停止相应变体，保留全部失败。只读确认 TOPReward 仓库提交与权重路径仍和 P0 一致。不得修改官方源码或采样参数。

**预先固定的本地分析：**对每段仍用 P0 的 `末三帧中位数 − 首三帧中位数`，逐变体报告 `E>S`、`E>I_b`、`E>N_b` 六个方向和原始差值，以及 `H<I_o`、`H<N_o`、`G>N_o` 控制。比较每个变体与 P0 在相同视频配对上的原始差值变化；只增加所有视频共同偏置而不改变配对方向，不叫“救回”。不使用事后阈值或显著性检验。报告 neutral、causal_fact、credit_rule **全部**条件与失败，不能只展示转正配对。

**如何读结果：**

- `causal_fact` 已能让 `E` 对照转正且 `neutral` 未转正：说明这些视频和原生读出对明确的前置关系文字敏感，支持研究“显式因果任务表示”；不证明原始方法内部没有看见状态。
- 只有 `credit_rule` 转正：更像是需要直接给奖励规则；可研究状态识别与价值映射分离，但仍需新实验排除提示词风格效应。
- 三种都不转正而 `G` 仍正确：这条文字修补未救回原生评分；不能据此断言视觉、推理或头部哪一层是唯一原因。
- `neutral` 也转正：一般时间/任务框架提示就可能改变排序，不能把效应归给因果事实。
- `G` 控制失效或大量调用失败：先把干预视为破坏任务适配性，不作救回结论。

**封存：**每单元保留完整原生逐点曲线、最终给模型的指令原文与 SHA、输入 manifest SHA、视频和帧 SHA、调用耗时/错误、仓库提交/模型 revision、退出码。每变体独立 seal，先下载并本地逐文件 SHA 核对，再揭盲评分；远端保留副本。若现有 `seal_fresh_batch` 固定要求 Robometer 四单元，不要伪造占位数据；写一个只针对 P4 两个 TOPReward 单元的独立封存器与验封器，或使用可核验的逐文件 SHA 清单，scope 必须标为 `P4_TOPReward_instruction_intervention_exploratory`。

**时间门槛：**冻结和本地 dry run 后，按 pilot 实测每九段时间估算 54 次总耗时，另加至少 600 秒下载缓冲。若时间不足，按固定顺序 `neutral → causal_fact → credit_rule` 运行完整九段单元；不能只跑已知有利的 E。任何未跑单元明确标记未完成，不根据先前结果改变顺序。最晚在租期最后十分钟停止新调用。

## P5：独立 Qwen 问答消歧（仅在 P4 安全备份后有余时）

P1 的独立 Qwen3-VL-8B 对所有六段“末态已开放但蓝块未动”的视频回答不能完成，理由常把“视频中未完成”误当“从末态以后不能完成”。P5 用**同样 18 段原始视频、同样 0/2/4/6/7/8/10/12/14 秒九帧和 512×384 采样**，两个阶段各独立起问、互不引用答复：

1. **定点视觉状态**：入口盒逐段问 `At second 0 and second 14, is the top opening of the transparent box fully unobstructed, partly obstructed, obstructed, or unclear? Describe only visible lid geometry and cite supplied seconds.`；承托板逐段问 `At second 0 and second 14, is the yellow sliding board fully deployed beneath the marked elevated landing, partly deployed, parked away, or unclear? Describe only visible geometry and cite supplied seconds.` 这是给了结构线索的视觉探针，不能解释为模型自主发现关键结构。
2. **明确时间起点的可达性**：两机制统一问：`Final goal: {原目标句}\nBegin a NEW attempt only AFTER second 14. Ignore whether the blue cube moved during the recorded video. From the visible state at second 14, the robot may pick up, move and release the blue cube, but may not move the lid, yellow board, box or landing. Can the final goal be completed? Answer yes, no, already_done, or unknown. Give the visible route or blocker and cite supplied seconds. If visibility is insufficient, use unknown.`

两阶段各 18 次固定问答，先完整记录 raw、提示词 SHA、帧 SHA、解析状态和失败，再封存下载本地验哈希，最后本地揭盲。`already_done` 对 G，`yes` 对开放未完成，`no` 对阻挡未完成，`unknown` 单列；视觉状态按本地真值表人工核查，不用语义关键词自动美化。若视觉正确而可达性错误，提示关系/反事实推理瓶颈；视觉错误则提示关键几何识别瓶颈；若两者都正确而 P0 TOPReward 仍失败，只能提出“原生价值读出/时间信用分配”假设，**不能将此独立 Qwen 的回答当作 TOPReward 内部状态**。P5 的澄清问法可能本身救回 P1，因此不得把 P1 错误无条件说成基础模型缺乏因果能力。

P5 只有在预计全程耗时加 600 秒缓冲足够时才开跑。若不足，只做本地 P0/P3 已有曲线复核与报告，不再占 GPU。

## 不在本租期匆忙做的事

不生成新场景并立即当“独立复现”；不改变 P0 原始评分阈值，不追加随机重复来当新证据；不下载新权重、不另租服务器、不为了看到正结果迭代提示词；不把 P4/P5 写成 G2 或原生模型内部证明。正式强证据下一步是另行冻结的未见场景、独立任务几何与原生方法全流程评价。

## 给实施对话的提示词

请按 `D:\monitor2\research\prerequisite_monitor\fresh_server_20261007\TAIL_WINDOW_P4_PLAN.md` 执行剩余租期的追加实验。先确认服务商实际到期时间、P3 本地逐文件验封及备份。优先完成 P4 原生 TOPReward 三变体指令干预；仅在 P4 完整下载验封且仍有足够时间时做 P5 Qwen 问答消歧。所有新代码、输入、提示词、评分规则先在本地冻结并核 SHA；无模型 dry run、pilot、完整运行、远端封存、本地验封、揭盲评分按计划顺序做。不要改 P0–P3，不上传 truth/condition_map，不替换权重或官方方法，不根据中间结果改提示词。每次 GPU 启动前估时并留至少 600 秒下载缓冲，租期最后十分钟停止新调用。任何异常先保住 raw 和日志，明确报告完成/未完成项。最后给我原始差值、控制项、全条件结果和对应可支持/不可支持的研究判断。
