import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'Bird/Tripo_v001'
bpy.ops.wm.open_mainfile(filepath=str(P/'tripo_pigeon_review.blend'))
pts=[o.matrix_world@v.co for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices]
out={}
for name,ps in [('all',pts),('center',[p for p in pts if abs(p.x)<.08]),('wing',[p for p in pts if abs(p.x)>.2])]:
 out[name]={'min':[min(p[i] for p in ps) for i in range(3)],'max':[max(p[i] for p in ps) for i in range(3)]}
(P/'coordinate_probe.json').write_text(json.dumps(out,indent=2))
