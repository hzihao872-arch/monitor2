# 无黄块平面六类开发候选 v1

**状态：六段无黄块平面单场景开发输入已就绪；不是两机制 `SCENE_READY.json` 或新盲测。** 本包只用蓝块、红块、绿色桌面方框；U0 从开放初态把红块由一个框外位置搬到另一框外位置，没有黄色无关物。v2 自然目标句、成功谓词、绿框/方块尺寸、主视角和 15 秒 1 FPS 640×480 协议未改。旧含黄块 v1–v3 原样保留。

**原始证据。** `truth/mapping_and_trajectories.json` 保存六段各 450 步轨迹、同初态签名、终态谓词与匿名映射；`truth/input_audit.json` 记录独立再解码六段各 15 帧、视频/像素哈希、输入隔离、物理终态均无 issue；`truth/motion_audit.json` 记录动作量和第 14 秒机器人姿态。B+、U0、H− 红块净位移分别约 0.179、0.180、0.178 m；B0 搬出再放回，净位移约 0.0003 m、最大远离初位约 0.178 m；G+ 是唯一满足目标的终态。U0 的 450 个时刻红块投影均未触及绿框，最近的 x 向边缘间隔约 0.105 m。独立 U0 路线预检另存 `../flat_red_only_route_probe_v1.json`。

**旧审读适用范围。** 新 B+ `clip_5108.mp4` 与旧无黄块试片 `clip_0274.mp4` 的 MP4 字节及全部 15 个解码帧哈希完全相同，故旧读者对“红块从绿框移出、蓝块不变”的观察可直接复用。旧平面 N0 `clip_0816.mp4` 是**blocked 初态**，新 N0 `clip_2513.mp4` 是 open 初态，画面不同，不能拿旧判读冒充新 N0 审读。旧无黄块终态示意图曾正确拒绝叠红，但不是本六段视频的独立观察。

**审读包。** `flat_red_only_reader_only.zip` SHA-256 `9aecb28c71bdbadc67bd5ce14e85577ed1e99e67fd14d3bafe2034cfe84b6faa`，仅含六段匿名 MP4、目标句、媒体哈希与空白 `reviewer_packet.md`，共九条目；真值、条件映射、轨迹和作者联系表不在包内。读者首次原答与后续补答均已分开封存，来源与接触声明见审读收据。

**最强反例与限制。** B0 因往返总红块轨迹约 0.406 m，是 B+/U0/H− 单程约 0.21 m 的近两倍；不能声称动作量严格匹配。六段读者答卷支持关键物体变化和整体完成判定可观察，但没有逐项解释 G+ 的直接桌面支撑，也不保证 Monitor 会正确区分叠红与直接桌面支撑。几何排除只支持红块**状态变化**必要性，不支持独立准备步骤必要性。

**审读与开发交接。** 首次原答和同一位读者的补答分开封存；六段核心物体变化及补答的终态完成标签均 6/6 对应隔离真值，详情见 `../reviews/flat_red_only_six_receipt_and_comparison.md` 与 `../reviews/flat_red_only_six_supplement_receipt_and_comparison.md`。补答仍未逐项解释成功片中的底面桌面支撑、夹爪释放和静稳。`model_input/` 有六段原字节匿名视频的数字别名、目标句、媒体清单与运行器清单，共九个文件；条件别名仅在 `truth/server_alias_map.json`。输入专用 ZIP SHA-256 `c99543639e2ac7e8ddf270654d1394f42d6f121021463bf3f452648686183cfa`。已有运行器 dry run 无模型加载，六段各解码 15 帧，逐帧哈希与清单一致，九条 ZIP 内容亦逐字节一致。首次兼容审计因把有序列表与秒数键字典直接比较而误报，错误报告仍存在 `verification/compatibility_audit_v1_invalid_type_comparison.json`；纠正后的 `verification/compatibility_audit.json` 为 pass、issues=[]。交接索引是 `FLAT_DEV_READY.json`。

**下一步唯一入口。** 开发侧只用本目录 `FLAT_DEV_READY.json` 指向的 `model_input/` 或输入专用 ZIP，在已有服务器保存模型原始输出；评分侧之后单独读取 `truth/`。原计划两个质不同机制未齐，不签发 `SCENE_READY.json`；方法未冻结，不造新盲测。
