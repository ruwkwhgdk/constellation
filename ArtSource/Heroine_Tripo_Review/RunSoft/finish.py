from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parent
frames=[Image.open(P/'frames'/f'{i:03}.png').convert('RGB') for i in range(1,31)]
palette=frames[0].quantize(colors=192)
gif=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
gif[0].save(P/'Run_Soft_Preview.gif',save_all=True,append_images=gif[1:],duration=[30,30,40]*10,loop=0,disposal=2,optimize=False)
sheet=Image.new('RGB',(480*4,600*2))
for j,i in enumerate([0,4,8,12,15,19,23,27]):sheet.paste(frames[i],((j%4)*480,(j//4)*600))
sheet.save(P/'Run_Soft_KeyPoses.jpg',quality=93)
print('Preview encoded: 30 frames, 1.0 second')
