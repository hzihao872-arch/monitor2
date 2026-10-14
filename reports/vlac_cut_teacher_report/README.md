# VLAC-Cut 中文研究报告交付包

报告日期：2026 年 10 月 3 日。主报告为 8 页中文研究阶段汇报，供导师阅读与讨论。

## 文件入口

- `VLAC-Cut_中文研究报告.pdf`：排版后的最终报告。
- `report.md`：可编辑正文，修改后运行 `build_report.py` 重新生成 PDF。
- `build_report.py`：PDF 排版及拟议方法图源代码，不依赖 TeX。
- `prepare_evidence.py`：公开数据复核、曲线和关键帧资产生成源代码；从当前工作目录下的既有研究材料读取，不覆盖来源。
- `assets/`：四幅图的 PNG／PDF／SVG，及洋葱例 7 个原始解码帧。曲线 PNG 为 300 dpi，SVG 保留可编辑文字；视频帧原始分辨率为 640 × 480。
- `evidence/`：三例作者原始预测与标签副本、固定论文版本和评测实现、来源 URL／哈希、CSV 和补充计算结果。
- `style_profile.md`：参考 PDF 的视觉观察及中文适配记录。
- `qa/`：8 页最终渲染、版面日志、文字／字体核查和逐页验收记录。

## 重建 PDF

在本机 PowerShell 中执行：

```powershell
& 'C:\Users\HANWANG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'D:\monitor2\reports\vlac_cut_teacher_report\build_report.py'
```

脚本需要 ReportLab、matplotlib、Pillow、pypdf，以及 Windows 宋体、黑体、Arial 字体。依赖已经在本机捆绑 Python 中可用，不安装 TeX。若还要从原视频重建证据图，再运行同目录的 `prepare_evidence.py`；该步骤另需 numpy 和已安装的 ffmpeg，并需保留工作目录中的原研究材料。

## 本轮新增证据

1. 检查全部洋葱原始预测点，后半段连续三个相邻区间的预测增量与作者标签反向；早期两个退步区间方向一致。
2. 核对 20 个实际输入帧与原始输出时间：2 Hz 输入和生成的 6.1／8.3 秒时间点不相同。
3. 对 6.1／8.3 秒标签端点各自作 ±15 帧（±0.5 秒）扰动，961 个组合均下降，范围 −13.0 至 −4.6；这不是新推理，也不是 961 个独立样本。
4. 核对三例稠密标签与锚点线性曲线，最大差约 0.05，明确稠密标签不应解释成逐帧独立人工判断。
5. 补齐时间对齐的关键帧和正确方向对照；未找到可以确认的有效准备实证，已在报告中保留缺项。

没有运行 VLAC-Cut、其他模型代替推理或改进系统；未下载权重、训练、调用付费推理、联系作者或发送报告。核心机制仍是待检验假说，方法独特性尚待系统核查。
