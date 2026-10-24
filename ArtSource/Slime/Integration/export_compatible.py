"""Export a gameplay-bind-compatible copy; never modify the maintained source."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parent
src=bpy.data.objects['Slime_Liquid_Rig']
names=['Slime_Body','Slime_Droplet','Slime_InnerGel','Eye_L','Eye_R']
meshes=[bpy.data.objects[x] for x in names]
rename={'root':'Root','center':'Center','top':'Top'}
rest={b.name:b.matrix_local.copy() for b in src.data.bones}
parents={b.name:b.parent.name if b.parent else None for b in src.data.bones}
poses={}
for f in range(1,98):
 bpy.context.scene.frame_set(f)
 poses[f]={b.name:b.matrix.copy() for b in src.pose.bones}
offset=Vector((-.0004504776,.001236,-.84327904))
T=Matrix.Translation(offset)
# The droplet rests inside the crest in gameplay clips without a droplet track.
G=Matrix.Translation(Vector((.21,-.13,1.46)))@Matrix.Scale(.35,4)@Matrix.Translation(-rest['drop'].translation)
data=bpy.data.armatures.new('Slime_Gameplay_Skeleton')
rig=bpy.data.objects.new('Armature',data);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for n in rest:
 b=data.edit_bones.new(rename.get(n,n))
 if n in rename:
  z={'root':0,'center':.478177604675293,'top':1.530338134765625}[n]
  b.head=offset+Vector((0,0,z));b.tail=b.head+Vector((0,.1,0))
 else:
  b.matrix=T@rest[n];b.length=.1
  if n=='drop':b.matrix=T@G@rest[n]
 pn=parents[n]
 if n=='top':pn='root'
 if pn:b.parent=data.edit_bones[rename.get(pn,pn)]
bpy.ops.object.mode_set(mode='OBJECT')
for obj in meshes:
 for polygon in obj.data.polygons:polygon.use_smooth=True
 world=obj.matrix_world.copy()
 obj.parent=None;obj.matrix_world=Matrix.Identity(4)
 geom=T@G if obj.name=='Slime_Droplet' else T
 for v in obj.data.vertices:v.co=geom@world@v.co
 for old,new in rename.items():
  group=obj.vertex_groups.get(old)
  if group:group.name=new
 for mod in obj.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 obj.parent=rig
# Vertex attributes for the engine's gel shading; preserve mesh geometry/UV0.
for obj in meshes:
 attr=obj.data.color_attributes.get('GelDensity') or obj.data.color_attributes.new(name='GelDensity',type='FLOAT_COLOR',domain='POINT')
 for v,d in zip(obj.data.vertices,attr.data):
  p=v.co-offset
  d.color=(max(0,min(1,p.z/1.67)),0,0,1)
rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new('AS_Slime_Liquid_Idle')
error=0
for f,ps in poses.items():
 bpy.context.scene.frame_set(f)
 for n in rest:
  pb=rig.pose.bones[rename.get(n,n)];pb.rotation_mode='QUATERNION'
  geom=T@G if n=='drop' else T
  target=T@ps[n]@rest[n].inverted()@geom.inverted()@pb.bone.matrix_local
  pb.matrix=target
  bpy.context.view_layer.update()
  for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=f,group=pb.name)
  error=max(error,max(abs((pb.matrix@pb.bone.matrix_local.inverted()@geom)[i][j]-(T@ps[n]@rest[n].inverted())[i][j]) for i in range(4) for j in range(4)))
bpy.context.scene.frame_set(1)
# Author the delivery scene explicitly in centimeters. UE strips the object
# named Armature; leaving FBX's 100x object transform there loses animation units.
bpy.context.scene.unit_settings.scale_length=.01
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for b in rig.data.edit_bones:
 b.head*=100;b.tail*=100
bpy.ops.object.mode_set(mode='OBJECT')
for obj in meshes:
 for v in obj.data.vertices:v.co*=100
for layer in rig.animation_data.action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    if fc.data_path.endswith('.location'):
     for k in fc.keyframe_points:
      k.co.y*=100;k.handle_left.y*=100;k.handle_right.y*=100
bpy.context.scene.frame_set(2);bpy.context.scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for obj in meshes:obj.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(P/'SKM_Slime_Liquid.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,mesh_smooth_type='FACE')
# Static companion for editor preview references.
dg=bpy.context.evaluated_depsgraph_get();statics=[]
for obj in meshes:
 if obj.name=='Slime_Droplet':continue
 mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
 static=bpy.data.objects.new('Static_'+obj.name,mesh);bpy.context.collection.objects.link(static);statics.append(static)
bpy.ops.object.select_all(action='DESELECT')
for obj in statics:obj.select_set(True)
bpy.context.view_layer.objects.active=statics[0]
bpy.ops.export_scene.fbx(filepath=str(P/'SM_Slime_Liquid.fbx'),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=False)
(P/'export-report.json').write_text(json.dumps({'source':'../Production/Slime_Liquid.blend','bones':[b.name for b in data.bones],'max_deformation_matrix_error':error,'root_offset_m':list(offset)},indent=2))
assert error<.012,error
