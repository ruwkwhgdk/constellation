import bpy,json,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parent
out={};fingerprints={}
for label,path in [('before',P.parent/'RigContourFix/Delivery/Heroine_GameSkeleton.blend'),('after',P/'Delivery/Heroine_GameSkeleton.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];rig=bpy.data.objects['Heroine_GameSkeleton']
 pts=np.array([list(o.matrix_world@v.co) for o in meshes for v in o.data.vertices]);head=pts[pts[:,2]>1.37]
 out[label]={'height_cm':float(np.ptp(pts[:,2])*100),'head_width_cm':float(np.ptp(head[:,1])*100),'head_depth_cm':float(np.ptp(head[:,0])*100),'shoulder_height_cm':rig.data.bones['upperarm_l'].head_local.z*100,'shoulder_joint_span_cm':abs(rig.data.bones['upperarm_l'].head_local.y-rig.data.bones['upperarm_r'].head_local.y)*100}
 fingerprints[label]={o.name:{'uv':hashlib.sha256(np.array([list(l.uv) for l in o.data.uv_layers.active.data],dtype=np.float32).tobytes()).hexdigest(),'topology':hashlib.sha256(str([list(p.vertices) for p in o.data.polygons]).encode()).hexdigest(),'materials':[m.name for m in o.data.materials]} for o in meshes}
 out[label]['textures']={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}
out['uv_topology_materials_identical']=fingerprints['before']==fingerprints['after']
out['original_textures_preserved']=all(out['after']['textures'].get(k)==v for k,v in out['before']['textures'].items())
out['reference_head_width_cm']=25.4281140864
out['reference_shoulder_height_cm']=(.5687381029129028+.9507081508636475)*1.6/1.899063289165497*100
out['pass']=out['uv_topology_materials_identical'] and out['original_textures_preserved'] and abs(out['after']['height_cm']-160)<.01 and abs(out['after']['head_width_cm']-out['reference_head_width_cm'])<.5 and abs(out['after']['shoulder_height_cm']-out['reference_shoulder_height_cm'])<.5
(P/'revision_audit.json').write_text(json.dumps(out,indent=2));assert out['pass'],out
