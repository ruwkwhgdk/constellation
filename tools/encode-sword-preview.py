"""Encode real captured viewport frames, preserving recorded wall-clock timing."""
import json,subprocess,sys
from PIL import Image
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=Path(sys.argv[1]).resolve()
rows=json.loads((O/'recording.json').read_text(encoding='utf8'))
assert len(rows)>10,'No usable footage'
lines=[]
qte=[i for i,r in enumerate(rows) if r['ui']]
omit=set()
if qte and rows[qte[-1]]['t']-rows[qte[0]]['t']>10:
    omit={i for i in qte if rows[i]['t']-rows[qte[0]]['t']>3 and rows[qte[-1]]['t']-rows[i]['t']>2}
kept=[i for i in range(len(rows)) if i not in omit and (O/('frame-%05d.png'%i)).exists()]
sizes={i:Image.open(O/('frame-%05d.png'%i)).size for i in kept}
game_size=Counter(sizes.values()).most_common(1)[0][0]
other_window=[i for i in kept if sizes[i]!=game_size]
kept=[i for i in kept if i not in other_window]
for i in kept:
    row=rows[i]
    duration=max(.033,min(1.,rows[i+1]['t']-row['t'])) if i+1<len(rows) else .1
    lines += ["file 'frame-%05d.png'"%i,'duration %.6f'%duration]
lines += ["file 'frame-%05d.png'"%kept[-1]]
(O/'edit-notes.txt').write_text('Actual engine captures. Long QTE wait shortened; %d waiting frames omitted. No animation or item grant integration.\n'%len(omit),encoding='utf8')
with (O/'edit-notes.txt').open('a',encoding='utf8') as note:note.write('Startup editor-window captures excluded: '+str(other_window)+'\nQTE outcome injected in PIE; physical input and outcome retirement effects not tested.\n')
(O/'frames.txt').write_text('\n'.join(lines),encoding='utf8')
ff=R/'Saved/VideoTools/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
subprocess.run([str(ff),'-y','-f','concat','-safe','0','-i',str(O/'frames.txt'),'-vf',"pad=ceil(iw/2)*2:ceil(ih/2)*2,drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='ENGINE BLOCKOUT - ANIMATION / ITEM AWARD PENDING':x=16:y=16:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.7",'-r','30','-c:v','libx264','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(O/'SwordAcquisition_EngineBlockout.mp4')],check=True)
