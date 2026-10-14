"""Build the editable Markdown manuscript into a Chinese PDF. No TeX required."""
from pathlib import Path
import re,json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY,TA_LEFT
from reportlab.lib.pagesizes import A4
from PIL import Image as PILImage
from pypdf import PdfReader

R=Path(__file__).resolve().parent
A=R/'assets';Q=R/'qa';Q.mkdir(exist_ok=True)
font_manager.fontManager.addfont('C:/Windows/Fonts/msyh.ttc')
plt.rcParams.update({'font.family':'Microsoft YaHei','pdf.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False})
fig,ax=plt.subplots(figsize=(6.55,1.75));ax.set_xlim(0,100);ax.set_ylim(0,32);ax.axis('off')
items=[('任务与对象关系','目标洋葱 → 指定箱体\n同时记录阻挡与可操作性'),('原生进展曲线','冻结基底；保留原始值\n按固定窗口复查'),('局部状态变化','前／中／后帧与全局画面\n绑定证据、反证与不确定'),('有条件修订','有效变化保留；无助重估\n证据不足回退原值')]
for i,(title,desc) in enumerate(items):
    x=i*25+.4
    ax.add_patch(FancyBboxPatch((x,10),23.2,20,boxstyle='round,pad=.3,rounding_size=.8',facecolor='#f3f6f7',edgecolor='#78909a',lw=.7))
    ax.text(x+11.6,25,title,ha='center',va='center',fontsize=9,weight='bold')
    ax.text(x+11.6,17,desc,ha='center',va='center',fontsize=7.2,linespacing=1.6)
    if i<3:ax.annotate('',xy=(x+25,20),xytext=(x+23.3,20),arrowprops=dict(arrowstyle='->',color='#516874',lw=.9))
ax.text(50,3,'输出：原始曲线＋修订曲线＋证据记录＋不确定标记（拟议）',ha='center',fontsize=8.5)
fig.subplots_adjust(left=.01,right=.99,top=.98,bottom=.02)
for ext in ['png','pdf','svg']:fig.savefig(A/f'method_flow.{ext}',dpi=300,facecolor='white',bbox_inches='tight')
plt.close(fig)

pdfmetrics.registerFont(TTFont('Song','C:/Windows/Fonts/simsun.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('Hei','C:/Windows/Fonts/simhei.ttf'))
pdfmetrics.registerFont(TTFont('Symbols','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFontFamily('Song',normal='Song',bold='Hei',italic='Song',boldItalic='Hei')
W,H=A4; LM=58;RM=58; CW=W-LM-RM
styles={
 'body':ParagraphStyle('body',fontName='Song',fontSize=10.5,leading=15.8,alignment=TA_JUSTIFY,wordWrap='CJK',spaceAfter=6.5),
 'title':ParagraphStyle('title',fontName='Hei',fontSize=17,leading=23,alignment=TA_CENTER,spaceAfter=4),
 'subtitle':ParagraphStyle('subtitle',fontName='Song',fontSize=9.5,leading=15,alignment=TA_CENTER,spaceBefore=8,spaceAfter=20),
 'h2':ParagraphStyle('h2',fontName='Hei',fontSize=13,leading=19,spaceBefore=9,spaceAfter=9,keepWithNext=True),
 'h3':ParagraphStyle('h3',fontName='Hei',fontSize=10.8,leading=16,spaceBefore=8,spaceAfter=7,keepWithNext=True),
 'caption':ParagraphStyle('caption',fontName='Song',fontSize=8.8,leading=12.6,wordWrap='CJK',spaceAfter=8,alignment=TA_JUSTIFY),
 'table':ParagraphStyle('table',fontName='Song',fontSize=9.1,leading=13.2,wordWrap='CJK'),
 'th':ParagraphStyle('th',fontName='Hei',fontSize=9.1,leading=13.2,wordWrap='CJK'),
 'ref':ParagraphStyle('ref',fontName='Song',fontSize=9.6,leading=14.6,wordWrap='CJK',spaceAfter=10,alignment=TA_JUSTIFY),
}
def inline(s):
    s=s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<i>\1</i>',s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#276b85">\1</link>',s)
    s=s.replace('−','<font name="Symbols">−</font>')
    return s
def para(s,style='body'):return Paragraph(inline(s),styles[style])

table_weights={
 '原论文指标':[.25,.23,.52],
 '时间／帧（从 0 编号）':[.32,.17,.17,.34],
 '核查窗口':[.19,.46,.35],
 '诊断类别':[.16,.45,.39],
 '实验组':[.23,.47,.30],
 '评价项':[.25,.75],
}
def make_table(lines):
    rows=[[x.strip() for x in line.strip().strip('|').split('|')] for line in lines if not re.match(r'^\|[\s:|\-]+\|$',line.strip())]
    weights=table_weights.get(rows[0][0],[1/len(rows[0])]*len(rows[0]))
    data=[[para(x,'th' if i==0 else 'table') for x in row] for i,row in enumerate(rows)]
    t=Table(data,colWidths=[CW*x for x in weights],hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEABOVE',(0,0),(-1,0),.65,colors.black),('LINEBELOW',(0,0),(-1,0),.4,colors.HexColor('#888888')),('LINEBELOW',(0,-1),(-1,-1),.65,colors.black),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    return t

story=[];lines=(R/'report.md').read_text(encoding='utf-8').splitlines();i=0;refpage=False
while i<len(lines):
    line=lines[i].strip()
    if not line:i+=1;continue
    if line=='<!-- PAGEBREAK -->':story.append(PageBreak());i+=1;continue
    if line.startswith('# '):story.append(para(line[2:],'title'));i+=1;continue
    if line.startswith('研究阶段汇报'):story.append(para(line,'subtitle'));i+=1;continue
    if line.startswith('## '):
        if '参考文献' in line:refpage=True
        story.append(para(line[3:],'h2'));i+=1;continue
    if line.startswith('### '):story.append(para(line[4:],'h3'));i+=1;continue
    if line.startswith('|'):
        tb=[]
        while i<len(lines) and lines[i].strip().startswith('|'):tb.append(lines[i]);i+=1
        story.append(make_table(tb));story.append(Spacer(1,7));continue
    if line.startswith('!['):
        path=R/re.search(r'\]\((.+)\)',line).group(1)
        im=PILImage.open(path); iw,ih=im.size
        story.append(Image(str(path),width=CW,height=CW*ih/iw));story.append(Spacer(1,6));i+=1;continue
    buf=[line];i+=1
    while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','![','<!--')):buf.append(lines[i].strip());i+=1
    txt=' '.join(buf)
    style='caption' if re.match(r'^[图表] \d',txt) else ('ref' if refpage else 'body')
    story.append(para(txt,style))

layout=[]
class AuditDoc(SimpleDocTemplate):
    def afterFlowable(self,f):
        if isinstance(f,Paragraph):
            layout.append(dict(page=self.page,y=round(self.frame._y,2),text=f.getPlainText()[:65]))
def footer(c,doc):
    c.saveState();c.setFillColor(colors.black);c.setFont('Song',9);c.drawCentredString(W/2,25,str(doc.page));c.restoreState()
pdf=R/'VLAC-Cut_中文研究报告.pdf'
doc=AuditDoc(str(pdf),pagesize=A4,rightMargin=RM,leftMargin=LM,topMargin=43,bottomMargin=43,title='VLAC-Cut 的任务进展归因：公开证据复核与免训练验证方案',author='研究阶段汇报',allowSplitting=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(Q/'layout_log.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
reader=PdfReader(pdf);texts=[p.extract_text() for p in reader.pages]
result=dict(pages=len(reader.pages),page_text_lengths=[len(x) for x in texts],pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),forbidden_term_present=bool(re.search(r'\bARS\b','\n'.join(texts),re.I)),replacement_character_present='�' in ''.join(texts),font_resources=sorted(set(str(x.get_object().get('/BaseFont')) for p in reader.pages for x in p['/Resources']['/Font'].get_object().values())))
(Q/'pdf_text_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(Q/'extracted_text.txt').write_text('\n\n'.join(f'PAGE {i+1}\n{x}' for i,x in enumerate(texts)),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
