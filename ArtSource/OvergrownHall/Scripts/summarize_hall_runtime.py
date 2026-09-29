"""Matched editor-capture comparison. This is not a gameplay FPS benchmark."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
source=(ROOT/'ArtSource/OvergrownHall/Scripts/summarize_hall_profile.py').read_text().replace('TripoReplacement/v013','TripoReplacement/v014').replace('Hall_v013.csv','Hall_v014.csv')
source=source.replace('No before/after performance baseline.','See performance_comparison.json for the qualified v013 comparison.')
exec(compile(source,'runtime_profile','exec'),globals())
out=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v014'
before=json.loads((out.parent/'v013/performance.json').read_text());after=json.loads((out/'performance.json').read_text())
comparison={}
for key in ['GPUTime','FrameTime','RHI/DrawCalls','RHI/PrimitivesDrawn','DrawCall/ShadowDepths']:
    a=before['metrics'][key]['median'];b=after['metrics'][key]['median'];comparison[key]=dict(before=a,after=b,change_percent=(b/a-1)*100)
(out/'performance_comparison.json').write_text(json.dumps(dict(before='v013',after='v014',metrics=comparison,note='Same reference-camera editor capture script and window request; separate runs, not gameplay, actual viewport resolution can differ from requested window dimensions.'),indent=2));print(json.dumps(comparison,indent=2))
