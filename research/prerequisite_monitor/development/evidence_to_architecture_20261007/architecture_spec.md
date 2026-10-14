# 版本化比较/输出规格 0.1.1（未冻结方法）

本规格固定**可比接口和本地无模型验证**，没有选定胜出的模型架构。改提示、解析规则、帧预算或标签映射均须升版本；旧 P0 原始数据和指标永不重写。正式 `METHOD_FREEZE` 只有在模型比较和审读通过后另行生成。

## 许可输入与隔离

单次推理仅有最终目标文字与当前回合主视角 RGB 准备动作视频；同一视频可按冻结秒数回看。禁止真值/条件号、仿真状态、固定续行控制器结果、旧模型输出/分数、成功示范、审读帧或人工 `causal_fact` 作为推理输入。运行器只指向 `model_input` 包；任何结果、评分器或期望值都在原答封存后由本地审计侧读取。输入视频/目标文字 SHA 与实际解码帧 SHA 都记录。

## 共同输出 JSON

每个候选 D/T/P/F/H 要产出相同语义字段；`null`/`unknown` 是合法不确定结果，不得用默认零掩盖失败。关系由目标和图像**自动**提出，名称/颜色/坐标不预置。

```json
{
  "spec_version": "0.1.1",
  "mid_second": 7,
  "goal_done": {"t0": "false", "t_mid": "false", "t14": "false"},
  "candidate_relation": {
    "entity": "model-proposed text or null",
    "region": "model-proposed visible region or null",
    "predicate": "one falsifiable visible relation or null",
    "satisfied": {"t0": "false", "t_mid": "true", "t14": "false"},
    "goal_relevance": "supported|refuted|unknown",
    "alternative_route": {"t0": "refuted", "t14": "refuted"}
  },
  "continuation": {"t0": "blocked", "t_mid": "possible", "t14": "blocked"},
  "evidence": [
    {"second": 0, "region": "visible region", "claim": "what this frame supports"},
    {"second": 7, "region": "visible region", "claim": "what this frame supports"},
    {"second": 14, "region": "visible region", "claim": "what this frame supports"}
  ],
  "uncertainty_reason": null,
  "direction": "unchanged"
}
```

上述只是**抽象合成示例**，不是 A/B 模板或场景答案。`mid_second` 必须是 7 或 8，且出现在 `evidence`；所有 `t_mid` 字段均指这个秒数。其他引帧秒数只能是本次真实解码的冻结集合。`goal_done`/`satisfied` 的枚举为 `true|false|unknown`；`continuation` 为 `possible|blocked|unknown`；`direction` 为 `beneficial|unchanged|harmful|completed|unknown`。`goal_relevance=supported` 表示画面关系和目标语义有关，不自动表示绝对必要；某端 `alternative_route=unknown` 时不得把它解释成“已排除”。源帧 SHA、模型/提示版本、解析状态和成本元数据由外部封存器补，不由模型自报。

## 读出逻辑（确定性，先于模型比较固定）

1. 严格 JSON/schema 解析失败记 `parse_failure`；原文保留，不修补为有效答案，覆盖率分母不减少。证据秒数越界、缺秒、与解码索引不符记 `evidence_invalid`，确定方向不能计为证据有效。
2. `goal_done(t0)=false` 且 `goal_done(t14)=true` 时 `completed` 优先；这是 G 控制。两端均已完成则净变化为 `unchanged`，另记 `already_done_at_start`；完成状态由真变假，若可见证据充分，记 `harmful`，否则 `unknown`。不能仅因蓝块尚未放到位将准备动作置零。
3. 未完成时，若相关关系、帧事实或初/末合法续行有冲突或未知，方向为 `unknown`，注明是遮挡、实体绑定、替代路线还是任务约束未定。可见关系 `false→true` 但仍可能有原先合法替代路线，也为 `unknown` 或 `unchanged`（只有替代路线得到正面证据时），不凭画面改观硬给分。
4. 在目标未完成且证据有效时，合法续行 `blocked→possible` 记 `beneficial`，`possible→blocked` 记 `harmful`，两端相同记 `unchanged`。关系主张只是支持这个判断的证据，不能由关系布尔值直接替代路线判定。
5. 中段另记事件，不能用最后一个峰值替代净结果。`blocked→possible→blocked` 需记录中段暂时正向、末段**回收全部准备信用**，最终 `unchanged`；`possible→blocked→possible` 同理。G 完成优先且不能被末段噪声撤销。
6. 有符号读出是 `−1/0/+1/completed/unknown` 的次序事件，不称未来成功概率，不与 TOPReward/Robometer 原始标度数值相减。报告成对胜/负/平与证据/覆盖/成本；不从开发集选择阈值来改 P0。

## 候选与公平预算

主层取现有 P5/P6 的 9 个实际秒数 `[0,2,4,6,7,8,10,12,14]`，每帧缩至 512×384；每视觉调用最多 384 新 token。D1 与合并 T/P1 各 1 调；D2 与 T/P2 各 2 调，第二调用可读第一调用**自己的**原答文本，不能读真值或别法分数。先试合并 T/P1；只有事实/续行错误定位后才开 T/P2；F/H 第三调若进入，给 D3 同权限，并作为单独预算层。记录每调实际输入/输出 token、帧数/尺寸、提示 SHA、视频和解码像素 SHA、耗时、峰值显存、原答及失败。名义上限相等不等于实际 token 完全相等，成本差单列。

旧 P6 direct 是 1 调开发诊断，不是按此 JSON 规格生成的 D1 新运行。旧 P5 visual/necessity 是分别起问，不能视为 T/P2 或 F/H 对照。TOPReward/Robometer 保持自身原生代码、权重、输出定义与 P0 评分；专用 ProcVLM/PRIMO R1 若原版权重已存在才作为独立强基线，不手写替身。

## 验收与更改门槛

审读时分列标签方向、可见事实、目标相关性、合法续行理由、证据秒数有效、unknown、平局、解析/运行失败。两机制九条件全报；E>S/I_b/N_b、H<I_o/N_o、G>N_o、R 中段/末段和 Robometer B E 3/3 正例必须保留。旧场景只回归错误类型，不把有争议真值当优化目标。最多两轮登记的开发机制诊断；选法后冻结提示/解析/预算/停止规则和哈希，再做真正未见 G2。
