"""Compare fresh saved-map snapshots; rejects changes outside the two outcrops."""
import json,re,sys
from pathlib import Path

def norm(x):
 return re.sub(r'0x[0-9A-Fa-f]+','PTR',json.dumps(x,sort_keys=True)).replace('-0.000000','0.000000')

def verify(before,after,changes,material,old_lights,new_lights):
 allowed={x['name']:x for x in changes}
 assert set(allowed)=={'StaticMeshActor_831','StaticMeshActor_833'}
 indexed={x['name']:x for x in after}
 assert len(indexed)==len(after)==len(before)
 for row in before:
  actual=indexed[row['name']];expected=json.loads(json.dumps(row))
  if row['name'] in allowed:
   change=allowed[row['name']]
   assert len(expected['meshes'])==1
   expected['transform']=change['new_transform']
   expected['meshes'][0]['mesh']=change['new_mesh']
   expected['meshes'][0]['materials'][0]=material
  assert norm(expected)==norm(actual),row['name']
 assert norm(old_lights)==norm(new_lights),'Lights changed'
 return dict(changed_actors=2,unchanged_actors=len(before)-2,lights_unchanged=True)

if __name__=='__main__':
 out=Path(sys.argv[1]);read=lambda n:json.loads((out/n).read_text(encoding='utf-8-sig'))
 report=verify(read('baseline-actors.json'),read('final-actors.json'),read('changes.json'),read('normal-preview.json')['material'],read('baseline-lights.json'),read('final-lights.json'))
 report['fresh_reload']=True
 (out/'verification.json').write_text(json.dumps(report,indent=2));print(report)
