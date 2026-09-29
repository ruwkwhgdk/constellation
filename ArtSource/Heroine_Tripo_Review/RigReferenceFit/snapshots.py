import bpy,math,json,sys
from mathutils import Vector,Quaternion,Matrix
from pathlib import Path
P=Path(__file__).resolve().parent
labels=['reference','before','after']
for label in labels:
 if label=='reference':
  bpy.ops.wm.open_mainfile(filepath=str(P/'comparison_aligned.blend'))
  obs=[o for o in bpy.context.scene.objects if o.name.startswith('REF_')]
  rig=next(o for o in obs if o.type=='ARMATURE');rig.location.x+=.79
  meshes=[o for o in obs if o.type=='MESH'];factor=1.
 else:
  root=P if label=='after' else P.parent/'RigContourFix'
  bpy.ops.wm.open_mainfile(filepath=str(root/'rig_bound.blend'))
  rig=bpy.data.objects['Heroine_AnimationRig'];meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('WGT-')]
  factor=1.6/(max((o.matrix_world@v.co).z for o in meshes for v in o.data.vertices)-min((o.matrix_world@v.co).z for o in meshes for v in o.data.vertices))
 for pose,angle in [('rest',0),('relaxed',75),('raised',-20)]:
  for b in rig.pose.bones:b.matrix_basis.identity()
  for b in rig.pose.bones:
   if 'IK_FK' in b:b['IK_FK']=1.
  for side,s in [('L',1),('R',-1)]:
   name=('mixamorig:'+('Left' if s==1 else 'Right')+'Arm') if label=='reference' else 'upper_arm_fk.'+side
   b=rig.pose.bones[name]
   rest=rig.matrix_world.to_quaternion()@b.bone.matrix_local.to_quaternion()
   vec=rig.matrix_world.to_3x3()@(b.bone.tail_local-b.bone.head_local)
   initial=math.degrees(math.atan2(-vec.z,abs(vec.x)))
   rotation=angle-initial if pose!='rest' else 0
   b.rotation_mode='QUATERNION';b.rotation_quaternion=rest.inverted()@Quaternion(Vector((0,1,0)),math.radians(s*rotation))@rest
  bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();copies=[]
  for o in meshes:
   ev=o.evaluated_get(dg);data=bpy.data.meshes.new_from_object(ev,depsgraph=dg)
   data.transform(Matrix.Scale(factor,4)@o.matrix_world)
   copy=bpy.data.objects.new(label+'_'+o.name,data);copies.append(copy)
  bpy.data.libraries.write(str(P/f'snapshot_{label}_{pose}.blend'),set(copies),fake_user=True)
  for o in copies:bpy.data.objects.remove(o)
 print('SNAPSHOTS',label,flush=True)
