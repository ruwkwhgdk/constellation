import bpy,bmesh,json,collections
from pathlib import Path
R=Path(__file__).resolve().parent;out={}
for name,path,obj in [('Refined','Refined/Heroine_Refined.blend','Heroine_Refined'),('BoundaryLocal','BoundaryLocal/Heroine_BoundaryLocal.blend','Heroine_BoundaryLocal'),('ContourRepair','ContourRepair/Delivery/Heroine_ContourRepair.blend','Heroine_ContourRepair'),('Neutral','NeutralExpression/Heroine_NeutralExpression.blend','Heroine_NeutralExpression')]:
 bpy.ops.wm.open_mainfile(filepath=str(R/path));ob=bpy.data.objects[obj];bm=bmesh.new();bm.from_mesh(ob.data);counts=collections.Counter();locations=[]
 for e in bm.edges:
  if len(e.link_faces)>2:
   c=(e.verts[0].co+e.verts[1].co)/2;region='head' if c.z>.82 else ('arms' if abs(c.x)>.15 and c.z>.7 else ('torso' if c.z>.5 else ('skirt/thigh' if c.z>.35 else 'legs/shoes')))
   counts[region]+=1;locations.append([*c,len(e.link_faces)])
 out[name]={'edges_more_than_two_faces':sum(counts.values()),'regions':dict(counts),'loose_edges':sum(not e.link_faces for e in bm.edges),'boundary_edges':sum(e.is_boundary for e in bm.edges),'locations':locations};bm.free()
(R/'NeutralInspection/topology_history.json').write_text(json.dumps(out,indent=2));print(json.dumps({n:{k:v for k,v in x.items() if k!='locations'} for n,x in out.items()},indent=2))
