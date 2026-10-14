from pathlib import Path
from audit_sources import ROOT

status=ROOT/'research/status.md'
data=status.read_bytes()
heading='# 研究状态'.encode('utf-8')
assert data.startswith(heading)
intro='''

## 原生错题核查：尚无新 B 类缺口；ep513 已排除为 H-D 正例（D069—D071）

更新日期：2026-10-03。新报告：[宽任务基底的原生错题核查](native_task_gap_audit_20261003.md)。RoboMeter仍是宽机器人进展/奖励基底，Robo-Dopamine是同卷重要强比较；两者都不等同完整导航代理。作者Table6证实下降方向有残余错，Table8 RoboMeter历史依赖Falling准确率.901构成强反证；没有强法在本项目两个B候选上的逐例错误。先不选定新主缺口、不设计架构。

本轮实质材料进展：固定revision取得ep513全部19张发布帧及ep510/514各4帧。ep513第一项小瓶放置保持，第二项试管仍在杯中，排除为“后续成功附带破坏旧成果”正例，保留开发控制。27帧不是27任务；原媒体时钟/上游episode和许可尚未绑定，不进入模型推理。已追加data_manifest，仍S7-screening-4，全部相关视角/重复仅开发。

新增源码事实：R²VLM官方已有单样本递归推理/原始输出保存脚本，本轮补核到；不能继续把“未审推理入口”当发布缺失。权重/原图仍不齐，无模型运行。PRM工具默认居中曲线平滑不能代替Table6五帧因果差分评分；短区间、零标签和有效点分母未完全公开。ep513下降14—18在不同边界读法仅余0或1个帧点，实际评分掩码未知，不虚报错误率。RoboMeter正文OOD976与TableVII571口径也不能混用。

**唯一下一动作**：按固定RoboMeter客户端/服务端源码，为已有ep621下降22—28列出实际四帧输入及其原视频坐标，检查前后关系证据是否被采到；并列ep618保持锚。先排除采样/遮挡，不调用模型、不继续用H-D预筛。B1只是优先否定的诊断入口，H-D暂无正例；C取决于新增输出义务，加入失败执行本身不自动是C。

S6-draft-4、S7-screening-4、C1/C2/C3未批及阶段8关闭不变；run_ledger、08、协议和配置保持字节不变。39件来源合计5,402,835B，低于本批6MiB；[材料登记](sources/native_gap_audit_20261003/case_registry.json)、[验证](sources/native_gap_audit_20261003/validation.json)。以下D068及更早入口保留历史，当前行动顺序以上述为准。
'''.encode('utf-8')
if b'D069' not in data[:500]:status.write_bytes(heading+intro+data[len(heading):])

log=ROOT/'research/decision_log.md'
append='''

## 宽任务基底原生错题核验与反证材料（单执行者）

| ID / 日期 | 问题 | 备选项 | 决定 | 证据 | 适用范围 | 触发重审的新证据 |
|---|---|---|---|---|---|---|
| D069 / 2026-10-03 | 作者原生剩余错是否已定位到新的B类缺口 | 泛化Falling低分为旧成果错判；硬造逐条件标签；核原生分母与强反证 | 保留RoboMeter宽基底、Robo-Dopamine同卷强比较。Table6下降难是A；Table8 RoboMeter .901反对普遍不会撤销。新增失败执行不自动C，新增逐条件三值义务才是C。只保留B1短时旧终局关系撤销、B2 H-D待检卡；未选定研究主缺口，B1仅优先否定。RoboMeter OOD正文976/TableVII571不调和，RoboPulse原始0区间、端点、有效点分母继续标未知 | [新报告§1—4/6](native_task_gap_audit_20261003.md)；原文Table6/8、RoboMeter VI/VII/XXVII；[分母审计](sources/native_gap_audit_20261003/native_denominator_audit.json) | 证据定位与诊断优先级；不批准架构，不改协议/阶段 | 可绑定强法在同原生目标下的逐例错/对；作者评分器或分母清单；新材料反驳子类假设 |
| D070 / 2026-10-03 | ep513两段上升后下降是否支持后续成功附带破坏 | 仅凭标签纳入H-D；核全部发布帧及对象身份 | 19帧核到左小瓶放置后仍保持，目标试管仍在右杯中；排除H-D正例，保留后续未完成/旧成果保持控制。ep510/514各4帧也未证成后续成功及旧损坏。原标签不改，27帧不是27独立任务；三例原时钟/上游许可仍缺，仅开发。数据清单因新增材料追加但版本不变 | [报告§5](native_task_gap_audit_20261003.md)；[case registry](sources/native_gap_audit_20261003/case_registry.json)；固定HF revision和LFS SHA；原PNG/联系图 | 材料绑定、排除与可见性，单人判断；无监测器预测，不报子类错误率 | 原始完整视频/任务修订/独立复核改变观察；确切上游对应与许可；强法逐例输出 |
| D071 / 2026-10-03 | 是否继续以入口缺失阻塞，下一最便宜反证是什么 | 等作者或跑普通Qwen；核现有精确接口和输入证据 | 补核R²VLM官方单样本runner与raw_output保存路径，修正此前仅README的可用性审查；仍缺精确本机权重与原图。PRM默认居中平滑不是论文C.4因果差分评分，公开results仍.gitkeep。下一步只枚举ep621下降22—28及ep618保持锚的RoboMeter真实四帧输入/上游坐标，核证据是否被采到。零模型、零新权重/付费，不更新台账/08 | [报告§4/7](native_task_gap_audit_20261003.md)；R²VLM固定3b5c09ff树/runner，PRM固定34e8cd4的metrics/curves/cli，RoboMeter固定352d160服务器；[缺项单](sources/native_gap_audit_20261003/inference_readiness.json) | 接替D068下一入口；S6-draft-4/S7-screening-4，C1/C2/C3未批、阶段8关闭保持 | 输入核查后精确强法本地条件满足，才完整审核运行协议/资源；若采样或语义解释足够，收窄/放弃机制故事 |
'''
if '| D069 /' not in log.read_text('utf-8'):
 with log.open('ab') as f:f.write(append.encode('utf-8'))
print('status and decision log updated, historical bytes retained')
