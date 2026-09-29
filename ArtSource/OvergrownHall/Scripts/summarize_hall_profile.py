"""Summarize actual rendered editor frames; never report idle frames as game performance."""
import csv,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v013'
source=ROOT/'Saved/Profiling/CSV/Hall_v013.csv'
with source.open() as f:rows=list(csv.DictReader(f))
active=[]
for row in rows:
    try:
        # CSV footer/event tables can contain numeric values in some columns.
        if float(row.get('DrawCall/Basepass') or 0)>0 and float(row.get('FrameTime') or 0)>0 and float(row.get('GPUTime') or 0)>0:active.append(row)
    except ValueError:pass
assert len(active)>100,'Insufficient actual scene rendering; discard idle-editor results'
keys=['FrameTime','RHI/DrawCalls','RHI/PrimitivesDrawn','DrawCall/Basepass','DrawCall/Translucency','DrawCall/ShadowDepths','GPUTime','GameThreadTime','GPUMem/LocalUsedMB']
metrics={}
for key in keys:
    values=[]
    for row in active:
        try: values.append(float(row[key]))
        except (ValueError,TypeError,KeyError): pass
    values.sort()
    metrics[key]=dict(median=statistics.median(values),p95=values[int((len(values)-1)*.95)]) if values else None
report=dict(active_frames=len(active),metrics=metrics,context='Editor fixed-camera forced redraw, not PIE or packaged gameplay. Window requested 1200x640; viewport size can differ. Startup/high-res screenshot work excluded. No before/after performance baseline.',source=str(source.relative_to(ROOT)))
(OUT/'performance.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
