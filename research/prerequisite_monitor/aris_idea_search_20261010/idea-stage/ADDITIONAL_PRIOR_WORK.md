# 追加一手核查：评测与视觉身份近邻
- O-VAD：Mei Yuan et al., arXiv2607.18142v1, https://arxiv.org/html/2607.18142v1 。项目/作者代码标 ECCV2026，接收身份本轮未另核官方目录。对象grounding→SAM/tubelet状态tracking→无预设异常taxonomy推理→confidence-gated视觉核验。本轮正文已缓存sources/2607.18142v1.html。免训练、状态变化、身份轨迹、再核验的组合已有直接近邻；P1要对比命名先后和同样自动视觉工具，不能只称加跟踪。
- Points2Reward：Junyao Shi et al., RSS2025 workshop; https://points2reward.github.io/ 与作者PDF https://points2reward.github.io/static/Points2Reward.pdf 。示范与rollout跨域对应点、跟踪点后算reward。提供额外成功视频，与主输入不同；引用其点对应技术时不能冒称新。
- PRM-as-a-Judge1.5附录C已读：RoboPulse++把完整轨迹依任务相关状态变化人工分成Rising/Falling区间；SeqStyle对整区间逐帧给进度，五帧causal smoothing用于连续PRM；排除区间头尾各2采样时刻。含撤销后的上下文作用比较。故“密集进退/历史/撤销诊断”已有评价，拟议新协议需明确unknown/部分/冗余与独立功能续行truth，不能只用更多类别宣称新。
- Robots That Take Initiative §II已读：相对于无人机器人帮助的counterfactual轨迹计算value及human/robotcost差，明确减少工作/新增工作。对象为proactivehumanassistance，不是给目标RGBprefixmonitor，但“首次用节省工作证明帮助”不能成立。
- MAGMA-GEN HTML404并不代表paper不存在：arXivabs https://arxiv.org/abs/2609.20056 已确认标题/摘要。完整PDF未读，source/magma_gen_abs.html可核查；其validatedre-execution是E1重要近邻，全文缺口须保留。

补充更正：随后已通过 arXiv PDF 读到 MAGMA-GEN 全文25页，保存 sources/magma_gen.pdf 与 magma_gen.txt。§4.3从同parentstate重执行候选修正/恢复并匹配环境条件，按下游完成筛监督；§3.3区分合法决策与随机执行失败。HTML404的全文缺口已解除。不能主张首次通过counterfactual重执行检验帮助；区别待测在冻结monitor的作用准确性，而不是恢复数据生成。会议接收身份仍未另查目录。

本轮没有模型新成绩。候选pool是生成代理原输出的结构化凝练，保留全部16条和1条executor补充，无基于品味前置剔除。去重规则精确dedup_key，17键均唯一。
