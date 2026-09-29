import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'rig_bound.blend'))
rig=bpy.data.objects['Heroine_AnimationRig'];sc=bpy.context.scene
(P/'renders').mkdir(exist_ok=True)
sc.cycles.samples=16;sc.render.resolution_x=750;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.render.use_border=False;sc.render.use_crop_to_border=False
def reset():
 for p in rig.pose.bones:p.matrix_basis.identity()
 for p in rig.pose.bones:
  if 'IK_FK' in p:p['IK_FK']=1.0
 bpy.context.view_layer.update()
def rotate(n,axis,degrees):
 p=rig.pose.bones[n];p.rotation_mode='QUATERNION';q=p.bone.matrix_local.to_quaternion();p.rotation_quaternion=q.inverted()@Quaternion(Vector(axis),math.radians(degrees))@q
def pose(name):
 reset()
 if name in ['relaxed','bend','squat','hand']:
  for side,s in [('L',1),('R',-1)]:rotate('upper_arm_fk.'+side,(0,1,0),s*65)
 if name in ['bend','hand']:
  for side,s in [('L',1),('R',-1)]:
   rotate('forearm_fk.'+side,(0,0,1),-s*80)
   for f in ['f_index','f_middle','f_ring','f_pinky']:
    for j,deg in [(1,45),(2,55),(3,35)]:rotate(f'{f}.{j:02}.{side}',(0,1,0),s*deg)
  rotate('head',(0,0,1),15)
 if name=='squat':
  for side in ['L','R']:rig.pose.bones['thigh_parent.'+side]['IK_FK']=0.0
  rig.pose.bones['torso'].location=rig.data.bones['torso'].matrix_local.to_quaternion().inverted()@Vector((0,.025,-.08))
  # Torso control's local Y is approximately vertical; inspect final joint locations numerically.
  bpy.context.view_layer.update()
 bpy.context.view_layer.update()
def render(name):
 cam=sc.camera;cam.location=(.8,-3,.53) if name!='squat' else (2,-3,.53);cam.rotation_euler=(Vector((0,0,.51))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.12
 if name=='hand':
  target=rig.pose.bones['DEF-hand.R'].head;cam.location=target+Vector((-.25,-.35,.3));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.19;sc.render.resolution_x=sc.render.resolution_y=900
 sc.render.filepath=str(P/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
 print('RENDERED',name,flush=True)
poses=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['rest','relaxed','bend','squat','hand']
for name in poses:pose(name);render(name)
reset()
