import json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];folder=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'Saved/JumpAcquisition/Review05'
rows=json.loads((folder/'recording.json').read_text(encoding='utf8'))
lines=[]
for i,row in enumerate(rows):
 duration=1/30
 if i+1<len(rows):
  nxt=rows[i+1];dt=nxt['game']-row['game']
  duration=(nxt['t']-row['t']) if row['ui'] or nxt['ui'] or dt<=0 else dt
 duration=max(1/30,min(duration,.5))
 lines += ["file 'frame-%05d.png'"%i,'duration %.6f'%duration]
lines += ["file 'frame-%05d.png'"%(len(rows)-1)]
(folder/'frames.txt').write_text('\n'.join(lines),encoding='utf8')
ff=root/'Saved/VideoTools/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
subprocess.run([str(ff),'-y','-f','concat','-safe','0','-i',str(folder/'frames.txt'),'-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-r','30','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(folder/'JumpAcquisition_InGame.mp4')],check=True)
