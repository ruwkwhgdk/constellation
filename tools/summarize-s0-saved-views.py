"""Summarize fresh V20 CSV samples, without claiming PIE/game FPS."""
import csv,json,statistics,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1];o=r/'Saved/S0WetFloor/SavedViews_20261019'
completed=json.loads((o/'completed.json').read_text())
assert completed['map_unchanged']
session=json.loads((o/'session.json').read_text())
assert hashlib.sha256((r/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap').read_bytes()).hexdigest()==session['map_sha256']
csvroot=r/'Saved/S0WetFloor/SideFacets_20261018/User/Saved/Profiling/CSV'
result={}
for phase in completed['phases']:
 p=csvroot/('S0SavedViews_'+phase+'.csv')
 values={k:[] for k in ['GPUTime','GPU/ShadowDepths','RHI/DrawCalls','FrameTime']}
 with p.open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  assert 'GPUTime' in reader.fieldnames,p
  for row in reader:
   for k in values:
    try:
     v=float(row[k])
     if v>0:values[k].append(v)
    except (ValueError,TypeError,KeyError):pass
 assert len(values['GPUTime'])>=100,(phase,len(values['GPUTime']))
 result[phase]={k:dict(median=statistics.median(v),p95=sorted(v)[int((len(v)-1)*.95)],samples=len(v)) for k,v in values.items() if v}
report=dict(map_sha256=session['map_sha256'],scope='saved map, fixed1600x900 editor GPU; not PIE or gameplay FPS',phases=result,main_repeat_drift_ms=abs(result['main']['GPUTime']['median']-result['main_repeat']['GPUTime']['median']))
(o/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
