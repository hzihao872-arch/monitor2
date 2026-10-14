from pathlib import Path
import hashlib
import json
import re

B = Path(__file__).resolve().parent
root = B.parents[2]
research = root / 'research'
report = research / 'baseline_gap_rescreen_20261003.md'
status = research / 'status.md'
backup = B / 'status_before_rescreen.md'
sha = lambda data: hashlib.sha256(data).hexdigest()

if not backup.exists():
    backup.write_bytes(status.read_bytes())
prior = backup.read_bytes()
prefix = '''# 研究状态

## 当前入口：VLAC-Cut 降级；RynnValue 条件优先，DenseReward 备选

更新日期：2026-10-03。按用户最新决定，停止继续投入“错误物体＋补看验证”高重合方向，不再把 ARS 三段同例实验作为下一动作。已完成 [基底缺口复筛](baseline_gap_rescreen_20261003.md)。VLAC-Cut 其他入口未出现足够划算的独立具体错误，保留比较角色。

RynnValue 最新官方 Filter-BC 表中，抽屉任务策略成功率从 40% 降到 0%，但四任务平均从 35% 升到 42.5%。已核筛选代码及竞争解释；这是策略层负收益，不是评价器准确率，也未证明错因。ARS/WARP-RM 已覆盖进展筛选，HiRE 已覆盖依赖结果历史的免训练校准；不能直接以此宣布新方法。

下一步只做有界小诊断：绑定版本及原生分数/筛选白名单，区分评分错、片段用途与窗口不匹配、任务配比改变。当前公开 HF 4B/8B config 仍为 symlog，与最新仓库 quantile 描述不一致，Filter-BC checkpoint/数据输出未绑定；不启动完整策略训练。若材料追不到或又回到完成确认＋补看，则降低该切口优先级。DenseReward 的 DROID MAE 0.259 是第二入口，已核公开测试行数及材料限制。所有模型仍未运行，未确立新颖架构。

旧 RoboMeter—ProgressCompass 路线保持停止。以下原文逐字节保留为历史，不能覆盖本次用户取舍。

---

'''.encode('utf-8')
status.write_bytes(prefix + prior)
assert status.read_bytes().endswith(prior)

manifest = json.loads((B / 'fetch_manifest.json').read_text(encoding='utf-8'))
verified = []
failed = []
for row in manifest:
    if 'sha256' not in row:
        failed.append({'file': row['file'], 'error': row.get('error')})
        continue
    p = B / row['file']
    assert p.stat().st_size == row['bytes'], row['file']
    assert sha(p.read_bytes()) == row['sha256'], row['file']
    verified.append(row['file'])

links = re.findall(r'\]\(([^)]+)\)', report.read_text(encoding='utf-8'))
local_links = [u for u in links if not u.startswith(('http:', 'https:'))]
for u in local_links:
    assert (report.parent / u.split('#')[0]).exists(), u

cfgs = [json.loads((B / f'rynn_{size}_config.json').read_text(encoding='utf-8')) for size in ['4b','8b']]
assert all(c['value_tokenizer_config']['support_transform'] == 'symlog' for c in cfgs)
tree = json.loads((B / 'rynnvalue_tree.json').read_text(encoding='utf-8-sig'))
assert not tree['truncated']
assert sum([30,70,0,40])/4 == 35
assert sum([70,75,25,0])/4 == 42.5
data = json.loads((B / 'dense_metadata_audit.json').read_text(encoding='utf-8'))
assert sum(v['frame_samples'] for v in data['sources'].values()) == 28032
assert sum(v['filename_episode_groups'] for v in data['sources'].values()) == 958

result = {
    'model_inference_run': False,
    'verified_source_count': len(verified),
    'source_bytes': sum(r.get('bytes',0) for r in manifest),
    'failed_source_requests': failed,
    'report_sha256': sha(report.read_bytes()),
    'report_local_links_checked': len(local_links),
    'status_prior_sha256': sha(prior),
    'status_historical_suffix_preserved': True,
    'rynn_tree_entries': len(tree['tree']),
    'rynn_hf_config_support_transforms': [c['value_tokenizer_config']['support_transform'] for c in cfgs],
    'rynn_filter_bc_native_table': {'control':[30,70,0,40], 'filtered':[70,75,25,0], 'mean_control':35, 'mean_filtered':42.5},
    'rynn_native_filter_prediction_dump_obtained': False,
    'rynn_latest_readme_checkpoint_bound': False,
    'dense_test_rows': 28032,
    'checks_passed': True,
}
(B / 'final_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
