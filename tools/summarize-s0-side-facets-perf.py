import csv,json,statistics
from pathlib import Path
r=Path(__file__).resolve().parents[1];o=r/'Saved/S0WetFloor/SideFacetsPerfRetry_20261018'
result={}
for p in sorted((o/'User/Saved/Profiling/CSV').glob('S0SideFacets_*.csv')):
 with p.open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f);values={k:[] for k in ['GPUTime','GPU/ShadowDepths','RHI/DrawCalls','FrameTime']}
  for row in reader:
   for k in values:
    try:
     v=float(row[k])
     if v>0:values[k].append(v)
    except (ValueError,TypeError,KeyError):pass
 result[p.stem]={k:dict(median=statistics.median(v),samples=len(v)) for k,v in values.items() if v}
assert len(result)==3 and all('GPUTime' in v for v in result.values()),result
(o/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

