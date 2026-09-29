import bpy,bmesh,json
from pathlib import Path
R=Path(__file__).resolve().parent;O=R/'DetailFinish2';bpy.ops.wm.open_mainfile(filepath=str(O/'geometry_stage.blend'));me=bpy.data.objects['Heroine_DetailFinish2'].data;bm=bmesh.new();bm.from_mesh(me);out=[]
for e in bm.edges:
 c=(e.verts[0].co+e.verts[1].co)/2
 if abs(abs(c.x)-.0405)<.006 and .598<c.z<.615 and c.y<-.055:out.append({'v':[v.index for v in e.verts],'points':[list(v.co) for v in e.verts],'faces':len(e.link_faces),'length':e.calc_length()})
(O/'pocket_edges.json').write_text(json.dumps(out,indent=2));print('POCKET_EDGES',len(out),'BOUNDARY',sum(e['faces']==1 for e in out),flush=True)
