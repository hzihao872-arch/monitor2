# 平面单场景开发候选

六段候选视频及逐帧哈希已生成，真值只在 `truth/`。另一位未见真值的读者约 20:30 审完叠红对抗视频，2/2 完成判定与隔离真值一致，负例明确指出红块承托；正例未另写理由。原答及接收限度见 `../reviews/flat_stack_pilot_reader_raw.md` 和 `../reviews/flat_stack_pilot_receipt_and_comparison.md`。

首次八文件封装未符合现有 `run_monitor_qwen.py` 对四位数字视频名与 `manifest.jsonl` 的要求，已原样转存为 `unadapted_input_v1/` 和 `unadapted_input_v1.zip`，保留这次兼容失败证据。当前 `model_input/` 是六段原字节视频改匿名数字名，加目标句、逐帧哈希清单及运行器清单，共九个文件；`truth/server_alias_map.json` 单独保存数字名与原制样名/条件对应。现有运行器的 `collect_inputs` 和六段实际解码、15 帧像素哈希全部通过。输入专用 `flat_only_development_model_input.zip` 九条目逐项 SHA-256 核对通过，ZIP SHA-256 为 `f7e8f274ce231b9f02e094bb48795871985856f10a5193a25f1d870c27ae6481`。`FLAT_DEV_READY.json` 是单场景开发交接入口；本包不是两机制 `SCENE_READY.json`，也不是方法冻结后的新盲测。

现有运行器的完整 `--dry-run` 路径读取 `model_input/` 并逐段解码，返回 `videos: 6, dry_run: true`；配置与六段输入记录另存在 `truth/server_input_dry_run.jsonl`，未加载模型或读取真值。

**最强反例：** Monitor 仍可能把蓝块叠红的二维入框投影误判为成功。**下一步唯一入口：**在已有服务器上仅用 `model_input/` 做平面单场景开发比较，先封存模型原始输出再由评测侧打开 `truth/`；如需恢复原研究交付，另筛质不同第二机制。
