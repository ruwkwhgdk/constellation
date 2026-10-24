import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent/"GripMeasure02";P.mkdir(exist_ok=False)
s=bpy.context.scene;s.frame_set(46)
r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"];phone=bpy.data.objects["Phone_ReviewCube"]
rows={}
for b in r.pose.bones:
 if b.name.startswith(("hand_","thumb_","index_","middle_","ring_","pinky_")) and b.name.endswith("_l"):
  rows[b.name]={"head_phone":list(phone.matrix_world.inverted()@r.matrix_world@b.head),"tail_phone":list(phone.matrix_world.inverted()@r.matrix_world@b.tail)}
(P/"bones.json").write_text(json.dumps(rows,indent=2))
# Keep only the left hand region in this diagnostic via camera clipping, not mesh edits.
center=(phone.matrix_world.translation+r.matrix_world@r.pose.bones["hand_l"].head)*.5
for view,off in [("edge",(1,0,0)),("top",(.05,-.1,1)),("player",(.05,.08,.15))]:
 s.camera.location=center+Vector(off);s.camera.rotation_euler=(center-s.camera.location).to_track_quat("-Z","Y").to_euler()
 s.camera.data.type="ORTHO";s.camera.data.ortho_scale=.25;s.camera.data.clip_start=.01
 s.render.filepath=str(P/(view+".png"));bpy.ops.render.render(write_still=True)

