"""Encode real engine joint render targets in authored clip order at half speed."""
from pathlib import Path
from PIL import Image,ImageDraw
import subprocess,sys,json
p=Path(sys.argv[1]);source=p/'JointReview';ff=Path(__file__).resolve().parents[1]/'Saved/VideoTools/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
order=['Approach','BraceLoop','ExtractRecover','ReleaseLeft','Raise','RaisedHoldLoop','Lower'];names=[]
for clip in order:names += sorted(source.glob(clip+'-*-hands.png'))
assert names
output=p/'SwordArm_CloseReview_HalfSpeed.mp4'
cmd=[str(ff),'-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1024x1080','-framerate','5','-i','-','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for f in names:
 stem=f.stem.rsplit('-',1)[0];canvas=Image.new('RGB',(1024,1080),(20,20,20));draw=ImageDraw.Draw(canvas)
 for j,view in enumerate(['hands','outer','front','side']):
  im=Image.open(source/(stem+'-'+view+'.png')).convert('RGB').resize((512,512));x=j%2*512;y=j//2*540;canvas.paste(im,(x,y));draw.text((x+8,y+516),stem+' | '+view,fill='white')
 proc.stdin.write(canvas.tobytes())
proc.stdin.close();assert proc.wait()==0
subprocess.run([str(ff),'-v','error','-i',str(output),'-f','null','-'],check=True)
(p/'joint-video-validation.json').write_text(json.dumps({'frames':len(names),'duration_seconds':len(names)/5,'speed':0.5,'sampling_game_seconds':0.1,'views':4,'decode':'passed','loop_policy':'one unique cycle per clip; not full event playback'},indent=2));print(output)
