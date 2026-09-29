import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'Heroine_Rebuild.fbx'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
rig=rigs[0]
report={'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'meshes':len(meshes),'bones':len(rig.data.bones),'unweighted':0,'bad_weight_sums':0,'over_four_weights':0,'nonfinite_vertices':0,'missing_uv':[],'missing_images':[],'skeleton_hierarchy_mismatch':[]}
report['material_slots']=sum(len(o.data.materials) for o in meshes)
for o in meshes:
    if not o.data.uv_layers:report['missing_uv'].append(o.name)
    for v in o.data.vertices:
        weights=[g.weight for g in v.groups if g.weight>1e-6]
        report['unweighted']+=not bool(weights)
        report['bad_weight_sums']+=abs(sum(weights)-1)>.002
        report['over_four_weights']+=len(weights)>4
        report['nonfinite_vertices']+=not all(math.isfinite(c) for c in v.co)
for i in bpy.data.images:
    if i.source=='FILE' and i.size[0]==0:report['missing_images'].append(i.filepath)
src=json.loads((ROOT/'reference/source_audit.json').read_text())
for b in src['bones']:
    actual=rig.data.bones.get(b['name'])
    if not actual or (actual.parent.name if actual.parent else None)!=b['parent']:report['skeleton_hierarchy_mismatch'].append(b['name'])
report['max_rest_bone_head_error_m']=max(((rig.matrix_world@rig.data.bones[b['name']].head_local)-Vector(b['head'])).length for b in src['bones'])
deps=bpy.context.evaluated_depsgraph_get()
def bounds():
    pts=[o.evaluated_get(deps).matrix_world@Vector(c) for o in meshes for c in o.evaluated_get(deps).bound_box]
    return [[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)]
report['rest_bounds']=bounds()
for name,angle in [('mixamorig:LeftArm',68),('mixamorig:RightArm',-68)]:
    p=rig.pose.bones[name];p.rotation_mode='QUATERNION'
    axis=(rig.matrix_world@p.bone.matrix_local).to_quaternion().inverted()@Vector((0,1,0))
    p.rotation_quaternion=Quaternion(axis,math.radians(angle))
bpy.context.view_layer.update();report['posed_bounds']=bounds()
report['checks_pass']=65000<=report['triangles']<=75000 and report['max_rest_bone_head_error_m']<.0001 and all(report[k]==0 for k in ['unweighted','bad_weight_sums','over_four_weights','nonfinite_vertices']) and not any(report[k] for k in ['missing_uv','missing_images','skeleton_hierarchy_mismatch'])
(ROOT/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
