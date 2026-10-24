import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(P/'SKM_Slime_Liquid.fbx'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
source=json.loads((P.parent/'Production/revision-10.json').read_text())
out={'armature':rig.name,'world_scale':list(rig.scale),'bones':len(rig.data.bones),'frames':[]}
for frame in range(2,99):
 bpy.context.scene.frame_set(frame)
 p=rig.matrix_world@rig.pose.bones['drop'].matrix.translation
 # FBX importer converts delivery centimeters to world meters.
 out['frames'].append({'frame':frame,'drop_world':list(p)})
out['root_world']=list(rig.matrix_world@rig.data.bones['Root'].head_local)
assert len(rig.data.bones)==14
assert abs(out['root_world'][2]+.843279)<.0001
for frame in [2,26,50,74,80,88,94,98]:
 bpy.context.scene.frame_set(frame)
 dg=bpy.context.evaluated_depsgraph_get()
 for obj in bpy.context.scene.objects:
  if obj.type!='MESH':continue
  ev=obj.evaluated_get(dg);me=ev.to_mesh()
  points=[ev.matrix_world@v.co for v in me.vertices]
  assert max(p.length for p in points)<3,(frame,obj.name)
  ev.to_mesh_clear()
out['passed']=True
(P/'delivery-verification.json').write_text(json.dumps(out,indent=2))
