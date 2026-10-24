import bpy,math,json
from pathlib import Path
from mathutils import Matrix,Euler,Vector
s=bpy.context.scene;s.frame_set(120)
c=bpy.data.objects["Phone_Portrait_ReviewCube"];base=bpy.data.objects["Heroine_Rebuild_GameSkeleton"].matrix_world@bpy.data.objects["Heroine_Rebuild_GameSkeleton"].pose.bones["hand_r"].matrix@Matrix(json.loads((Path(__file__).parent/"OneHandRetarget01/cube_review.json").read_text())["offset"]);c.animation_data_clear()

s.render.engine="BLENDER_WORKBENCH";s.display.shading.show_shadows=False
s.display.shading.color_type="SINGLE";s.display.shading.single_color=(.63,.65,.68)
r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"];center=r.matrix_world@r.pose.bones["hand_r"].head+Vector((0,0,.07))
s.camera.location=center+Vector((.15,-1,.25));s.camera.rotation_euler=(center-s.camera.location).to_track_quat("-Z","Y").to_euler()
s.camera.data.type="ORTHO";s.camera.data.ortho_scale=.36
s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100
out=Path(bpy.data.filepath).parent/"CubeTiltReview";out.mkdir(exist_ok=False)
options=[((-.015,-.035,.0525),(a,0,0)) for a in (30,45,60,75)]
for n,(offset,rotation) in enumerate(options,1):
 c.matrix_world=base@Matrix.Translation(offset)@Euler(tuple(math.radians(a) for a in rotation)).to_matrix().to_4x4()
 s.render.filepath=str(out/f"{n}.png");bpy.ops.render.render(write_still=True)
(out/"options.json").write_text(json.dumps(options))

