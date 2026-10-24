import bpy,bmesh,json,math
from pathlib import Path
out=Path(bpy.data.filepath).parent
rows=[]
for obj in bpy.data.objects:
 if obj.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(obj.data)
 row=dict(name=obj.name,boundary_edges=sum(e.is_boundary for e in bm.edges),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),volume=bm.calc_volume(signed=True),uv_layers=len(obj.data.uv_layers),top=max(v.co.z for v in obj.data.vertices))
 bm.free()
 assert row['boundary_edges']==row['nonmanifold_edges']==0 and row['volume']>0 and row['uv_layers']>0
 assert all(math.isfinite(v) for p in obj.data.vertices for v in p.co)
 rows.append(row)
assert len(rows)==2
(out/'reopened-audit.json').write_text(json.dumps(rows,indent=2))

