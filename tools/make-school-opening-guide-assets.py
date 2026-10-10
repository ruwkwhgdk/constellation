"""Deterministic S0 graphic cards and guide audio. No final voice performance."""
from pathlib import Path
from PIL import Image,ImageDraw
import math,wave,struct,random
out=Path(__file__).resolve().parents[1]/'ArtSource/SchoolOpening';out.mkdir(exist_ok=True)
im=Image.new('RGB',(512,640),'#182443');d=ImageDraw.Draw(im)
r=random.Random(5)
for i in range(100):
 x,y=r.randrange(512),r.randrange(640);d.ellipse((x,y,x+2,y+2),fill='#8aa4c0')
points=[(95,470),(170,360),(240,315),(295,220),(380,135),(325,435),(380,535)]
d.line(points[:5],fill='#97b4d3',width=2);d.line([points[2],points[5],points[6]],fill='#97b4d3',width=2)
for x,y in points:d.ellipse((x-5,y-5,x+5,y+5),fill='#fff0b9');d.line((x-11,y,x+11,y),fill='#fff0b9',width=1);d.line((x,y-11,x,y+11),fill='#fff0b9',width=1)
d.rectangle((20,20,490,620),outline='#d0b885',width=2);im.save(out/'Card_Constellation.png')
im=Image.new('RGB',(256,256),'#e8cd88');d=ImageDraw.Draw(im)
for y,w in [(60,155),(86,178),(112,120),(175,90)]:d.line((30,y,w,y-3),fill='#777073',width=3)
d.polygon([(194,167),(200,182),(216,184),(204,194),(207,210),(194,201),(180,210),(184,194),(171,184),(188,182)],fill='#b97891');im.save(out/'Note_Stars.png')
sr=22050
notes=[(60,1),(60,1),(67,1),(67,1),(69,1),(69,1),(67,2),(65,1),(65,1),(64,1),(64,1),(62,1),(62,1),(60,2)]
def save(name,seq):
 with wave.open(str(out/name),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes(b''.join(struct.pack('<h',int(max(-.98,min(.98,x))*32767)) for x in seq))
samples=[]
for midi,beat in notes:
 dur=beat*.45;freq=440*2**((midi-69)/12)
 for i in range(int(dur*sr)):
  t=i/sr;env=min(1,t/.03)*min(1,(dur-t)/.1);samples.append(.2*env*(math.sin(2*math.pi*freq*t)+.2*math.sin(4*math.pi*freq*t)))
save('Guide_Twinkle_Melody.wav',samples)
save('Guide_Door_Creak.wav',[.17*math.exp(-i/sr*2)*(math.sin(2*math.pi*(280+90*math.sin(i/sr*11))*i/sr)+.25*r.uniform(-1,1)) for i in range(int(sr*1.1))])
save('Guide_Fall_Thud.wav',[.45*math.exp(-i/sr*8)*(math.sin(2*math.pi*65*i/sr)+.4*r.uniform(-1,1)) for i in range(int(sr*.7))])
