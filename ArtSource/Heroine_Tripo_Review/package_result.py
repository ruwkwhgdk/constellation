from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import zipfile
root=Path(__file__).resolve().parent
out=root/'Corrected'
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',24)
for name,before,after in [('face_comparison',out/'renders/face_before.png',out/'renders/face.png'),('front_comparison',root/'renders/front.png',out/'renders/front.png')]:
    images=[Image.open(p).convert('RGB') for p in [before,after]]
    width=600;height=round(images[0].height*width/images[0].width)
    sheet=Image.new('RGB',(width*2,height+60),(32,32,35))
    draw=ImageDraw.Draw(sheet)
    for i,(im,label) in enumerate(zip(images,['Tripo 원본','원화 참고 · 1차 보정'])):
        sheet.paste(im.resize((width,height),Image.Resampling.LANCZOS),(i*width,60))
        draw.text((i*width+22,15),label,font=font,fill=(240,240,240))
    sheet.save(out/'renders'/f'{name}.png')
archive=root/'Heroine_Tripo_Corrected_Package.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.suffix not in ['.blend1']:
            z.write(p,p.relative_to(out))
print(archive)
print('Package bytes:',archive.stat().st_size)
