# Robot Monitor A/B/C深入调研交付

文献核查截止2026-10-12；面向师姐的报告重整于2026-10-13。范围是文献探索、研究边界与候选想法；没有实验结果或已确认新颖性。原有研究文件保留。

- **[当前交给师姐的报告](FOR_SENIOR_REPORT_zh.md)**：每条主线按“师姐的直觉→现有研究及边界→一个候选idea”展开，辅助师姐考虑并定题。
- [简洁讨论稿](DISCUSSION_WITH_SENIOR_zh.md)：三条主线各一个想法的口头版本。
- [此前长版研究报告](REPORT_zh.md)：包含原路线排序和详细验证／预算设计，留作历史及备查，当前主报告以上述新文件为准。
- [逐项重合矩阵](OVERLAP_MATRIX_zh.md) / [CSV](overlap_matrix.csv)：27组七维机制对比及决定性对照。
- [可核验文献与版本](LITERATURE_SOURCES_zh.md) / [JSON](literature_sources.json)：56项资源，明确正文/项目/元数据层级。
- [此前讨论稿存档](DISCUSSION_WITH_SENIOR_previous_zh.md)：保留重整前的条件排序版本。
- 阅读笔记：[A](evidence_a.md)、[B](evidence_b.md)、[C](evidence_c.md)、[根任务交叉核查](evidence_root.md)。
- 来源快照：[manifest](SOURCE_MANIFEST_root.json)，公开正文、代码和元数据在sources/a_materials/b_sources/c_sources中；没有模型权重。

build_delivery.py用于此前长版及结构化材料的组装；新主报告直接编辑保存。snapshot_sources.py只抓取公开文献／源码。旧报告中的实验规模和成本是未来建议，不能引用为已测结果。RSI排除。
