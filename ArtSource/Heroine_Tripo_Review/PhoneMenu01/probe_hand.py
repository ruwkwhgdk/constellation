import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent/"HandProbe01";P.mkdir(exist_ok=False)
s=bpy.context.scene;r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
s.frame_set(46);r.animation_data_clear()
saved={b.name:b.rotation_quaternion.copy() for b in r.pose.bones}
for sign in (1,-1):
 for b in r.pose.bones:
  if b.name.startswith(("index_","middle_","ring_","pinky_","thumb_")) and b.name.endswith("_l"):
   b.rotation_quaternion=saved[b.name] if sign==1 else saved[b.name].inverted()
 bpy.context.view_layer.update()
 hand=r.matrix_world@r.pose.bones["hand_l"].head
 for view,offset in [("front",(.3,-1,.35)),("back",(-.3,1,.45)),("top",(0,0,1))]:
  center=hand+Vector((-.04,0,0));s.camera.location=center+Vector(offset)
  s.camera.rotation_euler=(center-s.camera.location).to_track_quat("-Z","Y").to_euler()
  s.camera.data.type="ORTHO";s.camera.data.ortho_scale=.3
  s.render.filepath=str(P/f"{sign}_{view}.png");bpy.ops.render.render(write_still=True)
