import pathlib
H=pathlib.Path(__file__).resolve().parent
S=H.parent/'atomic_contrast_20261009'
t=(S/'remote_ops.py').read_text(encoding='utf-8')
for a,b in [('change_first_contrast_20261009_v1','change_first_joint_choice_20261009_v1'),('contrast_v1.zip','choice_v1.zip'),('test_contrast.py','test_choice.py'),('contrast_runner.py','choice_runner.py'),('contrast_FINAL.tar.gz','choice_FINAL.tar.gz'),("['deploy','rgb','oracle','status','collect','seal','get']","['deploy','run','status','collect','seal','get']"),("elif a.op in ('rgb','oracle'):","elif a.op=='run':"),(' --block {a.op}',''),('{R}/rgb.log','{R}/run.log')]:t=t.replace(a,b)
(H/'remote_ops.py').write_text(t,encoding='utf-8')
t=(S/'seal_remote.py').read_text(encoding='utf-8').replace('contrast_runner.py','choice_runner.py').replace('contrast_FINAL.tar.gz','choice_FINAL.tar.gz').replace("config['parents']","[config['parent']]")
(H/'seal_remote.py').write_text(t,encoding='utf-8')
