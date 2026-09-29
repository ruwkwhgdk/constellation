import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(P/'Reference_Sword.fbx'))
report=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 co=[o.matrix_world@v.co for v in o.data.vertices]
 report.append({'name':o.name,'min':[min(v[k] for v in co) for k in range(3)],'max':[max(v[k] for v in co) for k in range(3)],'bands':[{'z':z,'width':max([v.x for v in co if abs(v.z-z)<.04],default=0)-min([v.x for v in co if abs(v.z-z)<.04],default=0)} for z in [-.9,-.7,-.5,-.3,0,.3,.5,.7,.9]]})
(P/'sword_geometry.json').write_text(json.dumps(report,indent=2));print(report)
