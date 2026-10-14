"""Local, evaluation-side delivery with original inputs and all evidence; no SSH bridge."""
import datetime,hashlib,json,pathlib,shutil,sys,tarfile
dev=pathlib.Path(__file__).resolve().parent.parent;workspace=dev.parents[2]
out=dev/'runs/diagnostic_20261009_window';delivery=out/'delivery';delivery.mkdir(exist_ok=True)
with tarfile.open(out/'window_v9_FINAL_20261009.tar.gz') as tar:
    # Verify has already succeeded. Extract only safe data and rename original manifest.
    members=[]
    for m in tar.getmembers():
        if not m.isfile() or '..' in pathlib.PurePosixPath(m.name).parts:raise ValueError('unsafe member')
        if m.name.endswith('/seal.json'):
            (delivery/'REMOTE_ORIGINAL_SEAL.json').write_bytes(tar.extractfile(m).read())
        else:members.append(m)
    tar.extractall(delivery, members=members,filter='data')
for name in ('window_v9_FINAL_20261009.tar.gz','FINAL_REPORT_20261009_zh.md','FINAL_ANALYSIS.json','EXTENDED_AUDIT.json','AUDIT_STDOUT.txt'):
    shutil.copy2(out/name,delivery/name)
audit=delivery/'local_audit';audit.mkdir(exist_ok=True)
for name in ('old_audit.json','old_seals_reverified.json','old_full_jsonschema_audit.json','window.json','source_freeze.json'):
    shutil.copy2(dev/'diagnostic_20261009_v9'/name,audit/name)
for p in (dev/'diagnostic_20261009_v9').glob('*_supplied.png'):shutil.copy2(p,audit/p.name)
for name in ('analyze_run.py','audit_final.py','build_delivery.py','ORACLE_PROVENANCE_zh.md','DOWNSTREAM_FAILURE_STOP_zh.md','ORACLE_TEXT_STOP_RULE_zh.md','ORDER_CONTROL_FREEZE_zh.md','REVISION_REASON_zh.md','reference_development_audit.json'):
    shutil.copy2(dev/'diagnostic_20261009_v10'/name,audit/name)
source=delivery/'source_original';source.mkdir(exist_ok=True)
for name in ('pilot_v8.zip',):shutil.copy2(dev/'packages'/name,source/name)
for name in ('protocol_freeze.json','protocol_freeze_v8.json','S1_PILOT_REPORT_20261009_zh.md','SESSION_20261009_1H_zh.md'):
    shutil.copy2(dev/name,source/name)
private=delivery/'private_eval';private.mkdir(exist_ok=True)
shutil.copy2(dev/'private_eval/pilot_v5_selection.json',private/'pilot_v5_selection.json')
old=delivery/'old_results';old.mkdir(exist_ok=True)
names=['s1_v1_results_20261009T121725Z.tar.gz','s1_v2_results_20261009T122427Z.tar.gz','s1_v3_results_20261009T123229Z.tar.gz','v1_length_results_20261009_final.tar.gz']
for n in names:shutil.copy2(dev/'runs/s1_20261009'/n,old/n)
materials=[workspace/'research/prerequisite_monitor/CHANGE_FIRST_IDEA_FREEZE_20261008_zh.md',workspace/'docs/plans/2026-10-08-change-first-monitor-architecture-blueprint-zh.md',workspace/'docs/plans/2026-10-08-change-first-monitor-local-first-implementation-plan-zh.md',workspace/'research/prerequisite_monitor/change_first_blueprint_20261008/S1_RESULTS_REVIEW_20261009_snapshot7_zh.md',workspace/'docs/plans/2026-10-09-change-first-window-diagnostics-zh.md']
for p in materials:shutil.copy2(p,source/p.name)
freeze=json.loads((dev/'protocol_freeze.json').read_text());errors=[p for p,h in freeze['implementation_sha256'].items() if hashlib.sha256((workspace/p).read_bytes()).hexdigest()!=h]
assert not errors
now=datetime.datetime.now(datetime.timezone.utc)
status={'closed_utc':now.isoformat(),'session_elapsed_seconds':now.timestamp()-1791550400,'hard_deadline_epoch':1791557600,'model_stop_epoch':1791556400,'new_requests':50,'old_requests':96,'new_contract_tests_passed':5,'existing_tests_passed':39,'core_freeze_errors':errors,'final_remote_idle_utc':'2026-10-09T13:43:18Z','remote_archive_sha256':'56014e7cd1462c436f802b73fab9c1b0b0e86479ca5c0d09dd21856083bb8b40','remote_archive_member_verification':True,'no_credentials_copied':True,'private_map_evaluation_only':True}
(delivery/'FINAL_LOCAL_STATUS.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
(out/'FINAL_LOCAL_STATUS.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
(delivery/'README_zh.md').write_text('先读 FINAL_REPORT_20261009_zh.md。window_v9/requests.jsonl 和 results 保存全部50次原答，provenance保存远端实际代码/日志/冻结身份。source_original/pilot_v8.zip 为原始合法输入和旧核心；old_results为四份旧最终结果。private_eval仅用于本地评估，不得送入模型。local_audit联系表与oracle为AI审读开发诊断，未经人工双标。local_audit中分析脚本依赖原项目目录布局；成本亦可直接从账本复算。未包含SSH凭据或连接桥。\n',encoding='utf-8')
sys.path.insert(0,str(dev));from collect_and_seal import seal,verify_seal
package=out/'CHANGE_FIRST_DIAGNOSTIC_DELIVERY_20261009.tar.gz'
result=seal(delivery,package);verified=verify_seal(package,result['sha256']);assert verified['valid'],verified
(out/'DELIVERY_VERIFIED.json').write_text(json.dumps({'seal':result,'verified':verified,'closure':status},indent=2),encoding='utf-8')
print(json.dumps({'seal':result,'verified':verified,'elapsed_minutes':status['session_elapsed_seconds']/60},indent=2))
