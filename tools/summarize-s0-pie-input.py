import csv,json,statistics,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1];o=r/'Saved/S0WetFloor/PIEPerformance_20261020'
result=json.loads((o/'result.json').read_text());assert not result['error'],result['error'];assert result['map_unchanged']
session=json.loads((o/'session.json').read_text());assert hashlib.sha256((r/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap').read_bytes()).hexdigest()==session['map_sha256']
phases={}
for name in result['phases']:
 p=r/'Saved/S0WetFloor/SideFacets_20261018/User/Saved/Profiling/CSV'/('S0PIEPerformance_'+name+'.csv')
 records=[]
 with p.open(encoding='utf-8-sig',newline='') as f:
  for row in csv.DictReader(f):
   record={}
   for k in ['FrameTime','GPUTime','GameThreadTime','RenderThreadTime','RHI/DrawCalls']:
    try:record[k]=float(row[k])
    except (KeyError,ValueError,TypeError):pass
   if record.get('FrameTime',0)>0:records.append(record)
 assert len(records)>100
 fields={}
 for k in ['FrameTime','GPUTime','GameThreadTime','RenderThreadTime','RHI/DrawCalls']:
  v=[d[k] for d in records if d.get(k,0)>0]
  if v:fields[k]=dict(median=statistics.median(v),p95=sorted(v)[int((len(v)-1)*.95)],p99=sorted(v)[int((len(v)-1)*.99)],max=max(v))
 phases[name]=dict(samples=len(records),metrics=fields,slowest_rows=sorted(records,key=lambda x:x['FrameTime'],reverse=True)[:5],frames_over_33ms=sum(d['FrameTime']>33.33 for d in records),frames_over_50ms=sum(d['FrameTime']>50 for d in records))
samples=[x for x in result['samples'] if x['phase']=='walk']
travel=sum(sum((a-b)**2 for a,b in zip(x['pos'],y['pos']))**.5 for x,y in zip(samples,samples[1:]))
report=dict(scope=result['scope'],map_sha256=session['map_sha256'],walk_path_length_cm=travel,walk_ignored_samples=sum(x['ignored'] for x in samples),phases=phases)
(o/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
