from PIL import Image
from pathlib import Path
P=Path(__file__).resolve().parent
frames=[Image.open(P/'frames'/f'{f:03}.png').convert('RGB') for f in range(1,61,2)]
pal=frames[0].quantize(colors=224);gif=[i.quantize(palette=pal,dither=Image.Dither.NONE) for i in frames]
gif[0].save(P/'Attack01_Preview.gif',save_all=True,append_images=gif[1:],duration=[30,30,40]*10,loop=0,disposal=2,optimize=False)
sheet=Image.new('RGB',(1600,800))
for j,i in enumerate([0,4,8,12,15,19,24,29]):sheet.paste(frames[i].resize((400,400)),((j%4)*400,(j//4)*400))
sheet.save(P/'Attack01_KeyPoses.jpg',quality=95)
