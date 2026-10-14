"""Recheck released example data and prepare reproducible report assets. No inference."""
from pathlib import Path
import json, csv, hashlib, shutil, subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parents[1] / 'research' / 'sources' / 'vlac_ars_coverage_20261003'
PAPER = ROOT.parents[1] / 'research' / 'sources' / 'new_baseline_search_20261003'
E = ROOT/'evidence'; A=ROOT/'assets'
E.mkdir(exist_ok=True); A.mkdir(exist_ok=True)
SHA='354df56ff177018f4ed3849996b3b1fc9cadedc8'
HF='93dc313de32258c0c81d5f50eabfe570a40d6dd6'
manifest=[]
def cp(src, dst, url):
    shutil.copyfile(src,E/dst)
    manifest.append(dict(file=dst,sha256=hashlib.sha256((E/dst).read_bytes()).hexdigest(),url=url))
for i in range(1,4):
    cp(SRC/f'early_example{i:02}_metadata.json',f'example_{i:02}_metadata.json',f'https://huggingface.co/InternRobotics/VLAC-Cut/blob/{HF}/examples/example_{i:02}/metadata.json')
    cp(SRC/f'current_example{i:02}_prediction.jsonl',f'example_{i:02}_prediction.jsonl',f'https://github.com/InternRobotics/VLAC-cut/blob/{SHA}/examples/reference_outputs/example_{i:02}.jsonl')
    video=SRC/f'early_example{i:02}_video.mp4'
    manifest.append(dict(file=str(video.relative_to(ROOT.parents[1])),sha256=hashlib.sha256(video.read_bytes()).hexdigest(),url=f'https://huggingface.co/InternRobotics/VLAC-Cut/blob/{HF}/examples/example_{i:02}/episode.mp4',copied=False))
cp(PAPER/'vlaccut.html','paper_v2.html','https://arxiv.org/html/2607.09776v2')
cp(PAPER/'vlac_scripts_evaluate_vpb_predictions.py','official_evaluate_vpb_predictions.py',f'https://github.com/InternRobotics/VLAC-cut/blob/{SHA}/scripts/evaluate_vpb_predictions.py')
cp(SRC/'early_reference_README.md','official_reference_outputs_README.md',f'https://huggingface.co/InternRobotics/VLAC-Cut/blob/{HF}/examples/reference_outputs/README.md')
cp(SRC/'pairing_validation.json','previous_pairing_validation.json','Local prior verification; see URLs above')
(E/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
cases=[]; raw_rows=[]; anchor_rows=[]
for i in range(1,4):
    m=json.loads((E/f'example_{i:02}_metadata.json').read_text(encoding='utf-8'))
    p=json.loads((E/f'example_{i:02}_prediction.jsonl').read_text(encoding='utf-8'))
    t=np.array(p['pred_curve_point_times_sec']); v=np.array(p['pred_curve_point_progress'])
    g=np.array(m['benchmark_dense_progress']); anchors=m['benchmark_semantic_anchors']
    for j,(ta,va) in enumerate(zip(t,v)):
        fr=round(ta*m['fps']); raw_rows.append(dict(example=i,time_sec=ta,frame=fr,author_label=float(g[fr]),author_prediction=va))
    for l,r in zip(anchors,anchors[1:]):
        lpr,rpr=np.interp(np.array([l['frame'],r['frame']])/m['fps'],t,v)
        gd=r['progress']-l['progress']; pd=rpr-lpr
        anchor_rows.append(dict(example=i,start_frame=l['frame'],end_frame=r['frame'],label_delta=gd,prediction_delta=float(pd),direction_agrees=bool(np.sign(gd)==np.sign(pd)),endpoint_hold=bool(r['frame']/m['fps']>t[-1])))
    lin=np.interp(np.arange(len(g)),[x['frame'] for x in anchors],[x['progress'] for x in anchors])
    cases.append(dict(example=i,frames=len(g),fps=m['fps'],raw_prediction_count=len(t),input_frames=p['input_frame_count'],dense_label_max_difference_from_linear_anchor_curve=float(np.max(np.abs(g-lin))),anchor_directions_correct=sum(x['direction_agrees'] for x in anchor_rows if x['example']==i),anchor_intervals=len(anchors)-1))
for name,rows in [('raw_points',raw_rows),('anchor_transitions',anchor_rows)]:
    with (E/f'{name}.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
m=json.loads((E/'example_02_metadata.json').read_text(encoding='utf-8'))
p=json.loads((E/'example_02_prediction.jsonl').read_text(encoding='utf-8'))
g=np.array(m['benchmark_dense_progress']); t=np.array(p['pred_curve_point_times_sec']); v=np.array(p['pred_curve_point_progress'])
assert g[183]==2.3 and g[249]==-6.4 and v[list(t).index(6.1)]==-8 and v[list(t).index(8.3)]==2
shift_rows=[]
for a in range(-15,16):
    for b in range(-15,16):
        shift_rows.append(dict(start_offset_frames=a,end_offset_frames=b,start_frame=183+a,end_frame=249+b,label_delta=float(g[249+b]-g[183+a])))
with (E/'alignment_sensitivity.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(shift_rows[0]));w.writeheader();w.writerows(shift_rows)
native=[]
for a,b in zip(raw_rows,raw_rows[1:]):
    if a['example']==b['example']==2:
        native.append(dict(start_sec=a['time_sec'],end_sec=b['time_sec'],label_delta=b['author_label']-a['author_label'],prediction_delta=b['author_prediction']-a['author_prediction']))
checks=dict(date='2026-10-03',model_inference_run=False,cases=cases,onion_native_transitions=native,
    alignment_sensitivity=dict(type='label endpoint lookup sensitivity; fixed released predictions, not resampled inference',max_endpoint_offset_seconds=.5,endpoint_pairs=len(shift_rows),min_label_delta=min(x['label_delta'] for x in shift_rows),max_label_delta=max(x['label_delta'] for x in shift_rows),all_label_deltas_negative=all(x['label_delta']<0 for x in shift_rows)),
    nearest_input_frames={str(tt):sorted(p['input_frame_indices'],key=lambda f:abs(f/30-tt))[:2] for tt in [6.1,8.3]},
    precision_weight_revision_bound=False,independent_test_videos=0)
(E/'supplemental_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')

font_manager.fontManager.addfont('C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':'Microsoft YaHei','font.size':9,'axes.unicode_minus':False,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
blue='#276b85'; orange='#bb6738'
def save(fig,name):
    for ext in ['png','pdf','svg']: fig.savefig(A/f'{name}.{ext}',dpi=300,facecolor='white',bbox_inches='tight')
    plt.close(fig)
fig,ax=plt.subplots(figsize=(6.55,2.9),layout='constrained')
ax.axvspan(4.3,5.1,color='#e9eef0');ax.axvspan(6.1,8.3,color='#f7ede6')
ax.plot(np.arange(len(g))/30,g,color=blue,lw=1.7,label='作者稠密标签')
ax.plot(t,v,color=orange,lw=1.5,marker='o',ms=3.5,label='作者原始预测点及连线')
ax.scatter([6.1,8.3],[2.3,-6.4],color=blue,s=24,zorder=5)
for x,y,s,dx,dy in [(6.1,2.3,'2.3',-12,9),(6.1,-8,'−8',-9,-19),(8.3,-6.4,'−6.4',6,-18),(8.3,2,'2',5,7)]:
    ax.annotate(s,(x,y),xytext=(dx,dy),textcoords='offset points',fontsize=9,color=blue if y in [2.3,-6.4] else orange)
ax.text(4.7,21,'正确退步',ha='center',fontsize=8);ax.text(7.2,21,'待解释的回升',ha='center',fontsize=8)
ax.axhline(0,color='#aaa',lw=.5);ax.set(xlim=(0,9.6),ylim=(-13,25),xlabel='视频时间（秒）',ylabel='有符号进展（作者尺度）',xticks=np.arange(10))
ax.grid(axis='y',lw=.5,alpha=.2);ax.legend(loc='upper left',frameon=False,fontsize=8)
save(fig,'onion_curve')

ids=[0,129,150,183,213,249,285]
for fr in ids:
    out=A/f'onion_frame_{fr:03}.png'
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(SRC/'early_example02_video.mp4'),'-vf',f'select=eq(n\\,{fr})','-vsync','0','-frames:v','1',str(out)],check=True)
fig,axs=plt.subplots(2,3,figsize=(6.55,3.75),layout='constrained')
for ax,fr,label in zip(axs.flat,ids[:6],['初始目标与容器','接近目标区域','箱体明显倾动','后续操作开始','接触其他物体区域','夹爪邻近黄色物体']):
    ax.imshow(Image.open(A/f'onion_frame_{fr:03}.png'));ax.set_axis_off()
    ax.set_title(f'{fr/30:.2f} 秒 · 第 {fr} 帧\n{label}',fontsize=8,loc='left',pad=4)
save(fig,'onion_frames')

fig,axs=plt.subplots(1,2,figsize=(6.55,2.1),layout='constrained')
for ax,i,title in zip(axs,[1,3],['方块例：退步后回升的方向对照','烧杯例：普通推进的方向对照']):
    mm=json.loads((E/f'example_{i:02}_metadata.json').read_text(encoding='utf-8'));pp=json.loads((E/f'example_{i:02}_prediction.jsonl').read_text(encoding='utf-8'))
    ax.plot(np.arange(mm['num_frames'])/30,mm['benchmark_dense_progress'],color=blue,lw=1.5)
    ax.plot(pp['pred_curve_point_times_sec'],pp['pred_curve_point_progress'],color=orange,marker='o',ms=2.6,lw=1.2)
    if i==1: ax.axvspan(220/30,239/30,color='#e9eef0')
    ax.set_title(title,fontsize=8.5);ax.set_xlabel('视频时间（秒）',fontsize=8);ax.tick_params(labelsize=8);ax.grid(axis='y',alpha=.2,lw=.5)
axs[0].set_ylabel('有符号进展',fontsize=8)
save(fig,'correct_controls')
print(json.dumps(checks,ensure_ascii=False,indent=2))
