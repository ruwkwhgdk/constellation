from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parent
paths=[P/'frames'/f'{i:03}.png' for i in range(1,41,2)]
assert all(p.exists() for p in paths)
images=[Image.open(p).convert('RGB') for p in paths]
palette=images[0].quantize(colors=192)
frames=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in images]
durations=[60,70,70]*6+[60,70]
frames[0].save(P/'Walk_Timid_Preview.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False,disposal=2)
sheet=Image.new('RGB',(480*4,600*2),(35,35,35))
for j,i in enumerate([0,2,5,7,10,12,15,17]):sheet.paste(images[i],((j%4)*480,(j//4)*600))
sheet.save(P/'Walk_Timid_KeyPoses.jpg',quality=93)
print('GIF and key-pose sheet encoded')
