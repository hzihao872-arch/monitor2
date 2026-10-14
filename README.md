# Monitor2 机器人任务监测研究

机器人操作任务的执行监测、任务进展与成果有效性研究工作区。仓库保存研究讨论、文献核查、原型代码及已有结果记录。

## 当前讨论入口

- [给师姐的研究思路讨论稿](research/monitor_evolution_literature_20261013/FOR_SENIOR_IDEA_zh.md)：执行反馈如何转成适用范围明确的监督，持续改进任务 Monitor。
- [Monitor 反馈学习文献整理](research/monitor_evolution_literature_20261013/REPORT_zh.md)。
- [Monitor 设计与最小验证方案](research/monitor_evolution_literature_20261013/DESIGN_AND_MVP_zh.md)。
- [RSI 与 Monitor 改进的相关研究](research/rsi_monitor_20261013/REPORT_zh.md)。

上述方案属于研究讨论，创新性和有效性需要后续对照验证。仓库同时保留更早阶段的不同方案及失败记录，应结合各文件日期和适用范围阅读，不能将历史报告当作当前方案已经验证的结果。

## 目录

| 目录 | 内容 |
|---|---|
| `docs/` | 研究计划、架构和工作流程说明 |
| `research/` | 文献、讨论、原型开发、实验协议及历史结果 |
| `experiments/` | 既有实验脚本、配置、测试与结果记录 |
| `reports/` | 研究报告与展示材料 |
| `output/` | 已生成的文档 |

各原型的运行要求以对应目录中的说明为准。部分历史脚本使用本地或服务器绝对路径，需要准备对应依赖和输入后再运行；克隆仓库不等于具备完整运行环境。

## 上传范围

本仓库用于保存项目代码和研究记录。虚拟环境、模型权重、原始视频、大量抽帧数据、重复压缩交付包及完整第三方仓库保留在原工作区，不随 Git 上传。没有删除本地材料。

详见 [仓库范围与本地材料说明](docs/REPOSITORY_SCOPE.md) 和 [第三方仓库来源记录](docs/third_party_repositories.json)。文献与代码摘录的来源、引用和原有权利归属保持不变。
