import bpy,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(bpy.data.filepath).parent
s=bpy.context.scene
target="Heroine_Rebuild_GameSkeleton" in bpy.data.objects
r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"] if target else next(o for o in s.objects if o.type=="ARMATURE")
def name(x):return x if target else "mixamorig:"+{"pelvis":"Hips","hand_l":"LeftHand","hand_r":"RightHand"}[x]
def pos(x):return r.matrix_world@r.pose.bones[name(x)].head
static="--stills" in sys.argv
no_shadows="--no-shadows" in sys.argv
out=P/("PreviewStills01" if static else ("Preview02" if no_shadows else "Preview01"));out.mkdir(exist_ok=False)
if not s.camera:
 bpy.ops.object.camera_add();s.camera=bpy.context.object
s.camera.data.type="ORTHO";s.camera.data.clip_start=.01
s.render.engine="BLENDER_WORKBENCH"
s.display.shading.color_type="SINGLE";s.display.shading.single_color=(.63,.65,.68)
s.display.shading.light="STUDIO";s.display.shading.show_cavity=True
s.display.shading.show_shadows=not no_shadows
s.display.shading.background_type="WORLD"
if not s.world:s.world=bpy.data.worlds.new("ReviewWorld")
s.world.color=(.09,.10,.12)
s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100
s.render.image_settings.file_format="PNG"
views=("front","side","hands") if target else ("front",)
static="--stills" in sys.argv
end=s.frame_end
frames=sorted(set(min(end,f) for f in [1,16,31,46,61,91,180,end//2,end-98,end-78,end-58,end-38,end-18,end])) if static else range(1,end+1)
for view in views:
 folder=out/view;folder.mkdir()
 for f in frames:
  s.frame_set(f);hip=pos("pelvis")
  if view=="hands":
   center=(pos("hand_l")+pos("hand_r"))*.5+Vector((0,0,.04))
   offset=Vector((.1,-1,.2));scale=.55
  else:
   center=Vector((hip.x,hip.y,.85 if target else .95))
   offset=Vector((.3,-4,.3)) if view=="front" else Vector((4,0,.15));scale=1.9 if target else 2.1
  s.camera.location=center+offset
  s.camera.rotation_euler=(center-s.camera.location).to_track_quat("-Z","Y").to_euler()
  s.camera.data.ortho_scale=scale
  s.render.filepath=str(folder/f"{f:04}.png");bpy.ops.render.render(write_still=True)
 print("VIEW_COMPLETE",view,flush=True)
(out/"provenance.json").write_text(json.dumps({"source_blend":bpy.data.filepath,"frames":list(frames),"fps":30,"display":"Neutral clay shading for joint inspection, original animation timing and poses."},indent=2))
