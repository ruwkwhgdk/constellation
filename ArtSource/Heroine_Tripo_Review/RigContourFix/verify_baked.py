import bpy,json,math
from pathlib import Path
from mathutils import Matrix
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parent;R=Matrix.Rotation(math.pi/2,4,'Z')
bpy.ops.wm.open_mainfile(filepath=str(P/'Delivery/Heroine_AnimationRig.blend'))
r=bpy.data.objects['Heroine_AnimationRig'];r.animation_data.action=bpy.data.actions['QA_squat'];bpy.context.scene.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();trees={}
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.name.startswith('WGT-'):continue
 ev=o.evaluated_get(dg);m=ev.to_mesh();k=KDTree(len(m.vertices))
 for v in m.vertices:k.insert(R@ev.matrix_world@v.co,v.index)
 k.balance();trees[o.name+'_Game']=k;ev.to_mesh_clear()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(P/'QA_squat_baked.fbx'));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();result={}
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(dg);m=ev.to_mesh();k=trees[o.name];result[o.name]=max(k.find(ev.matrix_world@v.co)[2] for v in m.vertices);ev.to_mesh_clear()
report={'baked_pose_roundtrip_max_m':result,'pass':max(result.values())<1e-4}
(P/'Delivery/baked_pose_validation.json').write_text(json.dumps(report,indent=2));print(report)
