"""Extract published tables and recompute descriptive statistics; no model inference."""
from pathlib import Path
from bs4 import BeautifulSoup
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'research/sources/native_gap_audit_20261003/robometer_v2.html'
soup = BeautifulSoup(SOURCE.read_text(encoding='utf-8'), 'html.parser')
tables = {}
for key in ['A3.T14', 'A3.T15', 'A5.T26', 'A5.T27']:
    element = soup.find(id=key)
    tables[key] = [[c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'])]
                   for tr in element.select('tr')]
rows = []
for quality, task in zip(tables['A3.T14'][1:-1], tables['A3.T15'][1:-1]):
    assert quality[0] == task[0]
    q, t = float(quality[2]), float(task[2])
    rows.append({'dataset': quality[0], 'quality_accuracy_pct': q,
                 'task_accuracy_pct': t, 'gap_percentage_points': round(t-q, 1)})
with (OUT / 'preference_comparison.csv').open('w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader(); writer.writerows(rows)

# Manual transcription from visually inspected official Figure 14(c).
# Rows: failure, suboptimal, success. Columns: predicted failure, predicted success.
matrix = [[31, 4], [23, 12], [9, 21]]
stats = {
    'figure': 'https://arxiv.org/html/2603.02115v2#A5.F14',
    'image_sha256': hashlib.sha256((OUT/'robometer_fig14c.png').read_bytes()).hexdigest(),
    'transcription_method': 'manual visual inspection of original 469x349 PNG',
    'matrix': matrix,
    'row_labels': ['failure', 'suboptimal', 'success'],
    'column_labels': ['predicted_failure', 'predicted_success'],
    'suboptimal_false_success_rate': 12/35,
    'failure_false_success_rate': 4/35,
    'false_success_rate_ratio_descriptive': (12/35)/(4/35),
    'false_success_rate_gap_pp': (12/35-4/35)*100,
    'suboptimal_share_of_missed_non_success': 12/16,
    'success_false_alarm_rate': 9/30,
    'pooled_failure_detection_tpr': 54/70,
    'pooled_success_identification_tnr': 21/30,
    'total_episodes_in_figure': sum(map(sum, matrix)),
    'limits': ['Pooled over tasks; no per-task quality cross-tab or episode IDs.',
               'Descriptive sample comparison, not a controlled causal effect or universal 3x law.',
               'Suboptimal means partial progress without completion, not necessarily near-complete.',
               'No model calls; counts are author results, not our reproduction.']
}
assert stats['total_episodes_in_figure'] == 100
assert all(r['gap_percentage_points'] > 0 for r in rows)
result = {'paper_url': 'https://arxiv.org/html/2603.02115v2',
          'cached_paper_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'tables': tables, 'preference_comparison': rows, 'figure14c': stats,
          'model_runs_this_followup': 0}
(OUT/'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'datasets': len(rows), 'quality_gap_all_six': True, 'figure14c': stats}, ensure_ascii=False, indent=2))
