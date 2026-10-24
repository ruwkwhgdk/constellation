"""Character garment clearance correction. Preserve wrist/finger orientations."""
import bpy,json,math,sys,runpy
from pathlib import Path
from mathutils import Matrix,Vector
root=Path(__file__).parent;p=root/"OneHandReview03";p.mkdir(exist_ok=False)
s=bpy.context.scene;r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"];c=bpy.data.objects["Phone_Portrait_ReviewCube"]
visibility={o:o.hide_get() for o in s.objects if o.type=="MESH"}
for o in visibility:o.hide_set(True)
def world(n):return r.matrix_world@r.pose.bones[n].matrix
def swing(n,child,goal):
 m=world(n);origin=m.translation
 q=(world(child).translation-origin).rotation_difference(goal-origin)
 r.pose.bones[n].matrix=r.matrix_world.inverted()@Matrix.Translation(origin)@q.to_matrix().to_4x4()@Matrix.Translation(-origin)@m
 bpy.context.view_layer.update()
rows=[];previous={}
for frame in range(1,s.frame_end+1):
 s.frame_set(frame)
 weight=0 if frame<=60 or frame>=218 else ((frame-60)/12 if frame<=72 else (1 if frame<=206 else (218-frame)/12))
 hand=world("hand_r");relative=hand.inverted()@c.matrix_world
 h,k,w=[world(n).translation for n in ("upperarm_r","lowerarm_r","hand_r")]
 goal=w+Vector((0,-.055*weight,0));l1=(k-h).length;l2=(w-k).length;v=goal-h
 d=min(max(v.length,abs(l1-l2)+.001),l1+l2-.001);axis=v.normalized()
 bend=k-h-axis*(k-h).dot(axis);bend.normalize()
 x=(l1*l1-l2*l2+d*d)/(2*d);elbow=h+axis*x+bend*math.sqrt(max(0,l1*l1-x*x))
 swing("upperarm_r","lowerarm_r",elbow);swing("lowerarm_r","hand_r",h+axis*d)
 now=world("hand_r");r.pose.bones["hand_r"].matrix=r.matrix_world.inverted()@Matrix.LocRotScale(now.translation,hand.to_quaternion(),now.to_scale())
 bpy.context.view_layer.update()
 for name in ("upperarm_r","lowerarm_r","hand_r"):
  b=r.pose.bones[name];b.rotation_mode="QUATERNION"
  if name in previous and b.rotation_quaternion.dot(previous[name])<0:b.rotation_quaternion.negate()
  previous[name]=b.rotation_quaternion.copy()
  for channel in ("rotation_quaternion","location","scale"):b.keyframe_insert(channel,frame=frame)
 c.matrix_world=world("hand_r")@relative
 if "cube" in previous and c.rotation_quaternion.dot(previous["cube"])<0:c.rotation_quaternion.negate()
 previous["cube"]=c.rotation_quaternion.copy()
 for channel in ("location","rotation_quaternion","scale"):c.keyframe_insert(channel,frame=frame)
 rows.append({"frame":frame,"clearance_weight":weight,"hand_goal_error_m":(world("hand_r").translation-goal).length})
for o,hidden in visibility.items():o.hide_set(hidden)
s.frame_set(120)
bpy.ops.wm.save_as_mainfile(filepath=str(p/"Heroine_Mixamo_OneHand_Cube07.blend"))
(p/"clearance_correction.json").write_text(json.dumps({"source":"../OneHandReview02/Heroine_Mixamo_OneHand_Cube06.blend","measured_clearance_max_m":.0505661,"correction_m":.055,"method":"Connected shoulder/elbow IK with original wrist orientation and finger local poses preserved; no new draw/stow motion","frames":rows},indent=2))
sys.argv.extend(["--stills","--no-shadows"])
runpy.run_path(str(root/"render_free_preview.py"))
