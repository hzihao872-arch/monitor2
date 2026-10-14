import pathlib,json,shutil
H=pathlib.Path(__file__).resolve().parent;B=H.parent;p=H/'REPORT_zh.md';text=p.read_text(encoding='utf-8')
text=text.replace('当前最有用的线索是**给定具体可见状态时，完整过去帧能改善结构状态读出；但单帧的高置信度、两句话概率差及同题选择都尚不足以支持可靠监测器**。','当前证据显示，**严格格式、更多历史、对象清单或作者式完成度读出，都没有消除自动结构变化发现的漏报与实体绑定错误**。固定终态上的前缀优势未稳定迁移至撤销；正反声明概率差有开发信号，但依然未经独立评估或校准。')
text=text.replace('相同稀疏帧原生视频','相同15全帧原生视频').replace('| gvl_order_v1/v2 | 各16计划 |','| gvl_order_v1/v2 | 各16实际 |').replace('保留v1失败。 |','保留v1失败。v2严格16/16有效，仍将静止蓝块叙述为已放入且chrono/shuffle不一致；停止扩写此提示族。 |').replace('| author_chat_v1 | 24计划 |','| author_chat_v1 | 24实际 |').replace('评分目标仍为最终True条件概率。 |','评分目标仍为最终True条件概率。raw/chat与可见完成代理的一致数20/24、21/24，G的1/7秒及H的1秒仍错误选择True。 |')
needle='表中的比例是开发问题与AI参考的一致数'
new='| precision_transfer_v1 | 40 | 12次新增R正反声明BF16，28次原8题及R6题输出头FP32。两精度正反概率差均14/14与AI参考同向，28个匹配回答零翻转；既有5/8及新增6/6互斥句同时True。不能把相对差当自然事实答案或校准概率。只转换未共享lm_head精度，未训练，主体仍BF16。 |\n| inventory_binding_v1 | 15 | 初始目标盲清单7/8严格有效，7个后续TRACK均有效；1条无效清单的依赖阶段跳过。清单混入机器人，后续仍把面板部件当灰色独立块移动，黄色结构错绑，甚至静止条目算变化。没有通过格式与ID一致性消除语义失败。 |\n\n'
text=text.replace('\n\n'+needle,'\n'+new+needle)
text+='\n\n## 因果范围与包验证\n\n所有模型实际视觉输入均不晚于该请求as_of；自动主线不注入目标、私有真值、手工正确区域或正确状态条件。定向状态题、完成度目标与文字oracle分别标识。PrefixPackage在构造时会对已经物化的14秒开发包整体做完整性哈希；早期题和时刻由AI从暴露素材中选择，因此上述过去帧检查不等于严格端到端在线验证。generated_fact的条件在14秒生成后回查过去帧，已按as_of14记录。\n\n文献源码许可证与来源单列保存；未核验到的许可证不推断。最终ZIP包含已封存系列的完整成员与本地分析，成员逐项SHA复核。没有服务器凭据或模型权重。' if '## 因果范围与包验证' not in text else ''
p.write_text(text,encoding='utf-8');(H/'licenses').mkdir(exist_ok=True)
for src,name in [(pathlib.Path('research/sources/TOPReward/LICENSE'),'TOPReward_LICENSE'),(pathlib.Path('research/sources/PRIMO-R1/transformers-main/LICENSE'),'Transformers_LICENSE')]:
 if src.exists():shutil.copyfile(src,H/'licenses'/name)
(H/'licenses/SOURCE_NOTICES.md').write_text('TOPReward 与 Transformers 随附已取得的原许可证。Robometer 本地 README 声称 MIT，但本次未取得 LICENSE 文件，未臆造许可证。GVL 作者 demo 来源与固定 commit/SHA 见 sources_gvl/PINNED.json，未核验独立 LICENSE；保留来源元数据。各来源片段用于机制审计，不代表作者背书。',encoding='utf-8')
print('report updated')
