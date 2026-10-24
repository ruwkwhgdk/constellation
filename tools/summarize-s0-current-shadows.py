"""Summarize fresh V20 CSV samples, without claiming PIE/game FPS."""
import csv,json,statistics,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1];o=r/'Saved/S0WetFloor/ShadowV20_20261019'
completed=json.loads((o/'completed.json').read_text())
assert completed['map_unchanged']
session=json.loads((o/'session.json').read_text())
assert hashlib.sha256((r/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap').read_bytes()).hexdigest()==session['map_sha256']
csvroot=r/'Saved/S0WetFloor/SideFacets_20261018/User/Saved/Profiling/CSV'
result={}
for phase in completed['phases']:
 p=csvroot/('S0V20Shadow_'+phase+'.csv')
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
base=statistics.mean(result[k]['GPUTime']['median'] for k in ['baseline','baseline_repeat'])
report=dict(map_sha256=session['map_sha256'],scope='fixed1600x900 editor GPU; not PIE or gameplay FPS',phases=result,baseline_mean_ms=base,baseline_drift_ms=abs(result['baseline']['GPUTime']['median']-result['baseline_repeat']['GPUTime']['median']),gpu_reduction_ms={k:base-result[k]['GPUTime']['median'] for k in [p for p in completed['phases'] if p not in ['baseline','baseline_repeat']]})
(o/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

