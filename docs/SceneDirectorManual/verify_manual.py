from pathlib import Path
import json
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent
out=root/'qa/render-final';out.mkdir(exist_ok=True,parents=True)
r=PdfReader(root/'SceneDirector_기획자_매뉴얼.pdf');info=[]
for i,p in enumerate(r.pages):
 t=p.extract_text() or '';info.append({'page':i+1,'chars':len(t),'start':t.replace('\n',' ')[:140]})
print(json.dumps(info,ensure_ascii=False,indent=2))
(root/'qa/page-report.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
d=pdfium.PdfDocument(str(root/'SceneDirector_기획자_매뉴얼.pdf'))
for i in range(len(d)):d[i].render(scale=1.5).to_pil().save(out/f'page-{i+1:02}.png')
for start in range(0,len(d),6):
 sheet=Image.new('RGB',(1260,1180),'#b5b5b5');draw=ImageDraw.Draw(sheet)
 for j in range(min(6,len(d)-start)):
  im=Image.open(out/f'page-{start+j+1:02}.png');im.thumbnail((410,570));x=(j%3)*420;y=(j//3)*590
  sheet.paste(im,(x,y+20));draw.text((x+5,y+3),str(start+j+1),fill='black')
 sheet.save(out/f'contact-{start+1:02}.png')
