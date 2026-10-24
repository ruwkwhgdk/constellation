"""Deterministic original S0 sound-design drafts, 48kHz mono PCM."""
import math,random,wave,struct
from pathlib import Path
O=Path(__file__).resolve().parents[1]/'ArtSource/SchoolOpening/Audio';O.mkdir(exist_ok=True)
sr=48000;r=random.Random(1510)
def save(name,s):
 peak=max(abs(x) for x in s) or 1;gain=min(1,.85/peak)
 with wave.open(str(O/(name+'.wav')),'wb') as f:
  f.setparams((1,2,sr,0,'NONE','not compressed'));f.writeframes(b''.join(struct.pack('<h',round(x*gain*32767)) for x in s))
def impact(t,freq,decay,level):return level*math.exp(-decay*t)*math.sin(2*math.pi*freq*t) if t>=0 else 0
save('S_UI_DialogueTick',[.12*math.exp(-t*130)*(math.sin(2*math.pi*920*t)+.25*r.uniform(-1,1))*min(1,t/.002) for t in [i/sr for i in range(int(.045*sr))]])
door=[]
for i in range(int(1.8*sr)):
 t=i/sr
 x=sum(impact(t-start,freq,decay,amp) for start in [0,.085,.21] for freq,decay,amp in [(177,16,.23),(563,10,.1),(1237,19,.055),(2111,23,.03)])
 x+=sum(.16*math.exp(-(t-st)*80)*r.uniform(-1,1) if t>=st else 0 for st in [0,.085,.21])
 if .24<t<1.45:
  q=t-.24;env=min(1,q/.06)*min(1,(1.45-t)/.2)
  x+=env*(.035*math.sin(2*math.pi*(740*q+18*math.sin(q*11)))+.024*r.uniform(-1,1))
 x+=impact(t-1.46,210,12,.23)+impact(t-1.46,677,15,.07)
 door.append(x)
save('S_Locker_MetalOpen',door)
steps=[]
for i in range(int(1.7*sr)):
 t=i/sr;x=0
 for k,st in enumerate([0,.23,.46,.69,.92,1.15,1.38]):
  q=t-st
  if 0<=q<.2:x+=impact(q,100+k%2*17,32,.32)+.12*math.exp(-q*65)*r.uniform(-1,1)
 steps.append(x)
save('S_Girl_RunApproach',steps)
print(str(O))
