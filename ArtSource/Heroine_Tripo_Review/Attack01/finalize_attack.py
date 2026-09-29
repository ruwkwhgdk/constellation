import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Attack01.blend'))
r=bpy.data.objects['Heroine_AnimationRig'];sc=bpy.context.scene
# Importing the static sword FBX also imports its 25fps time settings.
sc.render.fps=60;sc.render.fps_base=1.;sc.frame_start=1;sc.frame_end=61
if not sc.get('attack_clearance_margin_finalized',False):
 for f in range(1,62):
  sc.frame_set(f);delta=r.pose.bones['DEF-spine'].matrix@r.data.bones['DEF-spine'].matrix_local.inverted()
  for i in range(8):
   d=r.matrix_world.to_3x3()@delta.to_3x3()@Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),0));d.z=0;d.normalize();d=r.matrix_world.inverted().to_3x3()@(d*.004)
   mats=[r.pose.bones[f'skirt_{i:02}.{j:02}'].matrix.copy() for j in [1,2]]
   for j,m in zip([1,2],mats):
    p=r.pose.bones[f'skirt_{i:02}.{j:02}'];m.translation+=d;p.matrix=m;bpy.context.view_layer.update();p.keyframe_insert('location',frame=f,group=p.name)
 sc['attack_clearance_margin_finalized']=True
# Keep quaternion component curves on a continuous hemisphere.
for obj in [r,bpy.data.objects['Preview_Sword']]:
 a=obj.animation_data.action;groups={}
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
     if fc.data_path.endswith('rotation_quaternion'):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
 for group in groups.values():
  if len(group)!=4:continue
  keys=[group[j].keyframe_points for j in range(4)];previous=None
  for i in range(len(keys[0])):
   q=[keys[j][i].co.y for j in range(4)]
   if previous is not None and sum(a*b for a,b in zip(previous,q))<0:
    for j in range(4):keys[j][i].co.y*=-1
    q=[-x for x in q]
   previous=q
sc.frame_set(31)
hand={n:{'matrix':[list(row) for row in p.matrix],'location':list(p.location),'rotation_quaternion':list(p.rotation_quaternion),'scale':list(p.scale)} for n,p in r.pose.bones.items() if not n.startswith(('DEF-','ORG-','MCH-'))}
(P/'combo_handoff_pose.json').write_text(json.dumps({'frame':31,'time_s':.5,'next_attack':'Start attack 02 near this follow-through pose. Validate blending over the open window; not yet tested with attack 02.','controls':hand},indent=2))
timing={'duration_s':1.0,'fps':60,'play_rate':1.0,'root_motion':False,'hitbox_on_s':.35,'hitbox_off_s':.50,'combo_window_open_s':.50,'combo_window_close_s':.65,'handoff_pose_s':.50,'end_attack_s':.99,'suggested_next_attack_blend_s':.08,'integration':'New review assets only. Existing attack blueprint, damage and input logic unchanged. Attack02/03 not authored yet.'}
(P/'attack01_timing.json').write_text(json.dumps(timing,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'Heroine_Attack01.blend'))
print('ATTACK_FINALIZED')
