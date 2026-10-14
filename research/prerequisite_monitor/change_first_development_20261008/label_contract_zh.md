# 私有标签合同 v1

每个匿名查询保存 `physical_truth`（仿真状态/有限续行路线）和 `visual_reference`（只看该 RGB 前缀与目标可审定的事件及状态），并单独记录 `visual_judgability`。主模型输入不得接触本文件的样本答案或标签文件。

- `goal_done` 要求截至当前已拥有稳定窗口；不能借未来帧补确认。
- `direct_ready` 在不改变目标物以外环境结构的条件下按固定通用技能类判断；有限续行失败不证明所有控制器均不能完成。
- `partial_preparation` 要有目标相关条件改善、但还未直接就绪；单纯位移不足以标真。
- 事件作用为 `beneficial/harmful/irrelevant/mixed/unknown`。`irrelevant` 需要支持关系无关的证据，非“没找到有利”。
- `reversal` 必须指向本前缀内先前已支持的相同目标关系成就；末态与初态相同不抹掉中间事件。
- 双人独立审读、隐藏方法身份；当前只有开发预审模板，不能写成已有人审。争议保留 ambiguous。

评估按实体及时间容差先匹配事件，再比较作用；漏检为 FN，虚构为 FP，unknown/无效在可审定分母内。无事件查询单列特异度。cluster 为配对 bootstrap 单位；小 pilot 只报分子分母。
