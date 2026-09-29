"""Continuous center separation for the v019 piecewise-linear Sequencer paths."""
import json,math
from pathlib import Path
folder=Path(__file__).resolve().parents[1]/'TripoReplacement/v019/Flock'
data=json.loads((folder/'routes.json').read_text());best=float('inf');pair=None
for i,a in enumerate(data['birds']):
    for b in data['birds'][i+1:]:
        for k in range(len(a['samples'])-1):
            r=[x-y for x,y in zip(a['samples'][k]['position_cm'],b['samples'][k]['position_cm'])]
            next_r=[x-y for x,y in zip(a['samples'][k+1]['position_cm'],b['samples'][k+1]['position_cm'])]
            v=[x-y for x,y in zip(next_r,r)];vv=sum(x*x for x in v)
            t=max(0,min(1,-sum(x*y for x,y in zip(r,v))/vv)) if vv else 0
            distance=math.sqrt(sum((x+t*y)**2 for x,y in zip(r,v)))
            if distance<best:best=distance;pair=[a['name'],b['name'],k*8+t*8]
assert best>15
result=dict(continuous_linear_center_min_cm=best,pair_and_frame=pair,wing_collision_checked=False,gameplay=False)
(folder/'continuous_spacing.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
