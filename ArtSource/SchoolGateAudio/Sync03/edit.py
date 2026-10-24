import wave,json
import numpy as np
from pathlib import Path
P=Path(__file__).parent
source_path=P.parent/'0683.wav'
with wave.open(str(source_path)) as w:
 sr=w.getframerate();source=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
out=np.zeros(round(8.5*sr));pitch=2**(-8/12);edits=[]
for a,start,end,gain in [(2,.85,1.7,.85),(18.8,2,5.8,.9),(.35,5.8,8,.5)]:
 n=round((end-start)*sr);idx=a*sr+np.arange(n)*pitch
 cut=np.interp(idx,np.arange(len(source)),source)
 freq=np.fft.rfftfreq(n,1/sr);spectrum=np.fft.rfft(cut)
 # Suppress thin upper squeal while retaining the recorded low metal texture.
 spectrum*=1/np.sqrt(1+(freq/1100)**8)
 cut=np.fft.irfft(spectrum,n);fade=min(round(.12*sr),n//2)
 cut[:fade]*=np.linspace(0,1,fade);cut[-fade:]*=np.linspace(1,0,fade)
 out[round(start*sr):round(start*sr)+n]+=cut*gain
 edits.append({'source_start':a,'timeline':[start,end],'gain':gain})
assert abs(out).max()<1
with wave.open(str(P/'Gate_Low_8p5s.wav'),'wb') as w:
 w.setparams((1,2,sr,0,'NONE','not compressed'));w.writeframes((out*32767).astype('<i2').tobytes())
(P/'edit.json').write_text(json.dumps({'source':str(source_path),'license':'CC0','pitch_semitones':-8,'lowpass_hz':1100,'edits':edits,'peak':float(abs(out).max())},indent=2))
