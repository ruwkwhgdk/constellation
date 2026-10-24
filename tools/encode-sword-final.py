"""Encode background fixed-step engine captures without presentation mockups."""
import json,subprocess,sys
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]).resolve()
rows=json.loads((out/'recording.json').read_text(encoding='utf8'))
result=json.loads((out/'result.json').read_text(encoding='utf8'))
assert result['error'] is None,result
files=[out/('frame-%05d.png'%i) for i in range(len(rows))]
omitted=[]
if not files[-1].exists():
 omitted=[len(rows)-1];files=files[:-1];rows=rows[:-1]
assert all(p.exists() for p in files),'Missing interior capture frame'
startup_trim=0
bad=[i for i,p in enumerate(files) if Image.open(p).size!=(1286,760)]
if bad:
 assert max(bad)<5,bad
 startup_trim=max(bad)+1;files=files[startup_trim:];rows=rows[startup_trim:]
assert all(Image.open(p).size==(1286,760) for p in files)
steps=[b['t']-a['t'] for a,b in zip(rows,rows[1:])]
assert max(abs(d-1/30) for d in steps)<.002,(min(steps),max(steps))
ff=root/'Saved/VideoTools/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
video=out/'SwordAcquisition_FinalEnginePreview.mp4'
subprocess.run([str(ff),'-y','-framerate','30','-start_number',str(startup_trim),'-i',str(out/'frame-%05d.png'),'-frames:v',str(len(rows)),'-vf','crop=1280:720:3:35','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
subprocess.run([str(ff),'-v','error','-i',str(video),'-f','null','-'],check=True)
(out/'video-validation.json').write_text(json.dumps({'frames':len(rows),'duration_seconds':len(rows)/30,'game_time_step_min':min(steps),'game_time_step_max':max(steps),'decode':'passed','qte':'engine outcome injection','audio':'not captured','omitted_terminal_request':omitted,'startup_frames_trimmed':startup_trim},indent=2))
print(video)
