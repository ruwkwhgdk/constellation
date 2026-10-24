"""Encode actual functional-review frames at their recorded timing."""
import json, subprocess, sys
from collections import Counter
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
rows = json.loads((out / 'recording.json').read_text(encoding='utf8'))
frames = {i: out / ('frame-%05d.png' % i) for i in range(len(rows))}
sizes = {i: Image.open(p).size for i, p in frames.items() if p.exists()}
size = Counter(sizes.values()).most_common(1)[0][0]
kept = [i for i in sizes if sizes[i] == size]
assert len(kept) > 10
lines = []
for i in kept:
    duration = max(.033, min(1., rows[i+1]['t'] - rows[i]['t'])) if i+1 < len(rows) else .1
    lines += ["file 'frame-%05d.png'" % i, 'duration %.6f' % duration]
lines += ["file 'frame-%05d.png'" % kept[-1]]
(out / 'frames.txt').write_text('\n'.join(lines), encoding='utf8')
(out / 'edit-notes.txt').write_text(
    'Actual engine viewport captures. Animation clips pending approval. '
    'Item presentation, dialogue, combat unlock and restored-input toast integrated. '
    'QTE outcome injected; physical swipe not tested. '
    'Different-sized startup captures excluded: %s\n' % [i for i in sizes if sizes[i] != size], encoding='utf8')
ffmpeg = root / 'Saved/VideoTools/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
subprocess.run([str(ffmpeg), '-y', '-f', 'concat', '-safe', '0', '-i', str(out / 'frames.txt'),
    '-vf', "pad=ceil(iw/2)*2:ceil(ih/2)*2,drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='FUNCTIONAL PREVIEW - ANIMATION PENDING':x=16:y=16:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.7",
    '-r', '30', '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    str(out / 'SwordAcquisition_FunctionalPreview.mp4')], check=True)
