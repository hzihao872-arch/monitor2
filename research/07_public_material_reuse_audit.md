# 公开材料复用核查：R1 首批与 putspoon 下一小批

日期：2026-10-03。依据[新版续行计划 R1](../docs/plans/2026-10-03-task-progress-research-replan.md)。性质：一名执行者的来源、元数据与少量视频筛查；没有本地 VLM 运行、H1 比较或独立人审。第 1—6 节保留首批当时的记录；本轮结论见第 7 节。

## 1. 执行结论

R-A 已完成现象定位；R-B 第一批筛查已执行，尚未取得合格 H1 正反事件对。不进入 R-C 的模型诊断或 R-E 的效果先导。

- 有现成论文证据，不必要求用户先采数据来证明问题存在。
- Robometer 官方公开库确有任务和质量标签，但检查的 LeRobot 导出版本几乎每条只保留 32 帧，不能直接用于原始时间上的 P0 延迟评测。
- 沿作者转换说明找到可访问的 MIT Franka 原始视频目录，实际取得 3 条失败、1 条成功的外部视角文件。这里的类别都是**来源标签**，不是本项目逐条件真值。
- 看似贴合的 `movemouse` 文本包含避免洒咖啡，但所查起始画面已有侧倒的杯状物与黄色洒出状物体。不能把该静态布景认作本次执行造成的咖啡洒出，也不能用标签替代实际变化事件。
- 新增来源文件共 **22,115,921 B（约 21.09 MiB）**，低于首批 25 MiB；未下载整库、安装环境或取得新权重。

## 2. 来源、版本和可复核位置

| 一手入口 | 固定版本 / 本地证据 | 已核事实与限制 |
|---|---|---|
| [Robometer 官方 OOD 数据](https://huggingface.co/datasets/robometer/rbm-1m-ood/tree/3f3ee69ecc0ee0db627684da7d599ec26d08175c) | revision `3f3ee69ecc0ee0db627684da7d599ec26d08175c`；[来源目录](sources/replan_r1/)、[下载清单与逐件 SHA](sources/replan_r1/fetch_manifest.json) | 读取 README、info、export summary、类别表和四件 Parquet。HF 递归文件树只保留首个最多 1000 项页面，不能冒充完整仓库清单；本节数量依据已下载完整表。 |
| [官方数据转换代码](https://github.com/robometer/robometer/tree/352d160389daa964788de1ec933d1925f3a6de4f/dataset_upload) | commit `352d160389daa964788de1ec933d1925f3a6de4f`；本地 `code_*` 仅阅读，未执行 | `code_new_mit_franka_loader.py:18` 任务映射、约 176 行按质量目录读取；`code_helpers.py:28` 均匀抽帧、约 203/242 行抽帧后按给定 fps 编码；`code_new_mit_franka.yaml:9` 最大 32 帧。所读代码说明转换机制，但没有断言已重放每条发布文件的完整构建过程。 |
| [作者 MIT Franka 数据指南](https://github.com/robometer/robometer/blob/352d160389daa964788de1ec933d1925f3a6de4f/dataset_upload/dataset_guides/NewMITFranka.md) | `code_NewMITFranka.md`，Source、Camera Views、Task Instructions Mapping | 指向原始 Google Drive，说明外部/腕部视角来自同一执行。任务文字由目录名映射，质量标签来自质量子目录；这是作者数据定义，尚未独立核实执行时指令与修订。 |
| [原始目录](https://drive.google.com/drive/folders/1dd62YeKY9-bTeK5fkjljzoFkNX2uZ1YD)、[movemouse](https://drive.google.com/drive/folders/17UnU8d8O9R_n7bWXT1BgCvc6UHbMawFk) | 保存五个目录 HTML、[条目索引](sources/replan_r1/mit_movemouse_directory_index.json)、4 个原始 MP4、ffprobe 与查看帧 | 无登录读取目录和选定公开文件；没有上传或联系作者。HF 导出卡标 Apache-2.0，但本轮原始目录及指南未给可直接核实的原始视频再用许可；仅内部来源核查，正式研究再用与再分发资格未验收。 |

访问失败也保留：匿名 GitHub API 返回 403 速率限制，改用现有 gh 的只读 API 成功；web 工具不能打开 Google Drive，但直接公开 HTTP 可读。不能把这两个工具访问问题表述为作者拒绝开放数据。

## 3. 元数据实查结果（项目计算，不是作者论文成绩）

从 `rbm_episodes.parquet` 和 `rbm_data.parquet` 按 episode 去重：

| 项目 | 结果 | 对研究的影响 |
|---|---|---|
| LeRobot 记录数 | 571，41 个任务文字 | 不是 571 个独立物理 rollout；视角可能重复 |
| 帧数 | 570 条各 32 帧，1 条 21 帧 | 32 帧/10 fps 的播放长度不能当原始执行时长 |
| 来源质量类别 | successful 233、failure 166、suboptimal 172 | 只作筛查；不能生成 `E−/E+` 或逐时有效性 |
| `partial_success` | 571 条均为空字符串 | 字段存在不等于已发布可用部分成功标签；修正上一轮数据卡层面的乐观推断 |
| 逐帧字段 | 时间、帧号、episode/task 索引与来源/质量字段 | 未列动作、对象状态或原始帧到导出帧时间映射 |
| `movemouse` 来源行 | 成功 6、失败 10、次优 2 | 原始目录为 3/5/1 个文件名时间戳，各有 ext/wrist；不能按 18 个独立执行算规模 |
| 跨布局 UUID 联接 | LeRobot 记录与 `mit_franka/metadata.parquet` 的 UUID 交集为 0 | 同任务/同数量不保证逐集对应；不能靠排序拼接或把腕部视角放进测试。原始目录可单独立案，不要求为读取原视频强行恢复此联接 |

完整分组统计：[rbm_metadata_analysis.json](sources/replan_r1/rbm_metadata_analysis.json)。可复算命令与派生表见本节末脚本。LeRobot 布局、同库 `mit_franka` 布局和论文中 100 条实机失败检测集目前不能自动等同。

## 4. 四条实际视频：只记录看见的，不补造失效

选取规则：先取按文件名时间排序的第一条失败与第一条成功外部视角；因首条失败未见目标事件，再取紧随的两条失败，仍受首批字节上限约束。未看模型输出，没有效果选优；所有取得或查看记录都保留。文件名中的时钟是采集标识，和视频播放时间分别记录。

| 本地文件 / 来源时钟 | 媒体事实 | 单人抽帧观察 | 当前纳排 |
|---|---|---|---|
| `mit_movemouse_failure_first_ext.mp4` / 00:22:46 | 655 帧，60 fps，10.916667 s | 1 fps 接触图中末端长时间停在原物体附近，未确证此前成果达成后又失效。 | 保留一般停滞/未完成候选；不纳入 H1 |
| `mit_movemouse_success_first_ext.mp4` / 00:25:18 | 201 帧，60 fps，3.35 s | 末段粉色物体已移到电脑附近；**0 s 画面已有侧倒杯状物及黄色区域**。 | 来源成功不证明全程“未洒”；未取得与某一失效事件匹配的保持标签 |
| `mit_movemouse_failure_2_ext.mp4` / 00:26:30 | 325 帧，60 fps，5.416667 s | 后段夹爪持粉色物体靠近杯状物；**0 s 已有相同侧倒杯状物及黄色区域**。不能把 5 s 画面当作刚刚洒出的证据。 | 原任务失效事件未确证，不纳入 H1 |
| `mit_movemouse_failure_3_ext.mp4` / 00:27:11 | 255 帧，60 fps，4.25 s | 2 fps 抽帧显示抓取附近的操作；未确证“先达成后失效”。 | 不纳入 H1，不由 failure 标签补前史 |

以上是完整文件上的**抽帧筛查**，不是全帧人工审阅或独立标注。60 fps/时长是容器数据，不保证录制没有加速、丢帧或剪辑；尚无动作/传感器同步参考。我们未判定黄色物体究竟是液体、道具还是其他布景，更未给出咖啡条件的 `t_e/t_v`。

证据：[失败例 2 起点](sources/replan_r1/frame_failure_2_0s.jpg)、[失败例 2 后段](sources/replan_r1/frame_failure_2_5s.jpg)、[成功例起点](sources/replan_r1/frame_success_0s.jpg)、[成功例后段](sources/replan_r1/frame_success_3.2s.jpg)。接触图只是查看工具，不是 P0 输入；后续需从源视频单独生成协议固定帧包，不能向模型透露人工事件锚点。

## 5. 当前可复用内容、仍缺内容与独立复核

可直接用于来源研究：官方任务表、来源质量类别、文件目录与同名双视角关系、转换程序、论文证据。现成标签降低筛查工作量，不需要全部重标。

仍缺的不是笼统的“请用户标一套数据”，而是：

1. 一个原任务要求实际经历先成立后失效的具体事件，以及匹配仍有效例；当前四条没有完成此核定。
2. 原始任务定义、采集时间与视频时间对应、参考状态/许可适用范围。`movemouse` 的布景及避免洒咖啡语义需解释，不能擅加“不碰杯子”替代条件。
3. 只对最终选中事件补 P0 首次可判与多段区间、遮挡/修复等缺失字段；现有质量标签不涵盖这些。
4. 在正式 H1 开发比较之前，按 S6-draft-4 做独立盲审。本轮没有第二标注者；没有计算一致率，亦没有制作假装已有答案的盲审包。

整份已读取 LeRobot 元数据纳入开发筛查，保守排除这 571 条记录及对应物理执行的其他视角进入保留测试；`movemouse` 已查任务族也列开发用途。将来保留组必须另选未查看来源/任务组，不利用新 UUID 绕过排除。

## 6. 首批时的下一入口和停止依据（现已执行）

本批到此收束：R-A 完成；R-B 的**首轮筛查动作完成、可用性门槛未通过**。无真实参考事件、许可与时间核定，不运行基线诊断，更不比较 C1。未改 S6-draft-4、工程配置或运行台账；未计算 BCY、效应、显著性及正式规模。

下一件具体公开材料是作者原始 [putspoon 目录](https://drive.google.com/drive/folders/1rcX85A68hgr3ca7vIyXadkrw_Zh449wD)：先查其质量目录与文件规模，核验是否有“成功抓取/放置后丢失”及匹配保持的清楚事件。它仅能作为短片段诊断候选，不能自动支持长时程多要求结论。该任务也无目标事件时，停止在此来源搜 H1；回到论文已有长程案例的原始发布物，而不是穷举所有 failure 视频。原始许可适用与语义说明仍须同时核查，未授权不联系作者。

RoboGraph 的论文 Table 4 继续支持子目标回退现象；本轮论文/作者入口及两条定向检索未核到作者数据下载与许可，第三方综述仓库不充官方发布。它当前属于文献证据，非已取得评测材料。

### 复查方式

在 `D:/monitor2` 运行 `py -3.12 research/sources/replan_r1/reproduce_metadata_audit.py`：使用已有全局 PyArrow（未安装依赖），只读取本地四件 Parquet、重算元数据统计和 UUID 联接结果，核对所有下载文件 SHA，不运行任何模型。

视图生成使用已安装 FFmpeg 7.1.1 的 `fps=1` 或 `fps=2,scale=400:-1,tile=5x5`。首次 drawtext 时间标签转义失败，随后移除该标签成功；截图不是精确事件标签。运行记录见来源目录的 `inspection_frames.json`、`*_ffprobe.json`。初次 HTML 解析采用 Windows 默认 GBK 失败，显式 UTF-8 后成功；源 HTML 未改动。

## 7. R-B 下一小批：作者 putspoon 原始目录与明确的一手后续线索

**筛查规则与规模。** 先保存作者链接的 [putspoon 目录](https://drive.google.com/drive/folders/1rcX85A68hgr3ca7vIyXadkrw_Zh449wD)及三个质量子目录 HTML，再对全部 16 个文件只作 HTTP HEAD。目录有 failure 2 次、suboptimal 5 次、success 1 次物理执行，每次各一个 ext/wrist 视角；不能按 16 次执行计数。所有 HEAD 均返回 `video/mp4` 和字节数。按文件名时钟预选前两条 failure ext、首条 success ext、首条 suboptimal ext；最后一条用于核查低效/调整是否能从现有质量类别解释。其余 ext 受有界规则排除，wrist 属同一次执行的重复视角。完整 16 条逐件纳排、HEAD 字节及 Last-Modified 见[机读筛查记录](sources/replan_r1/mit_putspoon_screening_records.json)、[目录快照与 HEAD](sources/replan_r1/mit_putspoon_metadata_audit.json)。

[官方任务指南](https://github.com/robometer/robometer/blob/352d160389daa964788de1ec933d1925f3a6de4f/dataset_upload/dataset_guides/NewMITFranka.md)把 `putspoon` 映为 “Pick up the spoon and place it inside the cup”，质量类别定义为整条轨迹成功、带低效/错误但完成、或未完成。目录与任务定义的绑定足以做本轮语义筛查；没有逐集聊天记录本身不是排除理由。指南与目录未独立证实执行时输入是否与映射完全相同、是否有修订。目录页面显示 21/22 Jan，文件名含 `Wed_Jan_21_..._2026`，HTTP Last-Modified 为 2026-01-21；这些是文件名/服务器元数据，**不是已校准的执行时间轴或时区**。四个原始 MP4 的容器均为 1280×720、60 fps、3.45—5.12 播放秒；不能仅由编码认定无剪辑、原始墙钟或长时程长度。

| 预选外部视角 / 作者来源类别 | 文件大小、容器长度 | 单人抽帧观察与本轮纳排 |
|---|---:|---|
| 00:17:02 / failure | 4,653,317 B；5.116667 s | 3.0、4.8 s 及全段 2 fps 接触图显示夹爪在餐具旁操作，末尾餐具仍在杯外桌上；**未见先入杯再失效**。排除目标事件；来源 failure 仅能表示整段未完成。 |
| 00:18:32 / failure | 3,572,886 B；3.966667 s | 3.7 s 及接触图显示夹爪接近桌上餐具；未见先入杯再失效。排除目标事件，不能把接近/普通抓取失败写成局部回退。 |
| 00:14:56 / success | 3,091,892 B；3.45 s | 3.3 s 一把勺子看似伸入杯口，是**终态成功候选**；之后片段只剩约 0.15 s，没有后续操作期间仍有效的检验区间。未核成匹配保持反例。 |
| 00:14:20 / suboptimal | 4,434,633 B；5.033333 s | 4.8 s 餐具靠近杯口，抽帧不能可靠分辨是否在杯内及其后状态；来源类别不能自动表示正常调整、修复或历史失效。排除目标事件。 |

观察来自整个文件的 2 fps 接触图和少量原分辨率帧，**不是全帧审阅、对象真值或独立复核**。未对任何片段赋 `t_e/t_v`，没有把终态失败、抓取失败、普通掉落或类别映射成 H1 正例。success 画面只留下候选保持终态，未与已核失效事件配成正反对；四条数秒视频也不能证明长时程多要求判断问题。文件、逐件 SHA-256、预选规则与下载量见[本批视频清单](sources/replan_r1/mit_putspoon_fetch_manifest.json)；接触图和 ffprobe 摘要由[机读筛查记录](sources/replan_r1/mit_putspoon_screening_records.json)索引。四个目录 HTML 的 SHA-256 列在[目录快照](sources/replan_r1/mit_putspoon_metadata_audit.json)。Google Drive 无不可变 revision，本批版本以 2026-10-03 快照、文件 ID、HTTP 元数据与实际字节哈希固定。

四个目录 HTML 共 1,378,022 B，四个 MP4 共 15,752,728 B；本来源新增 **17,130,750 B**。随后针对明确的堆叠坍塌线索保存 [DoReMi 作者项目页](https://sites.google.com/view/doremi-paper) HTML 172,399 B，本批新增来源合计 **17,303,149 B（约 16.50 MiB）**，未超过 25 MiB；未取其他 putspoon 视频或完整库。作者页的 Robot Arm / “Stack blocks in order with placement noise”展示 baseline 与 DoReMi 的坍塌恢复描述，可继续作**文献/演示现象证据**。页面快照只列展示 GIF，未给本轮可核的未剪辑轨迹、任务逐集绑定、原始时间/状态或视频再用许可。两条对应 GIF 的初次 HEAD 曾返回 `image/gif` 及约 4.06/1.15 MB，随后复核 HEAD 返回 403；未下载 GIF，不能把工具访问状态解释成作者拒绝提供数据。[作者页访问探针](sources/replan_r1/doremi_media_manifest.json)保留页面 SHA 与失败，未把展示媒体冒充 H1 轨迹。

**许可与停止决定。** putspoon 的 Drive 文件可公开读取，但作者指南和目录未给可核的原始视频正式研究再用及再分发许可；Robometer 导出卡的 Apache-2.0 不自动传给原视频。已读 Robometer 元数据的 571 条及对应物理执行其他视角、已查 movemouse、putspoon 的全部 8 次执行及对应视角均排除保留测试，不靠更换 UUID 或视角回收。现有标签用于找候选，不足以填“曾入杯→失效”和“仍有效”时间序列。按 R1 停止在 putspoon 继续穷举 failure；DoReMi 作者页提供明确现象但本轮没有合格原始材料入口。R-B 材料验收仍未通过，不进入 R-C，不运行 S0/S1/C1，不制作空壳盲审包；S6-draft-4 未改。下一项具体动作是**仅在出现一手未剪辑堆叠/放置轨迹或其公开映射与再用许可线索时，核该具体文件的任务绑定、原始时钟及同任务保持例**；当前公开入口没有该文件线索，数据分支停在 R-B，不扩展同义检索。用户此时无需采集或标注；若要解除材料缺口，最小外部材料为同任务原要求绑定的完整失效与保持各一条、时间/来源说明及允许研究再用的依据，独立盲审只在选出实际可标材料后办理。


## 8. 新的具体来源与关系失效/保持候选（D049）

2026-10-03 后续核到 RoboPulse++ 实物，不能再把 D048 的局部排除理解为没有公开材料。详见[逐项补查报告](07_alternative_sources_review.md)。ep621/ep618 分别为绿—蓝关系失效/保持单人候选，两条整体进展均可有负标签；已取全发布 view1 帧，尚无原始全帧率映射、明确聚合许可及独立复核。保留 ep620 任务文字/颜色异常。新存 211 项来源、32,602,719 B；先有界筛查，再登记 8 MiB 小批补齐候选；超限 API 中止及 UTF-8 重试保留在审计摘要。未运行模型或 H1，阶段 8 关闭。下一入口为已落盘的 ViFailback 三个堆叠任务原标注 JSON 和作者组织 LeRobot 映射。
