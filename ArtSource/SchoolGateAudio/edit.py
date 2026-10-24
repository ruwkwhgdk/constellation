import wave,json
import numpy as np
from pathlib import Path
P=Path(__file__).parent
with wave.open(str(P/'0683.wav')) as w:
 sr=w.getframerate();source=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
out=np.zeros(round(8.5*sr));edits=[]
for a,b,start,end,gain in [(2,3.4,.85,2.35,.65),(18.8,21.9,2.9,6.1,.60),(.35,1.25,6.1,7.7,.22)]:
 cut=source[round(a*sr):round(b*sr)];count=round((end-start)*sr);cut=np.interp(np.linspace(0,len(cut)-1,count),np.arange(len(cut)),cut)
 fade=min(round(.08*sr),count//2);cut[:fade]*=np.linspace(0,1,fade);cut[-fade:]*=np.linspace(1,0,fade)
 out[round(start*sr):round(start*sr)+count]+=cut*gain;edits.append({'source_seconds':[a,b],'timeline_seconds':[start,end],'gain':gain})
assert abs(out).max()<1
with wave.open(str(P/'Gate_Recorded_8p5s.wav'),'wb') as w:
 w.setparams((1,2,sr,0,'NONE','not compressed'));w.writeframes((out*32767).astype('<i2').tobytes())
(P/'edit.json').write_text(json.dumps({'source':'0683.wav','license':'CC0','url':'https://bigsoundbank.com/grinding-metal-gate-s0683.html','author':'Joseph Sardin','edits':edits,'peak':float(abs(out).max())},indent=2))
