"""Package captured PIE frames at their recorded game times, without synthesizing motion."""
from pathlib import Path
import json
from PIL import Image
root=Path(__file__).resolve().parents[1]
folder=root/'Saved/CarryReview'
report=json.loads((folder/'play-verification.json').read_text(encoding='utf-8'))
assert 'error' not in report and all(x['passed'] for x in report['checks']),report.get('error')
frames=[]; times=[]
for path in sorted((folder/'play-frames').glob('frame-*.png')):
    number=int(path.stem.split('-')[1])
    frames.append(Image.open(path).convert('RGB').resize((768,432),Image.Resampling.LANCZOS))
    times.append(report['frame_times'][number-1])
assert len(frames)>20
durations=[max(20,round((times[i+1]-times[i])*1000)) for i in range(len(times)-1)]+[500]
frames[0].save(folder/'carry-play-review.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False)
print(json.dumps({'frames':len(frames),'duration_seconds':sum(durations)/1000,'gif':str(folder/'carry-play-review.gif')}))
