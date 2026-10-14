"""Prepend superseding findings while retaining prior research bytes."""
from pathlib import Path
import hashlib
import json

b = Path(__file__).resolve().parent
r = b.parents[1]
updates = {
    'status.md': '''# 研究状态

## 当前入口：已配对 VLAC-Cut 原生错例，ARS 同例效果尚未验证

更新日期：2026-10-03。[ARS 覆盖核查报告](vlac_ars_coverage_audit_20261003.md)已完成：从官方历史版本恢复 3 个展示 episode 的标签，视频与当前仓库一致；前两例的历史/当前 prompt 和预测一致。洋葱例有两个“GT 下降、预测上升”区间，原始输出点也存在反向变化；保留紫色方块、烧杯及洋葱早期退步正确对照。3 段不是总体统计，未复现 AP−。

当前判断：错误物体操作获进展分的解释与 ARS 高度重合，暂不设计“补看＋验证”架构；既未证明 ARS 修好该例，也未证明其失败。下一次有条件的高收益动作是 3 段同例比较，包含简单提示与正确控制；输入清单已备，未运行模型。ARS 本轮 API 403 限流，不当作确认前轮 404。

纠正旧材料结论：历史官方版本有配套 GT；当前 split 前缀解析的 14 条记录均在 task_description 内含百分比步骤，不能当作裸指令。后续对齐任务规划、离线信息及输出尺度，不提供轨迹结果标签。保留 VLAC-Cut 诊断基底，降低泛化“局部退步＋验证”创新叙事优先级。旧 RoboMeter—ProgressCompass 路线仍停止。以下原文完整保留为历史。

---

''',
    'new_baseline_search_20261003.md': '''> **同日后续修正：** 已完成[VLAC-Cut 原生错例与 ARS 覆盖核查](vlac_ars_coverage_audit_20261003.md)。官方历史版本补齐了三个展示例的标签；洋葱例发现可追查的预测方向错误，但错误物体解释与 ARS 高度重合，尚无 ARS 同例实验。另确认 task_description 在所读正式 split 记录中含百分比步骤，不能据字段名推断输入只有任务指令。下文是首轮发现记录；涉及“展示无 GT”和“正式描述不含规划”的旧推断以上述核查为准。

'''
}
checks = []
for name, prefix in updates.items():
    path = r / name
    backup = b / (name + '.before_coverage_audit.bak')
    old = backup.read_bytes() if backup.exists() else path.read_bytes()
    if not backup.exists():
        backup.write_bytes(old)
    new = prefix.encode('utf-8') + old
    path.write_bytes(new)
    assert path.read_bytes().endswith(backup.read_bytes())
    checks.append({'file': str(path), 'backup': str(backup), 'old_bytes_preserved_as_suffix': True,
                   'old_sha256': hashlib.sha256(old).hexdigest(), 'new_sha256': hashlib.sha256(new).hexdigest()})
(b / 'entry_update_validation.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
print(json.dumps(checks, indent=2))
