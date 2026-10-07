from pathlib import Path
import json
from PIL import Image
from docx import Document
from docx.shared import Inches, Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

ROOT=Path(__file__).resolve().parent
pages=json.loads((ROOT/'manual_content.json').read_text(encoding='utf-8'))
doc=Document();sec=doc.sections[0]
sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=Cm(1.6);sec.bottom_margin=Cm(1.55);sec.left_margin=Cm(1.65);sec.right_margin=Cm(1.65)
sec.header_distance=Cm(.65);sec.footer_distance=Cm(.65)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Caption']:
 st=doc.styles[name];st.font.name='맑은 고딕';st.font.color.rgb=RGBColor(0,0,0)
 st.element.get_or_add_rPr().append(OxmlElement('w:rFonts'))
 st.element.rPr.rFonts.set(qn('w:eastAsia'),'맑은 고딕')
 st.font.size=Pt(10.5)
 st.paragraph_format.space_after=Pt(7);st.paragraph_format.line_spacing=1.22
for element in list(doc.styles.element.iter(qn('w:pBdr'))):
 element.getparent().remove(element)
doc.styles['Subtitle'].font.italic=False
normal=doc.styles['Normal'];normal.paragraph_format.widow_control=True
for name,size in [('Title',30),('Heading 1',21),('Heading 2',12),('Subtitle',14),('Caption',9)]:
 doc.styles[name].font.size=Pt(size)
for name in ['Heading 1','Heading 2']:
 doc.styles[name].font.bold=True;doc.styles[name].paragraph_format.keep_with_next=True
 doc.styles[name].paragraph_format.space_before=Pt(9 if name=='Heading 2' else 0)
doc.styles['Caption'].paragraph_format.space_after=Pt(10)
doc.styles['Caption'].font.color.rgb=RGBColor.from_string('454545')
header=sec.header.paragraphs[0];header.text='CONSTELLATION   /   SCENE DIRECTOR';header.style='Caption';header.runs[0].font.size=Pt(8)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('기획자 실습 매뉴얼   ·   ').font.size=Pt(8)
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');footer._p.append(f)

def text(t,style=None):
 para=doc.add_paragraph(style=style)
 # Keep long resource paths from making a line wider than the page.
 para.add_run(t)
 return para

def figure(item):
 path=ROOT/'assets'/item['image'];w,h=Image.open(path).size
 crop=item.get('crop');width=item.get('width',6.65)
 if crop:x0,y0,x1,y1=crop;ratio=(y1-y0)/(x1-x0)
 else:ratio=h/w
 para=doc.add_paragraph();para.alignment=WD_ALIGN_PARAGRAPH.CENTER
 para.paragraph_format.space_after=Pt(4);para.paragraph_format.keep_with_next=True
 inline=para.add_run().add_picture(str(path),width=Inches(width),height=Inches(width*ratio))
 inline._inline.docPr.set('descr',item.get('caption') or item['image'])
 if crop:
  fill=inline._inline.graphic.graphicData.pic.blipFill
  rect=OxmlElement('a:srcRect')
  for k,v in {'l':x0/w,'t':y0/h,'r':1-x1/w,'b':1-y1/h}.items():rect.set(k,str(round(v*100000)))
  fill.insert(1,rect)
 caption=text(item.get('caption','실제 프로젝트 화면'),'Caption');caption.alignment=WD_ALIGN_PARAGRAPH.CENTER

def table(data):
 cols=len(data[0]);tb=doc.add_table(rows=0,cols=cols);tb.alignment=WD_TABLE_ALIGNMENT.CENTER;tb.autofit=False
 widths=([2.15,4.8] if cols==2 else [1.35,2.5,3.1])
 if data[0][0]=='순서':widths=[.55,3.2,3.2]
 for col,width in zip(tb.columns,widths):col.width=Inches(width)
 pr=tb._tbl.tblPr;borders=OxmlElement('w:tblBorders')
 for n in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+n);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
 pr.append(borders)
 margins=OxmlElement('w:tblCellMar')
 for n,v in [('top',75),('bottom',75),('left',105),('right',105)]:
  e=OxmlElement('w:'+n);e.set(qn('w:w'),str(v));e.set(qn('w:type'),'dxa');margins.append(e)
 pr.append(margins)
 for i,values in enumerate(data):
  row=tb.add_row();trPr=row._tr.get_or_add_trPr();trPr.append(OxmlElement('w:cantSplit'))
  if i==0:trPr.append(OxmlElement('w:tblHeader'))
  for j,val in enumerate(values):
   c=row.cells[j];c.width=Inches(widths[j]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   c.text=val
   for pp in c.paragraphs:
    pp.paragraph_format.space_after=Pt(1);pp.paragraph_format.space_before=Pt(1);pp.paragraph_format.line_spacing=1.13
    for r in pp.runs:r.font.size=Pt(10);r.bold=i==0;r.font.color.rgb=RGBColor.from_string('FFFFFF' if i==0 else '000000')
   shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'243B50' if i==0 else ('EFF3F6' if i%2==0 else 'FFFFFF'));c._tc.get_or_add_tcPr().append(shade)
 gap=doc.add_paragraph();gap.paragraph_format.space_after=Pt(1);gap.paragraph_format.space_before=Pt(0);gap.paragraph_format.line_spacing=1;gap.add_run().font.size=Pt(2)

for i,item in enumerate(pages):
 if i:
  pp=text(f'{i+1:02d}   따라 하기와 참고','Caption');pp.paragraph_format.space_after=Pt(5);pp.paragraph_format.page_break_before=True
 text(item['title'],'Title' if i==0 else 'Heading 1')
 pp=text(item['lead'],'Subtitle' if i==0 else None)
 pp.paragraph_format.space_after=Pt(11)
 if item.get('image'):figure(item)
 for kind,body in item['blocks']:
  if kind=='p':text(body)
  elif kind=='h':text(body,'Heading 2')
  elif kind=='table':table(body)
  elif kind=='steps':
   for n,value in enumerate(body,1):
    pp=doc.add_paragraph();pp.paragraph_format.left_indent=Cm(.6);pp.paragraph_format.first_line_indent=Cm(-.6)
    pp.add_run(f'{n}.  ').bold=True;pp.add_run(value)
 # A short scope note is carried in document properties instead of layout noise.
doc.core_properties.title='연출 툴로 게임 이벤트 만들기'
doc.core_properties.subject='Constellation Scene Director 기획자 실습 매뉴얼'
doc.core_properties.author='Constellation 제작 지원'
doc.core_properties.keywords='Scene Director, 연출, 기획자, 사용 매뉴얼'
doc.save(ROOT/'SceneDirector_기획자_매뉴얼.docx')
print('Saved',ROOT/'SceneDirector_기획자_매뉴얼.docx')
