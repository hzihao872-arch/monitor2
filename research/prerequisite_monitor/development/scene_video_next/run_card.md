# 场景与视频开发运行卡（2026-10-05，上海时间）

**范围与隔离。** 本轮只运行本地原型、静态搜索、单帧渲染、单个开放终态的仿真接触测试及旧文件完整性只读审计。未调用 Monitor、云端模型或 SSH；未下载权重、复跑旧实验、新租或购买资源。旧 `probe.py`、`produce.py`、旧真值与视频未编辑。新增代码只在 `experiments/prerequisite_probe/flat_square_dev.py`、`flat_square_scene.py`、`source_lid_scene.py` 和对应测试；新证据只在本目录。根目录不是 Git 仓库，三处旧源码子仓库本轮检查为 `main...origin/main` 且无短状态改动。

**环境。** Windows 11，本地 `.venv` Python 3.12.3，ManiSkill 3.0.1，SAPIEN 3.0.3，PyTorch 2.11.0+cu128，NumPy 2.5.3。研究工作流 preflight 显示本机 RTX 4060 Laptop GPU 8 GB、磁盘剩余约 62.03 GiB；本轮 ManiSkill 使用 CPU 仿真和 CPU 渲染。SAPIEN 提示可选 `pinocchio` 未安装，但本轮环境创建与预览可运行；未安装新包。

**入口与精确命令**（在 `D:\monitor2` 的 PowerShell 执行）：

```powershell
& 'D:\monitor2\.venv\Scripts\python.exe' 'C:\Users\HANWANG\.codex\skills\agentic-research-workflow\scripts\preflight.py' --project 'D:\monitor2' --json
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.audit_collection
& 'D:\monitor2\.venv\Scripts\python.exe' -m unittest experiments.prerequisite_probe.tests.test_flat_square_dev -v
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.flat_square_dev --output 'research/prerequisite_monitor/development/scene_video_next/flat_square_static_search.json'
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.flat_square_scene --preview-dir 'research/prerequisite_monitor/development/scene_video_next/flat_square_preview/camera_v2'
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.source_lid_scene --preview-dir 'research/prerequisite_monitor/development/scene_video_next/source_lid_preview/v2'
& 'D:\monitor2\.venv\Scripts\python.exe' -c "import json,numpy as np,pathlib; from experiments.prerequisite_probe.probe import PandaIK; ik=PandaIK(); poses={'flat_blue_pick':[-.13,-.13,.019],'flat_target_place':[.18,.10,.019],'source_blue_pick':[-.08,-.07,.019],'source_lid_top':[-.08,-.07,.070]}; out={'solver':'PandaIK.solve','collision_checked':False,'poses':{name:{'target_xyz':xyz,'ik_error_m':ik.solve(np.array(xyz),ik.home_q)[1]} for name,xyz in poses.items()}}; p=pathlib.Path(r'research/prerequisite_monitor/development/scene_video_next/ik_reachability.json'); p.write_text(json.dumps(out,indent=2),encoding='utf-8'); print(str(p))"
& 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' --headless=new --disable-gpu --hide-scrollbars --window-size=1140,520 --screenshot='D:\monitor2\research\prerequisite_monitor\development\scene_video_next\flat_square_terminal_candidates_preview.png' 'file:///D:/monitor2/research/prerequisite_monitor/development/scene_video_next/flat_square_terminal_candidates.svg'
```

**已观察到的输出。** 旧六族只读审计：六族均 `true`。新静态搜索最终 blocked `13714/0`、open `13714/13714`（分母为完整入框候选，后数为红不变时无碰撞候选）。开放场景的放置测试在真实仿真桌面接触与连续 30 控制步后末帧成功。两场景 blocked/open 的单帧尺寸均为 640×480。自由空间四个 IK 目标位置误差均 <0.00081 m，且该筛查明确不含碰撞。TDD 的缺失模块、边界容差和网格覆盖失败先于代码修复；正式测试最终输出另在本轮命令记录中核验。迭代失败及旧计数见 `search_iteration_log.md`。预览图是开发真值，不在 Monitor 输入。

**源文件/协议和分叉。** 平面相机 v1 是旧主视角附近参数；v2 为眼位 `[-0.17,-0.42,0.46]`、目标 `[0.07,-0.01,0.04]`、FOV 0.85。两版渲染来自同一 blocked/open 初始化定义，仅相机不同。源端 v1 与 v2 同目标句但源端几何/视角差异大，都是原型，不能彼此充作完整配对六类。当前新文件 SHA-256 见 `artifact_hashes.sha256`。旧 `probe.py` 的 SHA-256 仍为 `4723422d05775b0733b0902dd9533d67828e31e7946ca0c9e74be7a5fa12037d`，旧 `produce.py` 仍为 `a21cc9f64edb63e3de91da47b3cb9e07da8a5e163d542770726beb58b93aee5c`。

**通过/失败、最强反例。** 当前仅平面谓词的合成负例、开放放置接触及红不变静态终态排除获证；独立语义、两机制严格必要、主视角视频可观察、六类拍摄与操作性效应均未通过。一次放置顺势推红与源端网孔/侧抓仍是强挑战。没有 `SCENE_READY.json`；也没有方法冻结文件或新盲测。

**下一步唯一入口。** 封存第二读者两份原答，先比较平面 A–H；若通过，再进行实际机器人替代路线挑战和主视角盲审。

## 同日审读增补

用户最初误称本人填写两份 v1 审读包，随后更正为朋友填写；其代述未见真值、场景设计或旧分数。两条身份说明、原答、文件时间、哈希、作者事前判断均见 `reviews/review_receipt_v1.md`。平面 E/F、凹槽 F/H 分歧，v1 S0 未通过。平面 v2 句子及 A–I 中性空白包放在 `reader_only_flat_v2/`，尚未有 v2 原答，未改代码中的 v1 指令或任何视频。v2 的 I 图让蓝块两时点都保持在方框内，但位置改变，避免靠出界替“静稳”判错。旧审读包原文未回填或修正。此后唯一入口为未见本对话分歧分析的读者之 v2 原答封存；同一朋友可重复审读，但需注明。

用户随后选择请另一位读者。为便于交接，`flat_square_v2_reader_only.zip` 只收录空白 `reviewer_packet.md`、`terminal_candidates.png`、`terminal_motion_inside.png`；Zip 条目及解压后字节均已逐项验证，无作者答案或旧审读内容。压缩包 SHA-256 `2a2b2e280ef14032ad0b0f893d8b7d7ef32e44fe18f883c27b6818dd3ebf42e6`。下一步唯一入口保持为新读者 A–I 原答与暴露声明。

## 同日 S0 更正、S1 与 S2 试片增补

用户指出第一张 v2 截图发错，确认第二张是另一位读者首次看到材料时的首次答案。错发版和正式版分别封存；正式版 A–I 9/9 与事前预期一致，见 `reviews/review_receipt_v2.md`、`reviews/semantic_comparison_v2.md`。将 v2 目标句写入新 `flat_square_dev.py` 的 `INSTRUCTION`，协议号改 `flat_square_dev_v2`；旧 `probe.py`、`produce.py` 未改。新加动态框内移动负例、路线契约、源端接触/出口测试。测试前有预期的红态失败，改动后完整测试须另核。静态搜索同几何重新得到 blocked `13714/0`、open `13714/13714`。

**新运行入口与命令**（仍在 `D:\monitor2`）：

```powershell
& 'D:\monitor2\.venv\Scripts\python.exe' -m unittest experiments.prerequisite_probe.tests.test_flat_square_dev -v
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.flat_square_dev --output 'research/prerequisite_monitor/development/scene_video_next/flat_square_static_search.json'
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.flat_square_route_challenge --route direct --output 'research/prerequisite_monitor/development/scene_video_next/flat_square_direct_place_challenge.json'
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.flat_square_route_challenge --route lateral_sweep --output 'research/prerequisite_monitor/development/scene_video_next/flat_square_lateral_sweep_challenge.json'
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.flat_square_operational_check --count 20 --output 'research/prerequisite_monitor/development/scene_video_next/flat_square_operational_20seed.json'
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.flat_square_route_challenge --scene source_lid --route direct --output 'research/prerequisite_monitor/development/scene_video_next/source_lid_direct_grasp_challenge.json'
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.flat_square_route_challenge --scene source_lid --route source_direct --output 'research/prerequisite_monitor/development/scene_video_next/source_lid_calibrated_grasp_challenge.json'
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.flat_square_route_challenge --scene source_lid --route source_lid_push --output 'research/prerequisite_monitor/development/scene_video_next/source_lid_push_challenge.json'
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.source_lid_operational_check --count 20 --output 'research/prerequisite_monitor/development/scene_video_next/source_lid_operational_20seed.json'
& 'D:\monitor2\.venv\Scripts\python.exe' -m experiments.prerequisite_probe.scene_observability_pilot --output 'research/prerequisite_monitor/development/scene_video_next/pilot_observability'
```

**结果与限度。** 平面、源端两机制各自的 20 个配对扰动种子均为等待 0/20、有效移障 20/20；原始种子序列、分叉状态与失败控制器版本分文件保存。平面红物不变的合格桌面落位终态被几何排除；源端闭合网格盖的最大出口 14 mm，小于蓝块最小宽 46 mm，墙顶与盖底闭合。两机制支持的是障碍状态必须变化；一次动作能否顺势改变障碍并完成仍非已排除命题。固定控制器的 `C=1` 不替代几何证明，也不能独自证明所有策略必要性。

两机制各自 blocked 快照产生移障/静止 15 秒、1 FPS、640×480 试片，共四个匿名 MP4，实际解码各 15 帧。`pilot_observability/observer_only/` 只含视频、最终指令、审读表、视频与解码帧哈希；`pilot_observability/truth/` 单独保存条件映射、原始渲染帧哈希、初末物体位置与 IK 误差。observer-only ZIP 已按七个允许条目检查，SHA-256 `0ba58942e9667b4afd7ee0ca57cf2ee226038870b88e7497207e7167fdcf2e6d`。试片只做可观察性审读，**不是正式六类，也不是 Monitor 输入**。读者尚未交视频审读原答，S2 待审；`SCENE_READY.json` 不存在。`METHOD_FREEZE.json` 未收到，未建新盲测。

**最强失败及下一步唯一入口。** 源端单段推盖把盖落在夹爪旁、两段推盖后按扰动位置追抓仍失败；`search_iteration_log.md` 保存版本和原始输出。下一步封存只见视频的读者答卷并核 S2；不通过就调整相机/几何后重审，两个机制都通过才拍六类。

**本次核验。** `python -m unittest experiments.prerequisite_probe.tests.test_flat_square_dev -v` 为 27/27 通过；四个匿名 MP4 各有 15 个实际解码帧，索引均为 `0,30,…,420`。ZIP 七条目与 `observer_only/` 七文件逐字节相同，视频文件 SHA 与审读包媒体清单一致，未含映射或状态文件。新旧源代码与开发证据的 `artifact_hashes.sha256` 已重建并逐条重算，无不匹配；旧 `probe.py` 和 `produce.py` SHA 分别仍为 `4723422d05775b0733b0902dd9533d67828e31e7946ca0c9e74be7a5fa12037d`、`a21cc9f64edb63e3de91da47b3cb9e07da8a5e163d542770726beb58b93aee5c`。`SCENE_READY.json`、`METHOD_FREEZE.json`、`new_test_candidates/next_round/` 均不存在，符合当前 S2 待审与未冻结状态。

## 平面单场景开发包交接增补（2026-10-05）

叠红主视角两段原答与独立读者来源已分开封存；2/2 完成判定与真值一致，负例明确指出红物承托，正例未另写理由。原答 SHA-256 `376584b41d0c93a1d41731d993c35f051bc4e00f146b300edfb5d602ae389b3a`。平面 v3 六段先前物理、视频/逐帧与输入隔离审核通过，本次没有复跑旧实验或服务器模型。首次八文件封装不符合现有运行器的数字视频名和 `manifest.jsonl` 要求，保留在 `unadapted_input_v1/` 和同名 ZIP。现行 `model_input/` 含六段原字节视频的数字名、副本目标句、媒体哈希、运行器清单，共九文件；数字别名映射只在 `truth/`。现有 `run_monitor_qwen.py` 的输入收集、全部六段解码与逐帧像素哈希核对均通过；输入 ZIP 九条目内容哈希与 `model_input/` 相同，ZIP SHA-256 `f7e8f274ce231b9f02e094bb48795871985856f10a5193a25f1d870c27ae6481`。交接索引为 `flat_only_six_candidate_v3/FLAT_DEV_READY.json`。

**当前限度与唯一入口。** 只准平面单场景开发比较；第二机制未入选，`SCENE_READY.json` 不签发，方法未冻结且新盲测未制作。架构侧从 `model_input/` 运行并先保存原始输出；评测侧之后才看隔离真值。最强剩余反例是 Monitor 将蓝块叠红的投影误当直接桌面落位。

**运行器无模型核验。** 在 `D:\monitor2` 执行 `D:\monitor2\.venv\Scripts\python.exe -m experiments.prerequisite_probe.run_monitor_qwen --input-dir research/prerequisite_monitor/development/scene_video_next/flat_only_six_candidate_v3/model_input --model-path D:\monitor2 --output research/prerequisite_monitor/development/scene_video_next/flat_only_six_candidate_v3/truth/server_input_dry_run.jsonl --dry-run`，返回 `videos=6, dry_run=true`；未下载或加载模型权重。此为输入链路测试，不是 Monitor 成效试验。
