import wave
from pathlib import Path
import numpy as np
P=Path(__file__).parent
with wave.open(str(P/'Firefly_Original.wav')) as w:
 sr=w.getframerate();channels=w.getnchannels();source=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,channels).astype(float)/32768
edited=source.copy();a=round(.02*sr);b=round(.12*sr)
edited[:a]*=np.linspace(0,1,a)[:,None];edited[-b:]*=np.linspace(1,0,b)[:,None]
out=np.zeros((round(8.5*sr),channels));start=round(.85*sr);out[start:start+len(edited)]=edited
with wave.open(str(P/'Gate_Firefly_Timed.wav'),'wb') as w:
 w.setparams((channels,2,sr,0,'NONE','not compressed'));w.writeframes((out*32767).astype('<i2').tobytes())
