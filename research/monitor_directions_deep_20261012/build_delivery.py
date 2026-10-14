"""Assemble this research delivery from the reviewed evidence; no model execution."""
from pathlib import Path
import csv, json, re

ROOT = Path(__file__).resolve().parent
report = ROOT / 'REPORT_zh.md'
s = report.read_text(encoding='utf-8')
if '进入训练前，另做oracle下游价值诊断' not in s:
    s = s.replace('随后仅在确认存在可重复错误的子类上比较训练预算：', '进入训练前，另做oracle下游价值诊断：用独立人工关系标签筛选固定混合池，按相同保留动作数训练同一BC配方，比较随机筛选和既有reward筛选。这是后续实验建议，本轮未执行；若oracle也无益，先改下游接口或数据分布，不把Monitor精度当最终价值。随后仅在确认存在可重复错误的子类上比较训练预算：')
if 'eVTA0完整方法还用冻结V-JEPA2' not in s:
    s = s.replace('终局TD、提示校准、密度比支持集、局部偏好归因是不同强对照。', 'eVTA0完整方法还用冻结V-JEPA2表征构造失败样本的软标签，不能把所有结果简化为纯二元终局TD。终局TD、提示校准、密度比支持集、局部偏好归因是不同强对照。')
s = s.replace('| 动作条件状态预测 | 当前历史+action/skill→短期状态 | 指定后果/风险 | 真正新增行动权限；ContactGuard/Foresight近邻 |', '| 动作条件预测表征/后果 | 当前历史+action/skill→未来latent或后果 | 指定后果/风险 | 新增待执行动作信息访问权限；ContactGuard/Foresight近邻 |')
s = s.replace('因此“冻结world model+小头”高度重合，各方法的实际预测时点必须分开。', '“冻结预测器+小头”与ContactGuard/FARM高度重合。Foresight训练动作条件predictor和failure Transformer；FoMo-FD训练flow/VAE，不能合称完整world model冻结。各方法的训练范围和实际预测时点必须分开。')
s = s.replace('首轮比较：current RGB direct head；当前latent head；未来latent head；', '首轮比较：current RGB+同样action/skill的direct head；当前latent+同样action/skill的head；未来latent head；')
s = s.replace('在风险尚未可见的时间点预测', '在失败后果尚未发生或被观测、且仍可干预的时间点预测；当前可见风险前兆允许作为输入')
for identifier,version in [('2412.04455','v1'),('2510.10975','v1'),('2406.18043','v2')]:
    s = re.sub(r'(https://arxiv.org/abs/'+re.escape(identifier)+r')(?:v\d+)*', lambda m:m[1]+version, s)
report.write_text(s, encoding='utf-8')
rootnote = ROOT / 'evidence_root.md'
s = rootnote.read_text(encoding='utf-8')
snapshot_count=sum('error' not in r for r in json.loads((ROOT/'SOURCE_MANIFEST_root.json').read_text(encoding='utf-8')))
s = re.sub(r'\d+项下载成功', str(snapshot_count)+'项下载成功', s)
s = s.replace('ImagineNav++ v1首发2025-12-19（以abs历史为准），未来视图生成+候选选择+记忆；', 'ImagineNav++首发2025-12-19，本轮另核查v3（2026-04-30）：训练Where2Imagine选择视图，配合Novel View Synthesis和记忆；')
s = s.replace('https://arxiv.org/html/2512.17435v1', 'https://arxiv.org/html/2512.17435v3')
s = s.replace('ProgressLM讨论answerability', 'ProgressLM先读v1，另核查v2（2026-05-21），讨论answerability').replace('https://arxiv.org/html/2601.15224v1', 'https://arxiv.org/html/2601.15224v2')
rootnote.write_text(s, encoding='utf-8')

# Fields are explicit so the CSV remains useful for later re-audits.
fields = ['id','direction','work','problem','input','output','supervision','mechanism','update','downstream','overlap','remaining_distinction','decisive_test','evidence','source']
rows = []
def row(id,d,w,p,i,o,s,m,u,t,over,dist,test,e,link):
    rows.append(dict(zip(fields,[id,d,w,p,i,o,s,m,u,t,over,dist,test,e,link])))
row('M01','A','ARS','离线任务进度与退步','目标+全轨迹；允许未来证据','事件、证据核验、局部progress','免训练；终局辅助可选','事件账本+重新取证+独立上下文核验','推理中证据修订；无权重训练','动作块筛选→BC','高度重合：原事件/核验/撤销链','严格前缀在线权限、同预算关系监督迁移仍待证；改权限不是新方法','原版/前缀适配版分列；同输入和预算比较','论文§3/4、Fig.2、固定公开源码','https://arxiv.org/html/2609.34484v1')
row('M02','A/C','RoboMonitor','少标注runtime监测','视频历史；预训练另用动作/未来','进度、成功、失败等读出','预测/逆向/掩码表征预训练+temporal SFT','预测表征学习后部署监测','离线训练；部署丢弃预测器','四项监测评测；两项恢复闭环','高度重合：少数据训练+预测表征+monitor','目标关系有效时段与跨目标监督价值未确认','同标注分钟；当前直接头/预测表征；闭环净成本','全文方法/实验及附录；四任务不等于四闭环','https://arxiv.org/html/2609.30715v1')
row('M03','A','Robometer','通用reward','目标+轨迹','进度、成功、偏好','混合成功/失败及trajectory comparisons','多监督reward模型','离线SFT','筛选、IL/RL评价','高度重合：小数据reward方向的强模型对照','可撤销对象关系和高分错误子类；非已有能力不存在','冻结公开模型先盲测；同保留量BC','论文v2；公开代码/模型条目','https://arxiv.org/abs/2603.02115v2')
row('M04','A/配套','RoboReward','通用结果reward','目标文本+视频','1–5结果reward','目标重标、temporal clipping等负例','VLM reward训练','离线训练','reward评价/策略用途','高度重合：目标重标与截断造负例','物理可靠编辑标签及关系有效时段价值','同审核分钟真实留出；成功goal重标不自动成物理负例','全文v2；官方HF数据/模型','https://arxiv.org/html/2601.00675v2')
row('M05','A','WARP-RM','非单调进度和坏片段筛选','冻结视觉特征+时间序列','signed progress velocity','warp/rewind合成时序','相对速度奖励；默认双向、代码可因果','离线小模型训练','数据筛选→BC','高度重合：回退负进度+筛选','真实正向执行中的条件撤销/必要恢复标签价值','warp/retry强对照；同保留预算；因果与双向分列','v4正文/附录及官方代码','https://arxiv.org/html/2606.28320v4')
row('M06','A/B','ReTVL','成功中的退步与重试','轨迹+retry关键点','非单调value','稀疏人工retry标注','局部下降/恢复价值学习','离线训练','加权BC','高度重合：局部监督非单调值+BC','非retry条件失效及跨目标关系；其排除项是候选缺口非新领域','retry监督 vs 关系监督同标注分钟；保留有效恢复','v2§3、App.C.1','https://arxiv.org/html/2606.24633v2')
row('M07','A','ConditionNET','技能前提/效果监测','当前RGB+当前skill文本+执行phase','precondition/effect/neither','技能条件标注','神经条件分类+BT监测','离线训练','异常时暂停/恢复控制','高度重合：前提/效果Monitor','多目标可撤销关系时段与输入权限迁移未确认','允许skill对照；只RGB不得继承技能成功真值','LRA正文；最早IEEE公开2024-12-23','https://doi.org/10.1109/LRA.2024.3520916')
row('M08','A','RAFAIL','任务相关关系异常','点云object pairs+policy特征','异常与progress/importance辅助量','离线VLM语义标注+成功支持分布','关系表征+policy辅助头+RND gate','离线训练','运行期异常检测','部分至高度：关系监测已有','RGB/goal权限不同；细微可见条件失效非已证缺口','成功分布内异常；点云oracle和RGB输入分列','v1§III及消融','https://arxiv.org/html/2609.18324v1')
row('M09','A','LRM','progress/completion reward','当前图可带初帧anchor；前后对比可加初帧','absolute/contrastive/completion','示范及时间/结果监督','多reward heads','离线训练','sim PPO；真实weighted BC','高度重合：加多字段/多reward组合','额外关系字段是否独立有益','单头/组合、同数据/成本；不能仅字段更多','v3正文/附录','https://arxiv.org/html/2603.16065v3')
row('M10','A/C','Robot Critics that Sweat the Small Stuff','细粒度critic与想象筛选','匹配初态视频对+生成候选','pairwise preference/score','同初态成功失败、成功时序对','微调critic','离线SFT','imagined候选选择','高度重合：小训练critic+世界模型候选评价','有效时段监督及错对象/假抓取诊断价值','matched pair预算；真实未来与生成未来差距','v1方法/实验/局限','https://arxiv.org/html/2606.21572v1')
row('M11','A/全局','CriticHack','reward优化中的错对象漏洞','目标+执行结果/视频','reward与task verifier','已有reward模型及目标专用verifier','审计高分错误；verifier干预','优化策略；非新通用Monitor','RL和真实执行审计','高度重合：加独立verifier修补reward','对象关系时段泛化与监督预算；真实显著性未充分分辨','高分尾部wrong-object；verifier-only；独立终局判定','v1§5–8/附录E','https://arxiv.org/html/2610.02527v1')
row('M12','B','HiRE','执行结果改善reward','冻结视觉特征+成功失败support库','KDE density-ratio potential','离线成功、在线终局结果；正库可多帧配置','非参数support更新+potential shaping','更新库/KDE，不是weight TTT','DICE-RL','高度重合：反馈不断改善reward','可信局部反馈义务和参数更新净价值待证','buffer/小头同反馈分钟；不要声称其不能回退','v1§4/6/附录；官方docs/源码','https://arxiv.org/html/2609.27068v1')
row('M13','B','Demo2Reward','少示范reward prompt优化','3–10示范及VLM评价','per-step成功reward prompt','外部meta-critic评价与示范','test-time prompt search','prompt更新；策略训练前冻结','policy RL','高度重合：监督者提示适应','部署流中的局部纠错与遗忘，不是改prompt即新颖','同反馈预算prompt vs adapter vs support','v1方法/附录；官方prompt/RL代码','https://arxiv.org/abs/2606.00083v1')
row('M14','B','eVTA0/RLER','无示范success-probability reward','目标+视频窗口+rollout结果','中间成功概率','终局TD/EMA；V-JEPA2特征软失败标签','Qwen3-VL LoRA+reward token/head','reward随policy rollout更新','交替reward学习/策略RL','高度重合：终局TD+LoRA+交替RL','稀疏合法局部监督、反馈归属和跨任务净收益','同数据/优化steps；终局TD强对照；不能只二元简化','v1§3/Alg.1/附录；官方代码及HF资产','https://arxiv.org/html/2609.33653v1')
row('M15','B','GCR','成功失败驱动goal reward','goal/视觉状态+在线反馈','implicit value/goal reward','成功失败与contrastive/value监督','goal-conditioned reward学习','部署反馈更新','机器人policy优化','高度重合：成功失败反馈reward','合法局部标签和旧任务稳定性待证','GCR类baseline；终局失败不重标所有中间事实','v2正文；外链附录未全读','https://arxiv.org/abs/2410.19989v2')
row('M16','B','PACT','intervention信用分配','轨迹+人工动作介入','progress/counterfactual Q','全轨迹进度及人工intervention','局部归因/策略改进','reward与policy训练','五项真实任务','高度重合：局部反馈和纠错归因','本项目若无action intervention不可继承其监督权限','feedback权限匹配；随机复核/动作介入分列','v2§3–6及附录；匿名代码未读成功','https://arxiv.org/html/2606.03949v2')
row('M17','A/B','SOLE-R1','因果video reward与退步','当前prefix；训练teacher可读privileged sim','dense progress/CoT reward','仿真状态teacher、真实t/T、反转负进度','reward蒸馏/全参训练','离线训练；部署reward固定','reward与policy用途','高度重合：事实teacher/反转退步','未来可见证据如何合法形成局部标签及stream适应','teacher权限分列；固定训练/在线适应；time-order强对照','v2§3/App.J,K；官方model仓库','https://arxiv.org/html/2603.28730v2')
row('M18','B','TTT/Tent/CoTTA','测试分布适应','测试样本/连续流','自监督或预测分布改进','辅助自监督/entropy/teacher','测试梯度适应、EMA与防遗忘','encoder/head等参数','通用视觉非机器人reward实证','部分重合：TTT/持续适应名称已成熟','任务反馈义务和机器人接口是应用区别非自动方法贡献','entropy可放大语义错误；matched静态/累计重训','原始论文方法；无直接机器人结论','https://proceedings.mlr.press/v119/sun20b.html')
row('M19','C','ContactGuard','pre-contact风险避免','当前history+待执行action chunk','未来latent/probe risk/abort','少量precontact标签','动作条件预测+probe','复用预测器；小头训练','执行前abort','高度重合：预测latent+小头+预警','跨技能关系后果/恢复是能力扩展，方法新颖性未确认','current+同action；shuffle/zero/reverse；总恢复成本','v1方法/动作消融','https://arxiv.org/html/2608.13438v1')
row('M20','C','FARM','VLA内部状态失败读出','冻结VLA-JEPA内部预测state','failure score','任务成功失败','33985参数readout；causal max','小头训练；内部模型冻结','运行监测','高度重合：冻结预测表征+小头','关系后果和恢复用途未确认','current state vs predictive state；跨policy/未见task','v1方法；官方repo当前Coming Soon','https://arxiv.org/html/2609.11445v1')
row('M21','C','Foresight','提前终局失败预测','视觉prefix+下一action chunk','未来latent→terminal failure','逐时刻终局标签','训练action predictor+causal failure Transformer','冻结视觉encoder；预测器/head训练','失败预警','高度重合：动作条件未来表征+failure head','可解释关系和候选恢复是额外义务','同action当前direct head；提前量和可干预率','v1全文','https://arxiv.org/html/2606.23085v1')
row('M22','C','FoMo-FD','动作转移异常','过去+动作+已观测endpoint','inverse-transport nonconformity','成功轨迹支持分布','训练flow/VAE；conformal检测','离线模型训练','runtime转移异常','部分重合：world model anomaly已有','不等同未来预警；预测时点不同不能混成同任务','observed endpoint vs true future权限分列','v1方法','https://arxiv.org/html/2607.27511v1')
row('M23','C','STRIPS-WM','视觉高层规划与条件','image goal+闭合scene graph+high-level action','predicates、pre/add/delete effects','视觉动作转移与负applicability','graph-grounded operators','离线学习','高层规划','高度重合：条件建立与撤销/WM','RGB前缀和技能风险权限不同，泛化未确认','负适用性监督；graph oracle与RGB输入分列','v1§3、App.RQ4','https://arxiv.org/html/2606.06832v1')
row('M24','C','CaM / RoVer','主动约束监测/动作验证','CaM多视角3D；RoVer policy候选action','约束违反/候选分数与细化','视觉模型/示范动作误差与偏好','代码时空约束/PRM搜索','CaM模块训练；RoVer评价/搜索','主动监测/固定VLA细化','高度重合：约束+动作验证','现有接口外的恢复义务；不同输入不得直接比','观测与候选成本匹配；无需WMselector','CaM读v1、RoVer读v1；最新版分列','https://arxiv.org/abs/2510.10975v1')
row('M25','C','World-Gymnast / GenRL','想象中评价/训练policy','兼容动作空间的生成/latent WM','imagined reward/rollout','预训练WM与任务目标','imagined evaluation/RL','policy及方法部件训练','世界模型中的策略训练','高度重合：WM给reward/策略优化','物理可靠关系后果和真实恢复泛化未确认','动作规范兼容；真实/生成未来；phantom grasp审计','World-Gymnast v1、GenRL v2及代码','https://arxiv.org/abs/2602.02454v1')
row('M26','C/B','Sirius Runtime Monitor','latent rollout失败与反馈','机器人history/learned dynamics','failure forecast','历史执行/部署反馈','runtime failure prediction/update','监测器部署反馈更新','runtime帮助与接管','高度重合：预测monitor并从执行改善','反馈合法性和关系恢复义务待证','同feedback静态/更新；提前量与额外干预','2023论文/project；后续repo不作原版等同','https://arxiv.org/abs/2310.17552')
row('M27','配套','UniGoal / ImagineNav++ / ProgressLM','图匹配/视图选择/answerability','posed RGB-D/goal image/参考示范等','目标核验/下一观察/进度','导航数据、view selection训练等','关系匹配/撤销记忆/新视图想象','各自离线训练；非直接机器人适应','image-goal navigation/进度评价','部分重合：可借机制，非同接口','动态关系需可撤销记忆；新视图不等于物理未来','无/永久/可撤销记忆；oracle crop/pose单列','读版本和权限见来源清单','https://arxiv.org/html/2512.17435v3')
with (ROOT/'overlap_matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader(); writer.writerows(rows)
md=['# Monitor研究方向的逐项重合矩阵','', '核查日：2026-10-12。判定针对候选贡献措辞；高度重合不表示全部能力或实验已经相同。下表是人工证据综合，未运行任何方法。完整输入、输出、监督、机制、更新与下游字段见[CSV](overlap_matrix.csv)。', '', '## 七维比较', '', '| ID/主线/工作 | 问题；输入→输出 | 监督；机制；更新 | 下游与重合判定 |', '|---|---|---|---|']
for r in rows:
    md.append(f"| {r['id']} / {r['direction']} / [{r['work']}]({r['source']}) | {r['problem']}；{r['input']} → {r['output']} | {r['supervision']}；{r['mechanism']}；{r['update']} | {r['downstream']}；**{r['overlap']}** |")
md += ['', '## 剩余区别与能推翻候选的对照', '', '| ID | 尚未确认的区别 | 决定性对照/降级检查 | 证据边界 |','|---|---|---|---|']
for r in rows: md.append(f"| {r['id']} | {r['remaining_distinction']} | {r['decisive_test']} | {r['evidence']} |")
md += ['', 'A优先来自当前数据/接口基础及可诊断性，不能从本矩阵推出已发现文献空白。B的终局TD/提示/非参数更新已有近同工作；C的预测表征与预警已有近同工作。真正剩余的候选是监督义务、预算价值、迁移与恢复后果，须由新实验支持。RSI不在候选范围。', '', '更细阅读记录：[A](evidence_a.md)、[B](evidence_b.md)、[C](evidence_c.md)、[ARS与跨主线核查](evidence_root.md)。']
(ROOT/'OVERLAP_MATRIX_zh.md').write_text('\n'.join(md)+'\n',encoding='utf-8')

# Bibliographic aliases deliberately retain the paper's checked version and access level.
sources=[]
def source(key,alias,arxiv,first,read,current,status,level,locator,note,asset=''):
    url = f'https://arxiv.org/abs/{arxiv}{read}' if arxiv else asset
    sources.append(dict(id=key,alias=alias,arxiv_id=arxiv,first_public_date=first,read_version=read,current_checked_version=current,publication_status=status,evidence_level=level,locator=locator,availability_note=note,url=url,official_asset_url=asset,checked_date='2026-10-12'))
source('S01','ARS','2609.34484','2026-09-28','v1','v1','arXiv预印本','正文+源码','§3/4、Fig.2、App.B；evidence_root.md','推理/审计/采集等源码已公开；全部BC流水线/原始评测数据未确认；固定commit 0b61a5de0c39af1788d960ea8dd996aa76b27f7f','https://github.com/midea-ai/ars/tree/0b61a5de0c39af1788d960ea8dd996aa76b27f7f')
source('S02','RoboMonitor','2609.30715','2026-09-25','v1','v1','预印本/投稿中','正文/附录','evidence_a.md；evidence_c.md','未确认官方可下载完整代码/权重/数据；四监测评测、两闭环')
source('S03','Robometer','2603.02115','2026-03-02','v2','v2/2026-05-13','RSS2026','正文+源码','evidence_a.md','代码、4B模型及processed_datasets可见；项目Coming Soon文字不等同全资产未公开','https://github.com/robometer/robometer')
source('S04','RoboReward','2601.00675','2026-01-02','v2','v2/2026-01-08','arXiv预印本','正文+资产元数据','evidence_a.md','HF数据和8B模型条目公开；未下载模型','https://huggingface.co/datasets/teetone/RoboReward')
source('S05','WARP-RM','2606.28320','2026-06-26','v4','v4/2026-09-06','arXiv预印本','正文+源码','evidence_a.md','官方源码与示例模型数据公开；默认双向但有causal代码','https://github.com/uynitsuj/WARP-RM')
source('S06','ReTVL / Beyond Monotonic Progress','2606.24633','2026-06-23','v2','v2/2026-07-06','arXiv预印本','正文/附录','§3/App.C.1；evidence_a.md','未确认官方完整代码/权重/数据；明确排除复杂/失败retry等')
source('S07','ConditionNET','2502.01167','2024-12-23 IEEE；2025-02-03 arXiv','v1','v1','IEEE RA-L；DOI 10.1109/LRA.2024.3520916','正文+项目','evidence_a.md','项目数据入口可见；实现/权重未确认','https://dsliwowski1.github.io/ConditionNET_page/')
source('S08','RAFAIL','2609.18324','2026-09-16','v1','v1','arXiv预印本','正文/附录','§III/消融；evidence_a.md','未确认官方代码/权重/数据')
source('S09','Robot Critics that Sweat the Small Stuff','2606.21572','2026-06-19','v1','v1','arXiv预印本','正文+项目/代码入口','evidence_a.md；evidence_c.md','官方代码入口公开；没有复现想象候选选择','https://github.com/SruthiSudhakar/robocritic')
source('S10','LRM / Large Reward Models','2603.16065','2026-03-17','v3','v3/2026-09-30','arXiv预印本','正文+源码','evidence_a.md','官方实现与adapter模型条目可见；仿真训练仅一训练checkpoint，不能把评测seeds当训练重复','https://github.com/physical-superintelligence-lab/Large-Reward-Models')
source('S11','CounterAlign','2608.21740','2026-08-22','v1','v1','arXiv预印本','正文','evidence_a.md','项目读取失败，资产未确认，不能断言无代码','https://counteralign.airoa.io/')
source('S12','CriticHack','2610.02527','2026-10-01','v1','v1','arXiv预印本','正文/附录','§5–8/App.E；evidence_a.md；evidence_root.md','未确认官方仓库；真实40次/条件不能外推显著改善')
source('S13','SARM','2509.25358','2025-09-29','v4','v4/2026-04-27','ICLR2026（分支核查）；arXiv无venue注释','正文+代码入口','evidence_a.md','先深读v2，再补核v4实现/消融/RA-BC/RA-QL；无逐字diff；opensarm含SARM2，后者未独立审计','https://github.com/xdofai/opensarm')
source('S14','ReWiND','2505.10911','2025-05-16','v2','v2/2025-09-19','arXiv预印本','正文+源码入口','evidence_a.md','官方代码公开；本轮未运行','https://github.com/rewind-reward/ReWiND')
source('S15','Relational Learning for Skill Preconditions','2012.01693','2020-12-03','v1','v1（本轮确认）','CoRL2020/PMLR2021','正文','evidence_a.md','代码完整性未审计','https://proceedings.mlr.press/v155/sharma21b.html')
source('S16','Position: Good Embodied Reward Models Need Bad Behavior Data','2606.01036','2026-05-31','v1','v1','ICML2026 Position Paper','正文','evidence_a.md','世界模型造数据部分是建议，不能转述为均有实测')
source('S17','LfVoid','2307.07837','2023-07-15','v1','v1（本轮确认）','NeurIPS2023','正文+项目','evidence_a.md','初始图→目标图编辑与discriminator RL已有；不代表本项目编辑必可靠','https://lfvoid-rl.github.io/')
source('S18','HiRE','2609.27068','2026-09-22','v1','v1','arXiv预印本','正文+源码','§4/6/附录；evidence_b.md','源码和3项MimicGen BC checkpoint公开；ToolHang BC未发布；支持库配置须区分','https://github.com/HiRE-Project/HiRE')
source('S19','Demo2Reward / From Demonstrations to Rewards','2606.00083','2026-05-22（按arXiv提交历史）','v1','v1','arXiv预印本','正文+源码','§3/4/5、Suppl.A/C；evidence_b.md','prompt与RL代码公开；示范原数据未直接包含','https://github.com/cgumbsch/Demo2Reward')
source('S20','eVTA0 / RLER','2609.33653','2026-09-27','v1','v1','arXiv预印本','正文+源码/资产元数据','§3/Alg.1/App.B–E；evidence_b.md','训练/评价/GRPO overlay、HF模型数据条目公开；软失败标签使用冻结V-JEPA2特征','https://github.com/duowuyms/eVTA0')
source('S21','GCR','2410.19989','2024-10-25','v2','v2/2025-05-14','ICRA2025','正文+项目；外链附录未全读','§V/VI；evidence_b.md','项目可读；官方代码/权重本轮未确认','https://gcr-robot.github.io/')
source('S22','PACT','2606.03949','2026-06-02','v2','v2/2026-07-07','arXiv预印本','正文/附录','§3–6/App.C,E,F；evidence_b.md','作者匿名仓库读取失败，权重/数据未确认；不是空仓证据','https://anonymous.4open.science/r/HILRL-A1X-BC05')
source('S23','SOLE-R1','2603.28730','2026-03-30','v2','v2/2026-05-26','arXiv预印本','正文+源码/资产入口','§3/App.J,K；evidence_b.md','官方model仓库有模型和训练数据链接；未下载；训练脚本完整性未核尽','https://github.com/Philip-MIT/sole-r1-model')
source('S24','RUDDER','1806.07857','2018-06-20','v3','v3/2019-09-10','NeurIPS2019','正文','§3/A2.8；evidence_b.md','论文链接官方代码，本轮仓库抓取失败','https://github.com/ml-jku/rudder')
source('S25','TAMER','','2009 K-CAP','原作者方法说明','本轮未作版本史审计','K-CAP2009','作者方法说明/论文入口','evidence_b.md','反馈延时/信用分配的成熟前例；不是当前VLM方法','https://www.cs.utexas.edu/~bradknox/TAMER.html')
source('S26','PEBBLE','2106.05091','2021-06-09','','ICML2021版本','ICML2021','正文','§4/Alg.2/Fig.5；evidence_b.md','PMLR正文与官方代码入口；未复现','https://proceedings.mlr.press/v139/lee21i.html')
source('S27','Eureka','2310.12931','2023-10-19','v2','v2/2024-04-30','ICLR2024','正文+项目','§3/G.1；evidence_b.md','官方项目/代码；未执行reward搜索','https://eureka-research.github.io/')
source('S28','ProgAgent','2603.07784','2026-03-08','v1','v1','arXiv预印本','正文','§3/4/6；evidence_b.md','未确认官方实现；真实部署证据需进一步核，不作已成熟真实系统结论')
source('S29','Test-Time Training','1909.13231','2019-09-29','','ICML2020版本','ICML2020','正文','§2/3；evidence_b.md','PMLR Software入口；用于术语边界','https://proceedings.mlr.press/v119/sun20b.html')
source('S30','Tent','2006.10726','2020-06-18','','ICLR2021版本','ICLR2021','方法/官方代码','evidence_b.md','通用视觉适应，不等同机器人局部reward监督','https://github.com/DequanWang/tent')
source('S31','CoTTA','2203.13591','2022-03-25','','CVPR2022版本','CVPR2022','正文方法/官方代码','§3；evidence_b.md','长期适应/防遗忘前例；未运行','https://github.com/qinenergy/cotta')
source('S32','ContactGuard','2608.13438','2026-08-13','v1','v1','arXiv预印本','正文/附录','evidence_c.md','未确认官方可下载代码/模型/数据')
source('S33','Foresight','2606.23085','2026-06-22','v1','v1','arXiv预印本','正文','evidence_c.md','项目读取失败，资产未确认；动作predictor及failure Transformer训练')
source('S34','FARM','2609.11445','2026-09-10','v1','v1','arXiv预印本','正文+仓库状态','evidence_c.md','官方repo当前README Coming Soon；0.2256ms为head-only，非端到端','https://github.com/HaoranPei-casia/FARM')
source('S35','FoMo-FD','2607.27511','2026-07-29','v1','v1','arXiv预印本','正文','evidence_c.md','未确认官方完整资产；observed endpoint异常不能称pre-action预警')
source('S36','Foundational World Models for Failure Detection','2603.06987','2026-03-07','v1','v1','arXiv预印本','正文','evidence_c.md','代码/权重/数据未确认；真实7 nominal/9 failure，小样本证据边界')
source('S37','STRIPS-WM','2606.06832','2026-06-05','v1','v1','arXiv预印本','正文/附录','§3/App.RQ4；evidence_c.md；evidence_root.md','未确认官方完整资产；graph/高层action权限不得隐藏')
source('S38','Code as Monitor / CaM','2412.04455','2024-12-05','v1','v3/2025-03-21','预印本；本次未核最终venue','正文+项目','evidence_c.md','本次深读v1，最新v3只查版本；多视角3D权限','https://zhoues.github.io/Code-as-Monitor/')
source('S39','RoVer','2510.10975','2025-10-13','v1','v2/2025-10-14','arXiv预印本','正文','evidence_c.md','本次深读v1，最新v2只查版本；policy候选action输入')
source('S40','World-Gymnast','2602.02454','2026-02-02','v1','v1','arXiv预印本','正文+源码入口','evidence_c.md','公开setup/scripts可读；4GPU示例不等于最低预算','https://github.com/world-gymnast/world-gymnast')
source('S41','GenRL','2406.18043','2024-06-26','v2','v2/2024-10-30','NeurIPS2024','正文+代码/资产元数据','evidence_c.md','官方code/HF模型数据；InternVideo2依赖访问；未下载','https://github.com/mazpie/genrl')
source('S42','Sirius Runtime Monitor','2310.17552','2023-10-26','','本轮未核全部版本史','2023预印本','正文+项目','evidence_c.md','项目链接后续sirius-fleet，不能等同2023完整实现','https://ut-austin-rpl.github.io/sirius-runtime-monitor/')
source('S43','SAFE','2506.09937','2025-06-11','','NeurIPS2025版本','NeurIPS2025','摘要/项目；非全篇深读','evidence_c.md','用于近邻发现；policy内部信息权限，具体实证不作全文核查结论','https://vla-safe.github.io/')
source('S44','FAIL-Detect','2503.08558','2025-03-11','v2','v3/2025-06-20','预印本；本次未核最终venue','正文','evidence_c.md','深读v2；最新v3只查版本；success-only OOD/conformal')
source('S45','Farid et al. Failure Detection','2202.05894','2022-02-11','','RSS2022版本','RSS2022 DOI 10.15607/RSS.2022.XVIII.042','正文','evidence_c.md','历史传感/PAC-Bayes监测前例，非当前RGB语义任务','https://www.roboticsproceedings.org/rss18/p042.html')
source('S46','B2FF','2606.09258','2026-06-08','v1','v1','arXiv预印本','正文','evidence_c.md','恢复性与触发迟延前例；资产未确认')
source('S47','UniGoal','2503.10630','2025-03-13','v1','v3/2025-03-18','预印本；本次未核最终venue','正文','evidence_root.md；evidence_a.md','深读v1；最新版只查版本；posed RGB-D/scene graph权限')
source('S48','ImagineNav++','2512.17435','2025-12-19','v3','v3/2026-04-30','arXiv预印本','正文','evidence_root.md','另读v1；v3视图选择Where2Imagine；novel view synthesis不等同物理动力学')
source('S49','ProgressLM','2601.15224','2026-01-21','v2','v2/2026-05-21','arXiv预印本','正文','evidence_root.md；evidence_a.md','另读v1；mental simulation不等于动作条件WM','https://github.com/ProgressLM/ProgressLM')
source('S50','Vision-Language Models for Robot Success Detection','','2024-03-24','正式出版页面','2024正式版本','AAAI Undergraduate Consortium2024','正式短文/页面','evidence_a.md','小规模VLM成功检测微调的成熟前例；短文证据范围','https://ojs.aaai.org/index.php/AAAI/article/view/30552')
source('S51','SuSIE','','未独立核首次公开日','官方项目','本轮未核全部版本史','支持性工作；不据此判定venue','项目机制；非全篇深读','evidence_a.md','图像编辑/goal相关机制入口；不作详细实证结论','https://rail-berkeley.github.io/susie/')
source('S52','SayCan','','未独立核首次公开日','官方项目','本轮未核全部版本史','支持性工作','项目机制；非全篇深读','evidence_c.md','skill/value选择前例；不将可执行性等同局部事实','https://say-can.github.io/')
source('S53','Criticality World Model','2607.28251','2026-07-30','v1','v2/2026-10-03','预印本；当前v2题名涉及RSI','排除项/风险近邻','evidence_c.md','只核v1风险相关机制；v2 Policy-Level Recursive Self-Improvement，不推荐、不进入候选路线')
source('S54','Robot monitoring survey','2607.21655','2026-07-22','v1','v1（本轮确认）','arXiv综述预印本','综述分类/文献发现','evidence_root.md','只作检索和接口分类，主要实证结论引用原始论文')
source('S55','Qwen3.6-27B official model card','','本轮未核首次发布时间','2026-10-12模型卡/API快照','在线状态2026-10-12','官方模型资源','模型卡/资产元数据','evidence_root.md','确认模型名称和视觉支持；未下载权重/实测，强底座效果仍待试验','https://huggingface.co/Qwen/Qwen3.6-27B')
source('S56','DoReMi','2307.00329','2023-07-01','v4','v4/2024-09-14','IROS2024','摘要/正式arXiv页面；非全篇深读','REPORT_zh.md§4；sources/DoReMi_abs.txt','LLM产生约束、VLM持续检测违反并恢复的早期接口前例；不作细节/定量机制结论','https://sites.google.com/view/doremi-paper')

# Attach exact titles where a checked abs-page manifest supplies them, without inventing others.
manifest=json.loads((ROOT/'a_materials/sources_a_manifest.json').read_text(encoding='utf-8'))
titles={x['arxiv_id']:x['title'].removeprefix('Title: ').strip() for x in manifest}
for x in sources:
    x['title_from_checked_manifest']=titles.get(x['arxiv_id'])
payload=dict(checked_date='2026-10-12',scope='深读核心机制+支持性资料；非穷尽系统综述；阅读不等于复现',sources=sources,semantic_discovery=dict(workspace_url='https://app.undermind.ai/projects/7e38292f-2b5e-4e86-95bc-9afc5fca5ba5',queries=3,results_per_query=20,raw_files=['sources/undermind_monitor.txt','sources/undermind_adapt.txt','sources/undermind_predict.txt'],metadata_only_examples=['MURAL','GIFT','SpaTiaL','To Err Is Robotic'],warning='语义命中60项不是60篇全文深读；仅元数据不得承载方法/效果结论'),snapshot_manifest='SOURCE_MANIFEST_root.json')
(ROOT/'literature_sources.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# 文献、版本与公开来源清单','', '核查日：2026-10-12（北京时间）。首次公开日期主要指最早核到的arXiv提交，ConditionNET另核正式出版更早日期；不保证它是全网所有渠道最早公开。编号月份不能代替提交日。“当前版本”是当日查得状态，**本次读版本**才对应具体方法结论。预印本不代表同行评审已接受；公开链接、仓库、模型条目不代表资产完整或结果已复现。', '', '本清单包含56项论文、方法或官方资源，并非56篇均全文深读。每行标明阅读层级；SAFE/SuSIE/SayCan/DoReMi及综述等只承担发现或支持性用途。未确认发布、读取失败、已发布三者分开记录。', '', '| ID / 名称及主来源 | 最早核查公开；本次读版；当日最新查得 | 状态 / 阅读层级 | 正文定位及开放边界 |', '|---|---|---|---|']
for x in sources:
    asset=f" [官方入口]({x['official_asset_url']})" if x['official_asset_url'] and x['official_asset_url']!=x['url'] else ''
    md.append(f"| {x['id']} / [{x['alias']}]({x['url']}) | {x['first_public_date']}；{x['read_version'] or '正式/指定正文'}；{x['current_checked_version']} | {x['publication_status']} / {x['evidence_level']} | {x['locator']}；{x['availability_note']}{asset} |")
md += ['', '## 固定源码与可追溯文件', '', '- ARS：`0b61a5de0c39af1788d960ea8dd996aa76b27f7f`；本轮38个代码/文本文件只读审查。10月10日早先空仓快照仍是历史记录。', '- HiRE：`bea7dfb15d1d279bc8f76ff0e8e44b838f696acc`；eVTA0：`8017928d59bc1d3d9051eba43011bd140bf76f54`；Demo2Reward：`2b5082465a4ce7151f479e715df7ab7881807f27`；SOLE-R1：`1c4f3f8340b45fbee5bd5c303fc41ed53072fbbf`。这些是读取快照，不是运行验证。', '- [根来源快照manifest](SOURCE_MANIFEST_root.json)保存URL、读取UTC、HTTP状态、SHA256和大小；[A版本记录](a_materials/sources_a_manifest.json)、[C版本核查](c_sources/version_check.json)、B证据笔记§10保存分支版本和仓库状态。', '- [机器可读清单](literature_sources.json)保存本表元数据；[A](evidence_a.md)、[B](evidence_b.md)、[C](evidence_c.md)、[跨主线](evidence_root.md)保留机制、局限和全文定位。', '', '## 检索方式与遗漏边界', '', '使用机制关键词的公开网页搜索、arXiv正文/附录、官方项目/源码/模型元数据，并以Undermind分别检索可撤销任务条件、执行反馈适应、动作条件预测与恢复，各返回20项。原始语义结果在sources/undermind_*.txt；[语义检索工作区](https://app.undermind.ai/projects/7e38292f-2b5e-4e86-95bc-9afc5fca5ba5)可追查。仅元数据发现的MURAL/GIFT/SpaTiaL等未被当作完整方法证据。', '', '没有注册系统综述协议或覆盖所有数据库，也不以“未检到”证明不存在。该清单支持当前选题比较，不能保证新颖性。对未读的新版本、匿名仓库失败及不可访问附录已保留不确定性。没有下载权重、租算力、训练或执行机器人。']
(ROOT/'LITERATURE_SOURCES_zh.md').write_text('\n'.join(md)+'\n',encoding='utf-8')

discussion='''# 给师姐的讨论稿：先验证监督义务，再决定Monitor形态

我重新查了少数据训练、执行反馈适应和预测Monitor三条路线。现在的判断是：方向本身合理，但泛泛的“小数据训练reward”“执行结果让监督者成长”“world model预测失败”都已有很近的工作，不能再靠换底座、换模块名称或允许训练来形成区别。

原来8B免训练的开发结果只说明格式改善、语义仍有错误。局部核验的8个终判槽没有有效输出，因而还不能说核验有净收益，也不能说原问题一定失败。ARS已覆盖事件、重新视觉取证、独立核验、准备/撤销和筛选后BC；本轮代码也已公开。我们需要重新定义真正希望学习的量：某对象关系在何时建立或失效，和“之后能否成功”并不是同一件事。

**我想优先做A，但把它缩成一个可推翻的问题：同样标注时间下，对象—关系—有效时段监督，能否比终局、阶段、retry或时间warp监督更好地识别跨目标的条件撤销，并改善混合轨迹筛选？** RoboMonitor已经做少标注预测表征+runtime头，ConditionNET已经做技能前提/效果，ReTVL/WARP已经处理非单调进度，所以新意不能是这些关键词。可争取的区别是监督义务、标注效率、关系与时间迁移，以及保留有效准备/恢复的下游价值，目前尚未确认。

先用独立新序列检验强底座、公开reward模型、ARS前缀适配和直接小头有没有可重复的关系错误；再用小批双标确认RGB证据能否支持真值。进入训练前还要做oracle筛选诊断：如果独立人工标签筛选的固定混合池也不改善同保留量BC，就先改接口或数据，避免只提高分类分数。若强模型已经解决，A降为基线工程；若只有旧受控例有效，则不能扩展成通用Monitor论文。

**B保留为第二候选：有限可信局部反馈怎样改善下一条执行的判断。** HiRE是support库更新，Demo2Reward是prompt优化，eVTA0已经是终局TD+LoRA+策略交替学习，并含表征软失败标签。我们若只做终局反馈继续训练，撞题很高。可以比较终局、后续可见事实、少量人工局部复核；但后来看清只能默认标后来的时刻，回填过去必须证明身份连续且状态没变。先固定policy，按“预测→揭示结果→更新→下一条”比较静态、buffer、prompt、TD小头和局部复核，匹配反馈分钟及优化步数，测跨任务和遗忘。若收益只是多给标签，贡献是监督价值；若buffer同样好，不坚持参数适应。

**C先做预测必要性诊断，暂缓完整视频世界模型。** ContactGuard/FARM/Foresight已有动作条件未来表征和失败读出；“冻结预测器+小头+执行前预警”很接近。若有稳定技能和兼容动作空间的预测器，可以在精确复位初态执行不同技能，只在评价侧看真实后果，比较当前特征+同样action与未来特征。若action打乱不掉、当前头同样好、或只有真实未来oracle有用，就不保留WM路线。跨技能关系失效和恢复可能是额外义务，但还不是已证明的方法空白。

更强底座、图像编辑、WM负例和导航中的身份核验/记忆都可以作为配套：编辑标签仍由目标决定，生成后果需要独立核实，动态操作中的黑名单要能撤销。最终用途优先在“固定技能恢复”或“固定混合池筛选→BC”选一个；RL等接口价值成立后再上。已有成熟rollout和可信局部反馈时B可以提前；有兼容WM和技能库时C成本会下降，但资源增加不会消除近同覆盖。

这次没有跑实验。我想先讨论并确定三件事：我们最需要改善的是局部可见关系还是成功概率；主要接口选恢复还是筛选；能否获得独立局部真值和稳定技能。确认后再执行一个能让路线升级或降级的最小诊断，而不是先承诺一套完整架构。

对应证据见[详细报告](REPORT_zh.md)、[重合矩阵](OVERLAP_MATRIX_zh.md)和[版本/来源清单](LITERATURE_SOURCES_zh.md)。
'''
if not (ROOT/'FOR_SENIOR_REPORT_zh.md').exists():
    (ROOT/'DISCUSSION_WITH_SENIOR_zh.md').write_text(discussion,encoding='utf-8')
legacy_readme='''# Robot Monitor A/B/C深入调研交付

日期：2026-10-12。范围是文献核查、选题重合审计和后续诊断设计；没有实验结果或已确认新颖性。原有研究文件保留。

- [详细研究报告](REPORT_zh.md)：条件推荐、问题重定义、机器人接口、A/B/C设计、成本与降级条件。
- [逐项重合矩阵](OVERLAP_MATRIX_zh.md) / [CSV](overlap_matrix.csv)：27组七维机制对比及决定性对照。
- [可核验文献与版本](LITERATURE_SOURCES_zh.md) / [JSON](literature_sources.json)：56项资源，明确正文/项目/元数据层级。
- [给师姐的讨论稿](DISCUSSION_WITH_SENIOR_zh.md)：可直接据此讨论的短稿。
- 阅读笔记：[A](evidence_a.md)、[B](evidence_b.md)、[C](evidence_c.md)、[根任务交叉核查](evidence_root.md)。
- 来源快照：[manifest](SOURCE_MANIFEST_root.json)，公开正文、代码和元数据在sources/a_materials/b_sources/c_sources中；没有模型权重。

build_delivery.py只组装文档和结构化文件；snapshot_sources.py只抓取公开文献/源码。所有实验规模、成本和停止条件都是未来建议，不能引用为已测结果。RSI排除。
'''
if not (ROOT/'FOR_SENIOR_REPORT_zh.md').exists():
    (ROOT/'README.md').write_text(legacy_readme,encoding='utf-8')
print(json.dumps({'matrix_rows':len(rows),'source_entries':len(sources),'output_dir':str(ROOT)},ensure_ascii=False))
