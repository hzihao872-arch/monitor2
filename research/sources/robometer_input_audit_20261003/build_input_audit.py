"""Reconstruct fixed-code frame selection only. Never imports a model/HTTP adapter."""
from pathlib import Path
import ast,json,hashlib,subprocess,csv
import numpy as np
from PIL import Image,ImageDraw

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
UP=ROOT/'research/sources/recovery_search_20261003/upstream_trace'
CLIENT=ROOT/'research/sources/prm_scope_review_20261003/official/eval/prm_judge/prm/robometer.py'
SERVER=ROOT/'research/sources/direction_selection_20261003/eval_server.py'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf-8')

if not (OUT/'before_edit.json').exists():
 entries=[]
 for rel in ['research/status.md','research/decision_log.md','experiments/data_manifest.json','experiments/run_ledger.csv','research/08_pilot_report.md','research/07_evaluation_protocol.md','experiments/config_stage7.json']:
  p=ROOT/rel;b=OUT/'before'/rel;b.parent.mkdir(parents=True,exist_ok=True);b.write_bytes(p.read_bytes());entries.append(dict(path=rel,sha256=digest(p)))
 save('before_edit.json',entries)
save('scope.json',dict(models_run=0,network_downloads=0,scope='Fixed-source arithmetic and visual inspection on ep621/618, all reconstruction cases retained. Not paper prediction replay, not independent annotation.',branches=['published PNG sequence supplied as array, no client resampling','original high-camera MP4 at default nominal fps=1'],paper_actual_branch_unknown=True,holdout_eligible=False,reviewer='same single reviewer, has seen full-reference labels; not prefix blinded',stopping_rule='If historical and current visible evidence is absent, do not infer memory/reasoning defect. If present, record input feasibility only, never infer model error.'))

# Compile only the standalone pure sampling function from fixed official source.
tree=ast.parse(CLIENT.read_text('utf-8'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='sample_frame_indices')
env={'np':np};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(CLIENT),'exec'),env)
sample=env['sample_frame_indices']
st=ast.parse(SERVER.read_text('utf-8'))
func=next(n for n in st.body if isinstance(n,ast.FunctionDef) and n.name=='process_batch_helper')
assignment=next(n for n in ast.walk(func) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='indices' for t in n.targets) and isinstance(n.value,ast.Call) and 'linspace' in ast.unparse(n.value))
expr=compile(ast.Expression(assignment.value),str(SERVER),'eval')
def server_indices(q):return eval(expr,{'np':np,'i':q+1,'NUM_SUBSAMPLED_FRAMES':4}).tolist()
save('code_extraction.json',dict(client_path=CLIENT.relative_to(ROOT).as_posix(),client_sha256=digest(CLIENT),client_function=ast.unparse(fn),server_path=SERVER.relative_to(ROOT).as_posix(),server_sha256=digest(SERVER),server_expression=ast.unparse(assignment.value),server_linenumber=assignment.lineno,model_code_imported=False))

matches=json.loads((UP/'exact_pixel_correspondence.json').read_text('utf-8'))
labels=[json.loads(x) for x in (ROOT/'research/sources/recovery_search_20261003/RoboPulsePlusPlus.jsonl').read_text('utf-8').splitlines()]
videos={618:UP/'stack_three_color_cubes_ep1_58_cam_high.mp4',621:UP/'stack_three_color_cubes_ep2_36_cam_high.mp4'}
rows=[];paths={};eps=[];derivatives=[]
for ep in [621,618]:
 video=videos[ep]
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,avg_frame_rate,duration','-of','json',str(video)]))
 save(f'ep{ep}_ffprobe.json',probe)
 s=probe['streams'][0];a,b=s['avg_frame_rate'].split('/');fps=int(a)/int(b);n=int(s['nb_frames'])
 old=next(x for x in matches if x['episode']==ep)
 pmap={x['logical_frame']:x['source_frame'] for x in old['frames']}
 assert all(x['pixel_exact'] for x in old['frames'])
 native=next(x for x in labels if x['episode_id']==ep)
 grids={'published_array':[pmap[q] for q in range(len(pmap))],'mp4_default_1fps':sample(n,fps,1.)}
 eps.append(dict(episode=ep,video=video.relative_to(ROOT).as_posix(),video_sha256=digest(video),native_task=native,source_fps=fps,source_frame_count=n,grids=grids))
 # Inspect every published falling coordinate, and all raw-client queries from first falling boundary onward.
 boundary=pmap[native['segments'][-1]['start_frame']]
 for branch,grid in grids.items():
  for q,cur in enumerate(grid):
   if cur<boundary:continue
   ix=server_indices(q);src=[grid[j] for j in ix]
   row=dict(episode=ep,branch=branch,query_index=q,current_source_frame=cur,current_playback_seconds=cur/fps,server_indices=ix,source_frames=src,playback_seconds=[j/fps for j in src],no_future_pixels=max(src)<=cur,visibility_review='pending_single_reviewer',original_label='Falling interval binding' if branch=='published_array' else 'NOT transferred as scored label; only placed in source-time span')
   rows.append(row)
   for j in src:
    key=(ep,j)
    if key in paths:continue
    if branch=='published_array':
     logical=grid.index(j);p=ROOT/f'research/sources/recovery_search_20261003/images/ep{ep}/{logical:03d}_view1.png'
    else:
     p=OUT/f'frames/ep{ep}_{j:04d}.png';p.parent.mkdir(parents=True,exist_ok=True)
     if not p.exists():subprocess.run(['ffmpeg','-v','error','-i',str(video),'-vf',f'select=eq(n\\,{j})','-frames:v','1',str(p)],check=True)
     derivatives.append(dict(path=p.relative_to(ROOT).as_posix(),source=video.relative_to(ROOT).as_posix(),source_frame=j,sha256=digest(p),kind='lossless PNG decoded from existing compressed MP4; no AI generation'))
    paths[key]=p

def contact(items,path,cols=4,width=400,height=300):
 canvas=Image.new('RGB',(cols*width,((len(items)+cols-1)//cols)*(height+28)),'white');draw=ImageDraw.Draw(canvas)
 for i,(p,label) in enumerate(items):
  im=Image.open(p).convert('RGB');im.thumbnail((width,height));x=i%cols*width;y=i//cols*(height+28)
  canvas.paste(im,(x,y+28));draw.text((x+4,y+4),label,fill='black')
 canvas.save(path)
for ep in [621,618]:
 for branch in ['published_array','mp4_default_1fps']:
  selected=[r for r in rows if r['episode']==ep and r['branch']==branch]
  items=[(paths[(ep,j)],f'ep{ep} q{r["query_index"]} slot{k} src{j} t={j/25:.2f}s') for r in selected for k,j in enumerate(r['source_frames'])]
  contact(items,OUT/f'ep{ep}_{branch}_packets.jpg')
save('input_manifest.json',dict(status='coordinate reconstruction, not actual inference',model_predictions=None,episodes=eps,queries=rows,exact_model_processor_pixels_verified=False,processor_limit='collator branches and image processor configuration not instantiated; packet views are decoded source images, not verified model tensors'))
save('derived_frames.json',derivatives)
with (OUT/'query_coordinates.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['episode','branch','query','current_source_frame','current_seconds','server_indices','source_frames','source_seconds'])
 for r in rows:w.writerow([r['episode'],r['branch'],r['query_index'],r['current_source_frame'],r['current_playback_seconds'],r['server_indices'],r['source_frames'],r['playback_seconds']])
sources=[CLIENT,SERVER,ROOT/'research/sources/direction_selection_20261003/rbm_heads.py',ROOT/'research/sources/direction_selection_20261003/setup_utils.py',UP/'exact_pixel_correspondence.json',UP/'relation_labels_draft.json',UP/'source_mapping.json',UP/'native_label_mapping.json',ROOT/'research/sources/recovery_search_20261003/RoboPulsePlusPlus.jsonl',*videos.values()]
save('source_hashes.json',[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in sources])
print(json.dumps(dict(queries=len(rows),derived_frames=len(derivatives),grids={x['episode']:x['grids'] for x in eps}),ensure_ascii=False))
