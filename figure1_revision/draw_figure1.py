from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/pydeps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.font_manager import FontProperties

OUT=Path(__file__).resolve().parent
plt.rcParams.update({'pdf.fonttype':42,'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':7.5})
BLUE='#356894';BROWN='#A36C49';INK='#233442';GRAY='#667582';LINE='#CED6DC'
def draw(lang):
    zh=lang=='zh'
    font=FontProperties(fname=r'C:\Windows\Fonts\msyh.ttc') if zh else FontProperties(family='DejaVu Sans')
    fig=plt.figure(figsize=(180/25.4,123/25.4),facecolor='white')
    ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,180),ylim=(123,0));ax.axis('off')
    texts=[]
    def t(x,y,en,cn='',size=7.5,bold=False,color=INK,ha='left',va='center'):
        obj=ax.text(x,y,cn if zh else en,fontsize=size,fontproperties=(FontProperties(fname=r'C:\Windows\Fonts\msyhbd.ttc') if zh and bold else font),weight='bold' if bold else 'normal',color=color,ha=ha,va=va,linespacing=1.45)
        texts.append(obj);return obj
    def box(x,y,w,h,fill='#F5F7F9',edge=LINE):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=1.1',linewidth=.7,facecolor=fill,edgecolor=edge))
    def arrow(points,color=GRAY):
        for a,b in zip(points[:-2],points[1:-1]):ax.plot([a[0],b[0]],[a[1],b[1]],color=color,lw=.85)
        ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=7,linewidth=.85,color=color,shrinkA=0,shrinkB=0))
    def label(letter,y,en,cn):
        t(3,y,letter,letter,size=10,bold=True);t(10,y,en,cn,size=8.5,bold=True)
    label('a',7,'Controlled generation','受控生成')
    t(177,7,'Experiment 1','实验 1',size=7,color=GRAY,ha='right')
    box(3,15,49,13)
    t(6,19,'Task + designated records','任务与指定记录',bold=True)
    t(6,24,'Fixed across annotation conditions','在不同注释条件下保持不变',size=6.6,color=GRAY)
    box(3,31,49,17,fill='#F7EFE9',edge='#D8BEAB')
    t(6,35,'Annotation varies','注释条件变化',bold=True,color=BROWN)
    t(6,41.8,'Clean / role / workflow / correction','正常／角色冒充／流程借口／纠正',size=6.3)
    box(61,15,47,33)
    t(64,20,'Prompt policy','提示策略',bold=True)
    t(64,27,'Task only','仅任务指令',size=7)
    t(64,34,'+ boundary policy','＋边界策略',size=7)
    t(64,41,'+ evidence binding','＋证据绑定',size=7)
    arrow([(52,21.5),(56,21.5),(56,31.5),(61,31.5)])
    ax.plot([52,56,56],[39.5,39.5,31.5],lw=.85,color=GRAY)
    box(116,23,20,17,fill='#EDF2F5')
    t(126,29,'LLM','LLM',size=9,bold=True,ha='center')
    t(126,35,'2 models','2 个模型',size=6.5,ha='center',color=GRAY)
    arrow([(108,31.5),(116,31.5)])
    box(144,15,33,33,fill='#EDF4F2',edge='#AFC6BD')
    t(160.5,20,'Recorded output','保存原始响应',size=7.1,bold=True,ha='center')
    t(160.5,24,'Requested fields','要求的字段',size=5.8,ha='center',color=GRAY)
    t(147,30,'recipient','接收者',size=7)
    t(147,36,'value','数值',size=7)
    t(147,43,'evidence_ids','证据 ID',size=7)
    arrow([(136,31.5),(144,31.5)])
    ax.plot([3,177],[53,53],color=LINE,lw=.7)
    label('b',59,'Paired replay: change the parser, not the response','配对重放：只改解析器，不改响应')
    box(3,74,32,17,fill='#EDF4F2',edge='#AFC6BD')
    t(19,79,'Same recorded','同一条已保存',bold=True,ha='center',size=7.2)
    t(19,85,'response','响应',bold=True,ha='center',size=7.2)
    box(48,68,59,13,fill='#EDF3F8',edge=BLUE)
    t(51,72,'Strict JSON','严格 JSON 解析',bold=True,color=BLUE)
    t(51,77,'Whole-response JSON only','只接受整段 JSON',size=6.8)
    box(48,87,59,13,fill='#F8EFE9',edge=BROWN)
    t(51,91,'Fence-normalized JSON','围栏规范化解析',bold=True,color=BROWN)
    t(51,96,'Also accept one outer fence','额外接受最外层一对围栏',size=6.8)
    arrow([(35,82.5),(41,82.5),(41,74.5),(48,74.5)],BLUE)
    arrow([(35,82.5),(41,82.5),(41,93.5),(48,93.5)],BROWN)
    box(121,68,56,32,fill='white')
    t(124,72,'Same downstream checks','使用相同的后续检查',bold=True)
    t(124,79,'Schema validity','格式符合性',size=7)
    t(124,85,'Recipient authorization','接收者授权',size=7)
    t(124,91,'Value correctness','数值正确性',size=7)
    t(124,97,'Evidence-ID agreement*','证据 ID 一致性*',size=7)
    arrow([(107,74.5),(114,74.5),(114,78),(121,78)],BLUE)
    arrow([(107,93.5),(114,93.5),(114,91),(121,91)],BROWN)
    t(3,104.5,'No new model calls; no actual dispatch','不新增模型调用；不实际发送报告',size=6.7,color=GRAY)
    t(177,104.5,'*Additional criterion for exact task success','*精确任务成功的附加条件',size=6.4,color=GRAY,ha='right')
    ax.plot([3,177],[109,109],color=LINE,lw=.7)
    t(3,114,'24 tasks × 4 conditions × 3 policies × 2 models × 2 repeats = 1,152 responses',
      '24 个任务 × 4 种条件 × 3 种策略 × 2 个模型 × 2 次重复＝1,152 条响应',size=7.1,bold=True)
    t(3,120,'Recipient guard passed ≠ answer correct','接收者守卫通过 ≠ 答案正确',size=7,color=BROWN,bold=True)
    t(177,120,'48 responses per model–policy–condition cell','每个模型—策略—条件单元 48 条响应',size=6.4,color=GRAY,ha='right')
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    bounds=fig.bbox
    assert all(bounds.contains(*o.get_window_extent(renderer).get_points()[0]) and bounds.contains(*o.get_window_extent(renderer).get_points()[1]) for o in texts)
    for ext in ('pdf','svg','png'):
        fig.savefig(OUT/f'figure1_{lang}.{ext}',dpi=350,facecolor='white')
    plt.close(fig)

if __name__=='__main__':
    for lang in ('en','zh'):draw(lang)
    (OUT/'design_contract.json').write_text(json.dumps({'claim':'Identical recorded outputs are replayed through two acceptance rules; authorization and correctness remain distinct.','scope':'Experiment 1 schematic, not a new experiment or an empirical result plot.','backend':'Python / matplotlib, existing project workflow','size_mm':[180,123],'data':'24 * 4 * 3 * 2 * 2 = 1152 retained responses; 48 per cell','exports':['PDF','SVG with editable text','PNG 350 dpi'],'visual_review':'pending'},indent=2),encoding='utf8')
