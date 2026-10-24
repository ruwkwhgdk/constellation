import bpy,math
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).parent;bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Sword_ArmCorrection12.blend'));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton']
poses={};originals={}
for f in [49,523]:
 s.frame_set(f);originals[f]={b.name:b.matrix_basis.copy() for b in r.pose.bones}
r.animation_data.action=None
changes={'index':((0,0,-1),[-12,22,0]),'middle':((-1,0,0),[-12,22,-5]),'ring':((0,0,1),[-10,18,-4]),'pinky':((0,0,1),[-6,10,0])}
for f in [49,523]:
 for b in r.pose.bones:b.matrix_basis=originals[f][b.name]
 for finger,(axis,degs) in changes.items():
  for i,deg in enumerate(degs,1):
   b=r.pose.bones[f'{finger}_{i:02}_r'];print('BEFORE',f,b.name,b.rotation_mode,list(b.rotation_quaternion),list(b.rotation_euler),len(b.constraints));b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion(axis,math.radians(deg))@b.rotation_quaternion
 bpy.context.view_layer.update();poses[f]={b.name:b.matrix_basis.copy() for b in r.pose.bones}
r.animation_data.action=bpy.data.actions.new('FingerPose13')
for f,pose in poses.items():
 for b in r.pose.bones:
  b.matrix_basis=pose[b.name]
  for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=f)
s.frame_set(523);bpy.ops.wm.save_as_mainfile(filepath=str(P/'Pose13.blend'))
