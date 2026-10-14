from pathlib import Path
import json, re, hashlib

B=Path(__file__).resolve().parent
R=B.parent.parent
queries=[
 'robot robot manipulation progress monitoring reward model September 2026 August 2026',
 'robot execution monitoring progress estimation foundation model 2026 benchmark',
 'site:arxiv.org "robot" "reward" "2026" "Sep" "progress"',
 '"Dream2Reward" github', '"SARM2" github',
 '"SARM2" "training-free" OR "inference" improvement',
 'robot "stage estimation" "training-free" temporal consistency',
 'robot failure detection "training-free" "2026" transfer',
 '"ProTracer" robot failure code github',
 'robot "failure onset" "training-free" -ProTracer',
 'robot "failure localization" "hierarchical" "2026"',
 'robot action segmentation "training-free" "temporal" decoding',
 '"Your VLM Already Knows When" arxiv', '"ViFailback" arxiv',
 '"ProTracer" "improvement" robot failure'
]
(B/'search_log.json').write_text(json.dumps({'search_date':'2026-10-03','timezone':'Asia/Shanghai','tool':'web.run','representative_actual_queries':queries,'scope':'30/90 days, expanded to 180; older mechanism comparators','limitation':'Representative query log; not exhaustive proof of absence. Aggregator and machine-review pages used only for discovery.'},ensure_ascii=False,indent=2),encoding='utf-8')
papers=[
 ('protracer','2609.21369','ProTracer: Proprioception-Guided Failure Diagnosis in Robot Manipulation'),
 ('sarm2','2606.10305','SARM2: Multi-Task Stage Aware Reward Modeling for Self Improving Robotic Manipulation'),
 ('farm','2609.11445','FARM: Reading Failure Signals from the Internal Predictive States of a Frozen Robotic World Model'),
 ('evta','2609.33653','Demonstration-Free Success-Probability Reward Learning for Generalist Robot Policies'),
 ('dream','2608.18787','Dream2Reward: Transition-Alignment Reward Models from Positive Demonstrations for Robotic Manipulation')
]
bib=[]
for key,aid,title in papers:
    # Metadata source preserves full authors; this index intentionally omits rather than guesses them.
    bib.append('@misc{'+key+'2026,\n  title = {'+title+'},\n  year = {2026},\n  eprint = {'+aid+'},\n  archivePrefix = {arXiv},\n  url = {https://arxiv.org/abs/'+aid+'}\n}')
(B/'candidates.bib').write_text('\n\n'.join(bib)+'\n',encoding='utf-8')
status=R/'status.md'
old=status.read_bytes()
backup=B/'status.before.md'
if not backup.exists(): backup.write_bytes(old)
prefix='''# 研究状态

## 当前入口：第三轮新基底筛选完成，ProTracer优先诊断，SARM2条件备选

更新日期：2026-10-03。按最新请求扩展检索并执行流程第一至第四步，见[new_baseline_search_20261003_round3.md](new_baseline_search_20261003_round3.md)。ProTracer官方代码、长轨迹标签与数据入口已核；作者Long起点MAE4.06秒、acc@1s49.12%，属于离线执行诊断，不冒称在线连续进度。源码核实容差分母为全部失败，MAE只统计检测到且有数值起点的失败；100条Long标签为57失败/43成功。尚无原生逐例预测，未定错因。候选边界、后续归因及平台差异需区分。

SARM2收伞原语识别57.74%提供另一原生线索，但阶段错误不等于价值错误，配套已发布权重未确认。FARM、eVTA₀、Dream2Reward因发布或具体错误材料不足暂缓。KITE、FV-Action、OVTAS及ProTracer自身已覆盖结构化证据、反思、扫描定位和时序一致性，不能重新包装为贡献。

下一件低成本动作：固定版本后对少量ProTracer Long开发轨迹检查原生确定性选帧/叙述与GT起点的覆盖关系，再决定是否需要VLM调用。严格连续progress估计则SARM2更贴题，但本轮未得到材料齐备的新替代。没有实现架构、运行模型或付费任务，尚未确认方法新颖性。旧RoboMeter—ProgressCompass及VLAC-Cut—ARS重合切口保持停止。以下历史原文完整保留，不自动恢复其下一动作。

---

'''
if not old.startswith(prefix.encode('utf-8')):
    status.write_bytes(prefix.encode('utf-8')+old)
assert status.read_bytes().endswith(backup.read_bytes())
report=R/'new_baseline_search_20261003_round3.md'
links=re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8'))
missing=[x for x in links if not x.startswith(('https://','http://','#')) and not (report.parent/x.split('#')[0]).exists()]
assert not missing,missing
validation={'report_exists':True,'local_report_links_checked':len([x for x in links if not x.startswith('http')]),'missing_local_links':missing,'status_history_preserved':True,'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),'model_runs':0,'source_audit':'python research/sources/new_baseline_search_20261003_round3/audit_sources.py'}
(B/'validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
print(json.dumps(validation,ensure_ascii=False))
