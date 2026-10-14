"""Render author-released values for a research briefing; no model inference."""
from pathlib import Path
import hashlib
import json
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

B = Path(__file__).resolve().parent
research = B.parent
source = research / 'sources' / 'vlac_ars_coverage_20261003'
prediction_path = source / 'early_example02_prediction.jsonl'
p = json.loads(prediction_path.read_text(encoding='utf-8'))
meta = json.loads((source / 'early_example02_metadata.json').read_text(encoding='utf-8'))
times = p['pred_curve_point_times_sec']
values = p['pred_curve_point_progress']
gt_t = p['gt_dense_timestamps_sec']
gt_p = p['gt_dense_progress']
assert values[times.index(6.1)] == -8
assert values[times.index(8.3)] == 2
assert abs(gt_p[183] - 2.3) < 1e-6
assert abs(gt_p[249] + 6.4) < 1e-6
assert len(gt_p) == meta['num_frames'] == 289

font = FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.size':11, 'axes.unicode_minus':False, 'pdf.fonttype':42})
fig, ax = plt.subplots(figsize=(9.8,4.9), layout='constrained')
ax.axvspan(6.1,8.3,color='#fff0d7',zorder=0)
ax.axhline(0,color='#bdc3c7',lw=.8,zorder=0)
ax.plot(gt_t,gt_p,color='#276b65',lw=2.2,label='作者逐帧标签')
ax.plot(times,values,color='#b94b47',lw=2,marker='o',ms=4.5,label='VLAC-Cut 原始预测点及连线')
for t,y,s,offset in [(6.1,-8,'−8.0',(-17,-20)),(8.3,2,'2.0',(7,6)),(6.1,2.3,'2.3',(-8,10)),(8.3,-6.4,'−6.4',(7,-14))]:
    ax.annotate(s,(t,y),xytext=offset,textcoords='offset points',fontsize=11,fontproperties=font)
ax.text(7.2,16.5,'标签继续下降，预测出现回升',ha='center',fontproperties=font,fontsize=11)
ax.set_title('官方示例：把洋葱放入快递箱',fontproperties=font,fontsize=15,pad=14)
ax.set_xlabel('视频时间（秒）',fontproperties=font)
ax.set_ylabel('有符号任务进展（作者尺度）',fontproperties=font)
ax.set_xlim(0,9.6)
ax.set_ylim(-13,22)
ax.set_xticks(range(10))
ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y',alpha=.18)
ax.legend(loc='upper left',prop=font,frameon=False)
fig.savefig(B/'onion_progress.png',dpi=180,facecolor='white')
fig.savefig(B/'onion_progress.pdf',facecolor='white')
plt.close(fig)

report = research / 'vlac_cut_teacher_report_20261003.md'
text = report.read_text(encoding='utf-8')
assert not re.search(r'\bars\b|rynn|densereward',text,re.I)
assert '尚未验证改进效果' in text
for path in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text):
    assert Path(path).exists(),path
check = {
    'model_inference_run':False,
    'source_prediction_sha256':hashlib.sha256(prediction_path.read_bytes()).hexdigest(),
    'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),
    'plot_uses_author_values_only':True,
    'raw_points':{'6.1':-8,'8.3':2},
    'author_labels_at_same_frames':{'183':gt_p[183],'249':gt_p[249]},
    'excluded_method_names_absent':True,
    'image_links_exist':True,
}
(B/'validation.json').write_text(json.dumps(check,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(check,ensure_ascii=False))
