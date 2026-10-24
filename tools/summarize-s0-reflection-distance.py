import csv,json,statistics,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1];o=r/'Saved/S0WetFloor/ReflectionDistance_20261020'
session=json.loads((o/'session.json').read_text());done=json.loads((o/'completed.json').read_text())
assert done['map_unchanged']
assert hashlib.sha256((r/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap').read_bytes()).hexdigest()==session['map_sha256']
result={}
for name in done['phases']:
 p=r/'Saved/S0WetFloor/SideFacets_20261018/User/Saved/Profiling/CSV'/('S0ReflectionDistance_'+name+'.csv')
 values={k:[] for k in ['GPUTime','FrameTime','GPU/ShadowDepths','RHI/DrawCalls','GameThreadTime','RenderThreadTime']}
 with p.open(encoding='utf-8-sig',newline='') as f:
  rows=csv.DictReader(f)
  for row in rows:
   for k in values:
    try:
     v=float(row[k])
     if v>0:values[k].append(v)
    except (KeyError,ValueError,TypeError):pass
 assert len(values['GPUTime'])>100
 result[name]={k:dict(median=statistics.median(v),p95=sorted(v)[int((len(v)-1)*.95)],p99=sorted(v)[int((len(v)-1)*.99)],maximum=max(v),samples=len(v)) for k,v in values.items() if v}
report=dict(scope='1600x900 fixed editor camera, distance-only A/B/C/A test; not PIE or gameplay FPS.',map_sha256=session['map_sha256'],phases=result)
(o/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

