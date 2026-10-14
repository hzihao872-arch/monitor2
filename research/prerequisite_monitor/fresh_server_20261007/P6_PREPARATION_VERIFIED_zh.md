# P6 本地准备核验（2026-10-07）

用户确认服务器仍关机。P6 仅完成本地预制，**没有模型结果**。

| 核验 | 本地结果 |
| --- | --- |
| 原冻结输入 dry run | 退出码 0；1 条 configuration、18 条匿名 video_input、0 条 model_output；逐视频与 15 帧 RGB 哈希均通过 |
| P6 封存及评分合成测试 | `python -m unittest test_p6_seal -v`：2 项通过；覆盖完整封存、本地验封、缺项、重复、提示 SHA 异常和 raw 篡改；合成标签本地评分符合预期 |
| Bash / PowerShell 语法 | `bash -n run_remote_p6.sh` 通过；`collect_p6.ps1` AST 解析通过 |
| 模型侧代码 ZIP | 仅 `p6pkg/__init__.py`、`p6pkg/run.py`、`p6pkg/seal.py` 三项；无真值、条件映射、评分器、旧输出或密码 |
| P6 代码 ZIP SHA-256 | `27aacffe5588b043e3d582eba30458eca420a6ccb068c1b282e5b81cf3e3d736` |
| P6 运行脚本 SHA-256 | `abaccceacab069b9d5d179bffbac1557b56b37601e6d26735b0622b24814426f` |

开机后仍必须核实例及租期、P0 远端 seal、原输入清单、现存 Qwen 配置和四个分片、GPU/磁盘；身份或哈希不符则停止。P6 pilot 与完整 18 段原答尚未产生，不能将 dry run 写作模型成功。
