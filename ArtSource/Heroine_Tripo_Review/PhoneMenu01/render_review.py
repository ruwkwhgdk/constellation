"""Render actual reopened candidate, no rig modifications."""
import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(bpy.data.filepath).parent
out=P/"VideoFrames";out.mkdir(exist_ok=False)
s=bpy.context.scene;r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"];phone=bpy.data.objects["Phone_ReviewCube"]
s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100
s.camera.data.type="ORTHO";s.camera.data.clip_start=.01
s.render.image_settings.file_format="PNG"
for view in ("front","side","hand","player"):
 folder=out/view;folder.mkdir()
 for f in (range(1,2) if view=="player" else range(1,152)):
  s.frame_set(f)
  wrist=r.matrix_world@r.pose.bones["hand_l"].head
  if view=="front":center=Vector((0,-.05,.85));offset=Vector((.7,-4,.9));scale=1.85
  elif view=="side":center=Vector((0,-.1,.85));offset=Vector((4,-.1,.4));scale=1.85
  elif view=="hand":center=(wrist+phone.matrix_world.translation)*.5;offset=Vector((.4,-.7,.35));scale=.46
  else: # Fixed proposed menu shot after the draw; repeated hold for close examination.
   s.frame_set(61)
   wrist=r.matrix_world@r.pose.bones["hand_l"].head
   center=phone.matrix_world.translation+Vector((0,0,-.025));offset=Vector((.08,.17,.20));scale=.36
  s.camera.location=center+offset
  s.camera.rotation_euler=(center-s.camera.location).to_track_quat("-Z","Y").to_euler()
  s.camera.data.ortho_scale=scale
  s.render.filepath=str(folder/f"{f:04}.png");bpy.ops.render.render(write_still=True)
 print("VIDEO_VIEW_DONE",view,flush=True)
(P/"render_provenance.json").write_text(json.dumps({"blend":bpy.data.filepath,"fps":30,"frames":[1,151],"views":["front","side","hand","player"],"player_view":"Held frame 61, static menu framing study. Other videos show the full saved animation."},indent=2))
