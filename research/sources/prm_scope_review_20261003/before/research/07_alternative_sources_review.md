# 停滞后的定向补查：RoboPulse++ 与真实堆叠案例

日期：2026-10-03。承接 R1 / D048；单执行者，只做公开来源和图像筛查。没有模型推理、H1 比较、训练或阶段 8。下文区分作者事实、实际文件检查、单人解释与未解决缺口。

## 1. 对上一轮结果的判断

D048 对 putspoon 的排除有依据：没先达成就不能算达成后失效，片尾成功也不能证明随后保持。问题是该结果只排除了一个来源中的少量候选，并未证明没有现成数据。“停止穷举这一来源”合理，“只能等用户提供材料”不是现有证据能支持的结论。

本轮按具体新增来源开展有界补查：RoboPulse++ 的区间标注、IMBench 的坍塌恢复任务、REBOOT 的失败恢复记录。优先查看前者的实际 JSONL 和图像，后两者停在元数据核验。

## 2. 最重要的新来源：RoboPulse++

- **身份与官方链路**：[PRM-as-a-Judge 项目页](https://prm-as-a-judge.github.io/index.html) → [RoboPulse++ 数据](https://huggingface.co/datasets/lyy0715/RoboPulsePlusPlus)；论文为 [PRM-as-a-Judge 1.5, arXiv:2608.14284v1](https://arxiv.org/html/2608.14284v1)。只精读本轮相关的附录 C，不宣称完成全文方法复现。
- **作者事实（附录 C.2–C.4）**：整段执行结合任务文字作区间标注；公开观测按 1 FPS 采样。数据混合真实机器人与仿真，不能全部称为真实机器人原视频。标注者使用全程上下文，因此不是天然的在线可判真值。
- **实物检查**：固定 revision `abcb94c1e924282c0005e53cff0b22a073de748a`；JSONL 实际 700 行、17,052 个逻辑帧、2,244 个区间。标签计数 `+1:1130, 0:537, -1:577`，429 条记录有负区间；按任务字符串精确分组为 269 组，其中 81 组同时存在有负区间/无负区间记录。这是检索候选，不是 81 组 H1 正反对。论文的 275 task entries 与字符串分组口径不同，暂不指认为错误。
- **标签含义已核**：[数据作者公开回复，discussion #2](https://huggingface.co/datasets/lyy0715/RoboPulsePlusPlus/discussions/2)，`lyy0715`（API 标为 owner）2026-09-02 说明：1 上升、0 停滞、-1 下降，下降不必不可逆。论文二分类评测如何排除/处理发布的 0 仍需另核，不能私自将 0 并为退步。
- **保存位置**：[源文件及哈希清单](sources/recovery_search_20261003/fetch_manifest.json)、[全表统计与候选任务组](sources/recovery_search_20261003/robopulse_annotation_audit.json)。首个目录树响应只覆盖前 1000 项；没有把它当完整媒体目录。选中后另查具体 episode 目录。

## 3. 已找到的具体物理情景，以及反例

首选判断对象是 **绿块当前是否仍在蓝块上**，而不是整段任务是否成功。任务文字还要求随后用另一只机械臂放红块，形成三层结构。下述帧号均是发布包逻辑索引，**不是已验证的原始机器人秒数**。

### ep621：先成立、后被后续操作破坏的候选

本轮取得 view1 全部 29 张发布帧；这是完整的已发布单视角采样序列，不能称未剪辑、全帧率原始轨迹。

- **作者标签**：`[0,22]:+1`，`[22,28]:-1`。
- **单人观察**：开始三块分离；14–19 帧可见绿块在蓝块上，前一机械臂已退开；20–23 帧另一机械臂接近红块和已有堆叠；24–26 帧夹爪遮挡且积木位置变化；27–28 帧可见原来上下关系已破坏，绿块落到前侧、蓝块留在后侧。
- **解释**：这比“总体失败”更直接地体现先前成立关系失效；后续操作与变化同时出现，支持动作副作用候选。但精确接触机制、原始事件时刻和修复后续不能从稀疏单视角补造。
- **暂定事件锚点**：最后清楚成立帧 23，失效证据在 27–28；先只记变化落在这个采样范围内。机械臂遮挡期不猜状态，不把作者负区间起点 22 直接写作 `t_e`，也不把此单人查看写作已完成 P0 的 `t_v` 标注。
- 查看：[全发布帧联系图](sources/recovery_search_20261003/ep621_contact.jpg)，[成立帧 018](sources/recovery_search_20261003/images/ep621/018_view1.png)、[后续操作帧 023](sources/recovery_search_20261003/images/ep621/023_view1.png)、[失效帧 028](sources/recovery_search_20261003/images/ep621/028_view1.png)。

### ep618：整体退步不等于已有关系失效

相同任务文字；作者标签 `[0,18]:+1`、`[18,29]:-1`。本轮取得 view1 全部 30 张发布帧，并查看[全帧联系图](sources/recovery_search_20261003/ep618_contact.jpg)。11–16 帧绿块放到蓝块上且夹爪退开；17–29 帧第二只机械臂随后尝试操作红块，绿—蓝堆叠仍在。

**解释**：它是“同任务族中第一项仍有效”的候选，尽管作者把第二阶段标成总体进度下降。不能为了寻找 E+ 只选全局成功标签，也不能将全局下降直接当作每个条件都失效。它与 ep621 场景布局不同，不是控制其他因素的严格匹配因果实验；保持只限实际观测覆盖范围。

### 所有其他已看记录也保留

| 记录 | 查看范围 | 单人筛查结论 |
|---|---|---|
| ep018 / ep019 | 各自 view1 全发布序列，30 / 52 帧 | 杯子放盘后另操作布丁；ep019 的总体负标签不足以证明杯—盘关系失效，不纳为本次失效对 |
| ep029 / ep030 | 10 / 5 个预选帧 | 抽屉任务有正负标签，但所看图不足以证实先前关系被撤销；不补造事件 |
| ep617 | 9 个预选帧 | 绿—蓝关系保持候选，红块步骤未完成；暂不扩下载 |
| ep620 | 6 个预选帧 | 文字要求绿在蓝上、红再叠上；画面却显示绿叠在红色底块上，蓝块留在侧方。存在任务绑定/颜色语义疑点，不能按全局 +1 当正确完成对照 |

## 4. 哪些已有标签可复用，哪些仍缺

| 内容 | 当前证据 | 使用边界 |
|---|---|---|
| 进展上升、停滞、下降的原生标签 | 实际 JSONL + 作者说明 | 可用于来源筛查和了解既有评测，不能改名为 H/C/P/G 标签 |
| 具体关系先达成后失效 / 仍有效 | ep621 / ep618 图像和任务文字 | 单人开发候选，尚无独立一致性 |
| 数据使用许可 | RoboPulse++ 卡仅 `license: other`，无具体条款 | GitHub 工具代码 Apache-2.0 不能替代聚合图像和新增标注的许可 |
| 原始出处、任务绑定与时钟 | JSONL 无 source_episode_id、动作、原始时间戳 | 下一步追溯上游，不能因论文说 1 FPS 就填物理 `t_e` |
| 独立复核 | 作者称人工标注；本项目没有第二人结果 | 作者全程进展标签不自动覆盖本项目逐要求在线判断 |
| 在线输入公平性 | 本轮看的是原分辨率发布图 | 尚未审核 P0 256² 实际四帧包，不能声称本地模型可识别该事件 |

**现在不需要用户从头标整个库。** 先用既有标签找到事件与对照，追原始映射；仅对最终影响判断的关系、遮挡边界及可判性做少量补审。当前不启动 H1，也不计算效应/显著性/样本规模。

## 5. 最近研究对创新性的影响

**作者事实**：附录 C.5.2 / Table 8 专门讨论已完成子目标后续被撤销的上下文依赖案例，并比较 Pair Style 的 Robo-Dopamine 与 Sequence Style 的 RoboMeter。该研究已经触及我们的核心动机，不能称“以前只看终态、没人研究历史进展失效”。

**我们的解释**：这是必须纳入的最近工作，而不是照搬它的模块。其比较跨模型、训练和推理形式；Sequence Style 的 C.4.2 使用人工区间内整段序列，不能直接解释为同模型、相同因果前缀、相同预算下“历史机制”的净贡献。这些差别只界定尚需核验的比较，不足以证明我们有新颖性或一定有收益。

**下一研究动作**：数据可再用后先用强基线及最近方法的合法可比目标检查剩余错误；若通用滚动摘要/逐项检查就能解决，不再为 C1 找存在理由。不因新数据出现而批准架构。

## 6. 另外两项来源为何暂不主攻

- **IMBench**：[论文附录 B.2.6 T28](https://arxiv.org/html/2607.15641v1)及[官方数据](https://huggingface.co/datasets/imbench/pb-puzzle-stack-collapse-recovery-v1)，revision `f3011c78d7960059b0192ac2349a0959fb33a8e1`。实际元数据为 10 次仿真执行，有 episode 时段、100 Hz 数据说明、三相机和对象状态字段，数据卡 Apache-2.0。论文明确初始就预先堆好，再由外力推倒，目标是重建；因此支持外生扰动情景，不能直接证明机器人自己完成的第一步被第二步破坏。全成功示范不代表没有中间失效，但本轮未取视频/帧数据，也未找到相同任务无扰动对照。
- **REBOOT**：[作者页](https://nanayawoa.github.io/REBOOT/)提供精密装配失败恢复证据；实查 `REBOOT26/USB-A_recovery_install` revision `cfa3498a3982eb24554e88e77140247871eee3eb`。作者页写 CC-BY-4.0，数据卡却 Apache-2.0，需澄清适用范围。数据块约数百 MB，不因名称含 recovery 就下载；本轮仅元数据。也不能将对齐重试自动当作已实现任务条件失效。

## 7. 下一项具体入口

追溯 **RoboPulse++ ep621 / ep618 → 上游原始轨迹 ID、任务与时间映射**。论文 C.2 列有 ViFailback；其[作者项目页](https://x1nyuzhou.github.io/vifailback.github.io/)公开链接 [ViFailback-Dataset](https://huggingface.co/datasets/sii-rhos-ai/ViFailback-Dataset) 和[作者组织 LeRobot 导出](https://huggingface.co/datasets/sii-rhos-ai/vifailback-dataset-lerobot)，两者数据卡均标 MIT。原库 revision `21df46c2585c52e5a62df5f4b946bae6cbc6fed7` 的 `annotated_data/` 与 `raw_data/` 均已核到 `stack_three_block`、`stack_three_color_cubes_ep1`、`stack_three_color_cubes_ep2` 目录。导出卡说明有逐集原始路径、任务、avoid/correct 稀疏关键帧；这些关键帧也不自动等于本项目事件时刻。**尚未证明这两个 episode 就对应其中哪个文件**，不能把上游 MIT 自动转授给 RoboPulse++ 新标注。另有 typoverflow 转换版，但本轮以作者项目页实际链接的组织版为准。

先按三层堆叠任务查元数据/critical-frame 标注与原 episode 映射，再取对应极少量原始帧和镜头；不下载整库。不再在 putspoon 短片中盲找，也不把没有上游映射说成没有现象。R-B 已有明确新入口，R-C 模型诊断、H1 和阶段 8 尚未放行。

## 8. 原始来源追溯结果（2026-10-03 续行，D050）

本节更新前文的“尚未映射”，保留前述筛查历史。**两条记录已匹配到 ViFailback 原库的具体发布视频，全部 59 张 RoboPulse++ view1 图像与对应视频解码帧逐像素一致。** 这是媒体内容身份的强证据，不是只按相同任务文字猜测。原始 HDF5 的路径和 LFS 哈希已取得，但没有下载原始传感器文件，不能称已核验完整原始采集过程。

| RoboPulse++ | 原库任务 / episode | LeRobot episode | 原库高视角视频 | 单人条件判断 |
|---|---|---|---|---|
| ep618 | `stack_three_color_cubes_ep1 / episode_58` | `5060` | 376 帧，25 fps，15.04 秒，最后帧时间 15.00 秒 | 绿在蓝上的关系建立后，后续右臂尝试失败，但该关系保持至记录结束 |
| ep621 | `stack_three_color_cubes_ep2 / episode_36` | `5197` | 361 帧，25 fps，14.44 秒，最后帧时间 14.40 秒 | 关系先成立；右臂随后操作既有堆叠，关系被破坏，记录结束前未见恢复 |

原库 revision 为 `21df46c2585c52e5a62df5f4b946bae6cbc6fed7`；作者链接的 LeRobot revision 为 `619791b94f61667333fe179d471051e0bca0e06f`。两条原标注的 `task`、8 项 `subtasks`、`images`、`video` 和关键帧均有实物；与 LeRobot 保存的嵌套 annotation 完全相同，Parquet 的 `task_index` 均为 99。两条原记录**没有 `source_index` 字段**，实际以文件路径和逐帧内容建立映射，不补造该字段，也不把 annotation 数组位置当作 episode ID。未提供任务修订日志；这是“没有该字段”，不是已经证明从未修订。采用 R1 允许的官方任务定义与 episode 可靠绑定，不要求用户补逐条聊天原话。

可核材料：[来源映射](sources/recovery_search_20261003/upstream_trace/source_mapping.json)、[全帧对应表](sources/recovery_search_20261003/upstream_trace/frame_correspondence.json)、[59 帧像素一致性](sources/recovery_search_20261003/upstream_trace/exact_pixel_correspondence.json)、[ep618 多时刻对照](sources/recovery_search_20261003/upstream_trace/ep618_multi_time_match.jpg)、[ep621 多时刻对照](sources/recovery_search_20261003/upstream_trace/ep621_multi_time_match.jpg)、[原任务与转换映射](sources/recovery_search_20261003/upstream_trace/selected_lerobot_annotations.json)。原库视频也可直接核验：[episode_58](https://huggingface.co/datasets/sii-rhos-ai/ViFailback-Dataset/blob/21df46c2585c52e5a62df5f4b946bae6cbc6fed7/annotated_data/stack_three_color_cubes_ep1/videos/episode_58_cam_high.mp4)、[episode_36](https://huggingface.co/datasets/sii-rhos-ai/ViFailback-Dataset/blob/21df46c2585c52e5a62df5f4b946bae6cbc6fed7/annotated_data/stack_three_color_cubes_ep2/videos/episode_36_cam_high.mp4)。不声称在所有未检查的仓库副本中全局唯一；同内容原始轨迹和其他视角全部仅开发。

### 8.1 四种时间坐标必须分开

1. **发布逻辑帧 k**：ep618 为 0—29，ep621 为 0—28，只是 RoboPulse++ 图像索引。
2. **上游视频帧 n**：两条实测均满足 `n=floor(6.25+12.5k)`，即 6、18、31、43……。所有对应帧像素完全一致；这个公式只描述这两条记录，尚未取得全库抽帧实现。
3. **播放秒 / LeRobot 导出秒**：上游视频 `n/25`，Parquet 时间与之最大误差约 `4.58e-7` 秒。逻辑帧间实际相隔 12/13 个视频帧，即约 0.48/0.52 播放秒。因此此前论文所述“1 FPS”不能直接套到这两条发布索引；到底哪个处理步骤改变采样尚未核定，不能将 k=22 记为机器人第 22 秒。
4. **机器人采集时间**：未取得硬件时间戳或采集／转换代码的充分依据。MP4 fps、LeRobot 均匀时间列本身不能证明真实采集节拍。本次只做发布视频时间坐标上的离线观察诊断，不报告物理检出延迟或实时吞吐。

RoboPulse++ ep621 的负区间起点 k=22 对应 n=281、播放 11.24 秒，此时绿—蓝关系仍可见；ep618 的 k=18 对应 n=231、9.24 秒，关系也仍在。不能用这两个负标签起点作关系 `t_e`。ViFailback 的 avoid/correct 帧分别为 ep618 的 277/334、ep621 的 275/338；它们是避免／纠正指引锚点，**correct 不表示实际发生修复**。详见[时间与标注审计](sources/recovery_search_20261003/upstream_trace/time_and_annotation_audit.json)。

额外[同视角转换核对](sources/recovery_search_20261003/upstream_trace/lerobot_ep618_alignment_audit.json)中，ep618 的 6 个预选时刻有 5 个最近画面索引与原库完全一致，近静止末帧 375 的最小像素差匹配到转换帧 374。AV1 有损编码下不能把最近像素差当独立精确同步证明，保留这一末帧歧义，不据此修订时间。右腕视频的共同索引依作者同步声明及相符场景／动作作参考，未独立证明硬件级、亚帧级同步；P0 仍只用逐像素匹配成立的原库高视角视频。

### 8.2 许可、预算与否定发现

原库固定版本 [README](sources/recovery_search_20261003/vifailback_README.md)明确声明 MIT；作者链接的[转换版卡](sources/recovery_search_20261003/vifailback_lerobot_README.md)也声明 MIT 并要求遵循原库条款／引用。后续本地诊断**直接使用原库高视角媒体和原任务**，保留来源卡与署名信息。RoboPulse++ 的 `other` 仍没有具体附加条款；其新进展区间只留作来源核查，不作为本项目可再分发真值或模型输入，不把上游 MIT 转授给新标注。

本批新保存 **55 个来源文件，26,105,349 B（约 24.90 MiB）**，未超过预先登记的 25 MiB。含两条原库高视角 MP4、ep618 的一个 LeRobot 高视角核对视频、ep621 的一个右腕参考视频及小型元数据／候选首帧。LeRobot 大标注文件仅请求尾部 1,553,675 B，HTTP 206 与 Content-Range 留档；丢弃首行残片后解析，未取 15.55 MB 全文件。原 HDF5 分别为 153,612,328 / 82,596,495 B，仅登记大小和上游哈希，未下载。

一次 JPEG TLS 失败、一次单文件大小拒绝及一个会超过总预算的重复高视角请求均保留，未把失败当下载成功。后者改取必要右腕视角后仍在原批上限内。按时长猜测的首批候选被场景／物体布局排除；橙—绿—蓝 `stack_three_block` 任务也排除。全部已看候选见[纳排表](sources/recovery_search_20261003/upstream_trace/candidate_dispositions.json)、[失败与范围记录](sources/recovery_search_20261003/upstream_trace/fetch_failures_and_scope.json)、[来源 URL／大小／SHA](sources/recovery_search_20261003/upstream_trace/fetch_manifest.json)。旧 211 项来源重新校验通过，未重下载。

### 8.3 参考条件、P0 与最小补审

**ep621**：原生失败类型是 `task planning`，失败子任务为第 5 项“右臂对准红块”；实际右臂接近已经建立的绿—蓝堆叠，红块仍在灰色台面上。高视角密集帧与右腕参考共同支持堆叠关系被破坏。单人保守变化范围暂记视频 n=290—310（11.6—12.4 播放秒），不是独立真值，更不是精确力学接触时刻。右腕图像补足了高视角遮挡，**不送给 P0 模型**。此前“绿落前、蓝留后”的具体运动描述过强；本轮只确认相对支撑关系破坏，不声称蓝始终固定或精确掉落机制。后续动作也没有成功完成“放红块”子目标，因此只能支持“后续错误操作破坏已有成果”，不能包装为“后续子任务成功同时造成副作用”的已核案例。

**ep618**：原生失败类型是 `gripper 6d-pose`，同样是第 5 子任务。全记录的后续右臂尝试未完成红块步骤，但可见绿—蓝关系持续保持。没有把“全任务失败”改称成功，只将第一项当前关系作为保持候选。两例布局和错误类型不同，不是控制其他因素的严格因果配对。

实际 P0 从上游视频取每整数秒最近过去帧，缩到 256×256，共 16 / 15 个钟；包顺序沿用当前、起始、t−1、t−5，去重，全前缀同源。已保存[ep618 实际 P0](sources/recovery_search_20261003/upstream_trace/ep618_P0_contact.jpg)、[ep621 实际 P0](sources/recovery_search_20261003/upstream_trace/ep621_P0_contact.jpg)和两份逐钟 packet manifest。单人草案中 ep618 自 q=6 可确认关系，后续保持；ep621 q=8—11 可确认成立，q=12—13 保留不确定，q=14 是首个暂定失效可判钟。**此人已见完整参考，不能冒充独立前缀盲审**，尤其 q=14 仍有部分遮挡，需要复核。

现有作者标签可复用任务／对象定义、episode 绑定、整轨失败、失败子任务与类型、关键帧导航；不能充 H/C/P/G、关系变化区间或 P0 `t_v`。只补后面这些缺失字段，见[原生标签映射](sources/recovery_search_20261003/upstream_trace/native_label_mapping.json)、[模型运行前冻结的单人草案](sources/recovery_search_20261003/upstream_trace/relation_labels_draft.json)、[最小独立复核说明](07_independent_review_handoff.md)。两条只有约 15 秒，是多步骤条件变化的具体开发例，不能独自支撑长时程泛化、正常调整／停滞完整区分或任何闭环收益。保持 S6-draft-4、S7-screening-4 和阶段 8 关闭。

## 9. R-C 首次探索诊断：发现格式与摘要执行失败（D051）

材料已满足**发布视频坐标下的探索诊断**条件：原库 MIT 声明、可靠任务绑定、已核帧顺序／导出时间、可追溯单人参考和实际 P0 包。硬件时钟、独立复核与 H1 仍未通过。运行前固定了[样例／提示／预算／一次迭代及输入哈希](sources/recovery_search_20261003/upstream_trace/diagnostic_preregistration.json)，使用已有冻结 Qwen3-VL-2B-Instruct BF16，只跑 S0/S1，无 C1、训练、网络模型调用或重跑烟测。

**实际结果不是有效的强基线比较。**四条运行共 62 次调用都执行到末钟，但严格解析结果全部 `invalid_json`：31 个 S0 响应均带代码围栏；31 个 S1 响应也带围栏，且全部生成至 256 token 上限，出现重复／不完整输出。S1 提示要求带时间的通用视觉摘要、保留先前达成和不确定性、核对各项条件；实际却没有任何合法摘要被接受，所有后续 `memory_in` 仍为空。因此只能说“强 S1 方案的本次接口执行未成功”，不能用它证明合理滚动摘要仍无法解决关系失效，也不能称已给予有效的强基线比较机会。

合计输入 **40,526 token**、输出 **9,888 token**、逐钟累计墙钟约 **360.02 秒**，PyTorch 峰值显存 **4,501,991,424 B**；初始化另存，不混入这些逐钟成本。全部调用遵守 B1 上限，同轨 S0/S1 的实际包及全前缀 SHA 一致。未事后剥围栏重算“有效输出”，未根据模型表现重标／选例，未调第二版提示或额外调用。原始输出、错误和实际成本见[诊断审计](sources/recovery_search_20261003/upstream_trace/diagnostic_audit.json)、[08 §9](08_pilot_report.md)、[运行台账](../experiments/run_ledger.csv)。没有 BCY 效应、显著性、样本规模或架构收益。

**下一步单一执行入口**：先针对这次已证实的格式／摘要长度问题，制定下一批有限预算的提示修复预注册，在同一两条已冻结开发轨迹上确认纯 JSON 和摘要实际跨钟传递，再诊断 S0／强 S1 的感知或历史状态错误。当前一版一次的预算已经用完，不靠更名追加调参。独立复核最小包已经可交付，无需重标整个库；未复核前 H1 效果比较继续停止。若将来需要硬件延迟，下一件具体源文件是上述两个原 HDF5 的 header／attributes 或对应采集／转换脚本，先有界读取，不下载全库。

收尾核验：[来源／像素／时间检查](sources/recovery_search_20261003/upstream_trace/verification_summary.json)与[本地链接／JSON／数据清单／台账检查](sources/recovery_search_20261003/upstream_trace/final_validation.json)。新旧源文件无 SHA 错误，新增台账恰为四条真实运行；模型输出非法率与材料核验通过是两件事，不混称“研究通过”。


## 10. R-C 后续有限修复的实际结果（D052）

来源匹配和单人关系草案保持 §8 的结论：ep621 为既有绿—蓝关系后续失效，ep618 为后续整体尝试失败但该关系保持；没有新的独立人审。本轮未下载任何数据，也未修改实际 P0、原标签映射或参考草案。

用户授权继续后，[运行前预注册](../experiments/artifacts/r1_interface_repair_20261003/preregistration.json)固定两版有限提示修复、ep618 q=0—2 的短前缀检查，以及接口通过后才启动完整轨迹的门槛。**实际只有 12 次探针，两个候选均未通过**：S0 六条变为严格合法但全未知；S1 六条仍非法（五条重复到 token 上限，一条多右括号），没有摘要成功传递。因此未运行余下完整 62 次；没有强基线效果或架构结论。旧首次 62 次失败完整保留，本批不做输出清洗或更名加跑。

实际新增 6,879 输入 / 1,603 输出 token，逐钟约 56.06 秒，四条真实台账；详细原文、候选门槛、成本和局限见[08 §10](08_pilot_report.md)、[本批审计](../experiments/artifacts/r1_interface_repair_20261003/audit.json)。266 个既存来源和 42 项运行前冻结文件重新校验通过，无新增来源范围。协议 S6-draft-4、清单 S7-screening-4 不变。

下一项具体排查对象已缩小为[短摘要候选的原始输出](../experiments/artifacts/r1_interface_repair_20261003/probe_B_S1/records.jsonl)：q=0 的重复摘要、q=2 的多括号。须在新的有界预注册中隔离摘要本身与组合结构输出，先验证真实摘要跨钟，再讨论感知/历史错误；本批到停止条件即结束。独立关系/P0 前缀复核仍是最小外部材料缺口，[交接包](07_independent_review_handoff.md)无需重标作者已给的任务、失败类型和子任务。R-C 未完成，H1、机制选择和阶段 8 未放行。


## 11. R-C 隔离诊断把瓶颈定位到零历史的视觉依据（D053）

本批复用原 ep618 的实际 q=0、2、6 帧包，没有新增来源、改标签或改时间/许可解释。任务语义和来源匹配继续按 §8。先固定纯文本摘要、仅摘要 JSON、判断＋摘要 JSON 三种输出契约，实际执行九次冻结模型调用。组合 JSON 三次严格合法，但在三块分开的 q=0 单帧也宣称三层已完成；纯文本同样错误。q=6 的绿—蓝关系与草案相容，但红块尚未放上，模型仍报整任务完成。

因此本批发现超出了标点格式：**零历史时已有画面与完成判断不符，不能归因记忆遗忘，也不能据此推进 C1。**仅摘要 JSON 两次重复至上限，组合 JSON 反而正常结束，故不能简单认定组合输出本身导致重复。尚未区分视觉识别不足与目标文字诱导。所有内容核查均为单人开发判断，没有独立人审或 H1 效应。

预注册的内容门槛失败后停止，未进行连续九钟摘要或完整 62 次；实际新增 4,272 / 923 输入/输出 token、约 32.37 秒推理与输出检查、九条台账。模型原文、同帧同上下文对照、CPU 处理器重建与 SHA 见[08 §11](08_pilot_report.md)、[隔离审计](../experiments/artifacts/r1_summary_isolation_20261003/audit.json)及[内容核查](../experiments/artifacts/r1_summary_isolation_20261003/isolation_review.json)。原 266 来源与单人标签草案哈希保持。

下一项具体动作是用[ep618 q=0 原 P0 图](sources/recovery_search_20261003/upstream_trace/p0/ep618/frame_00.png)隔离中性视觉描述与原任务条件描述，先查为何把目标说成已完成；另行冻结小预算，不继续本批剩余条件调用。原生任务/失败类型/子任务/关键帧仍可复用，对象关系/P0可判性仍待最小独立补审。协议 S6-draft-4、清单 S7-screening-4 不变，H1与阶段8关闭。


## 12. 已下载本地更大模型的可行性核查（D054）

用户授权检查并试用已有更强模型，实际发现Ollama中已有Qwen3-VL 8B/4B Q4_K_M；本批只调用8B，无新模型/来源下载。原视频、任务、许可、P0和单人标签草案均未变。预注册四次探针后才允许连续/完整诊断，结果为：q0中性描述及任务摘要能正确保留积木分离状态；q2在绿块受遮挡时仍过早确认绿在蓝上；q6四帧请求因4457 token超过4096上下文被本地服务拒绝。

因此8B在本机可运行，且q0文字观察比此前2B更贴近画面，但不能称已获得可靠强S1。Ollama本次使用每图至少1024视觉token，与此前HF64/图不同，四图已占满原4096预算；未静默加大上下文或删除帧重试。两个内容/运行门槛未通过，四调用到此停止，未用4B或完整两轨迹。详见[08 §12](08_pilot_report.md)、[审计](../experiments/artifacts/r1_local_stronger_20261003/audit.json)、[原文与内容核查](../experiments/artifacts/r1_local_stronger_20261003/probe_review.json)。

这次不是ViFailback-8B或RoboMeter等作者方法复现。下一步应以8B可用性为基础先对齐官方输入和单列后端预算，仍需独立复核原关系/P0字段；不改变原作者失败标签，不把监测模型自身失误当机器人错误或新机制证据。S6-draft-4/S7-screening-4保留，H1/阶段8不放行。
