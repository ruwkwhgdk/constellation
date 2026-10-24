import bpy,json,math,sys,runpy
from pathlib import Path
from mathutils import Matrix,Euler
root=Path(__file__).parent;p=Path(bpy.data.filepath).parent;s=bpy.context.scene
r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
offset=Matrix(json.loads((root/"OneHandRetarget01/cube_review.json").read_text())["offset"])
adjust=Matrix.Translation((-.015,-.035,.0525))@Euler((math.radians(90),0,0)).to_matrix().to_4x4()
bpy.ops.mesh.primitive_cube_add(size=1);c=bpy.context.object;c.name="Phone_Portrait_ReviewCube"
c.scale=(.055,.12,.006);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
c.rotation_mode="QUATERNION";previous=None
for f in range(1,s.frame_end+1):
 s.frame_set(f);c.matrix_world=r.matrix_world@r.pose.bones["hand_r"].matrix@offset@adjust
 if previous and c.rotation_quaternion.dot(previous)<0:c.rotation_quaternion.negate()
 previous=c.rotation_quaternion.copy()
 for channel in ("location","rotation_quaternion","scale"):c.keyframe_insert(channel,frame=f)
 c.hide_render=not 31<=f<=245;c.keyframe_insert("hide_render",frame=f)
s.frame_set(120)
bpy.ops.wm.save_as_mainfile(filepath=str(p/"Heroine_Mixamo_OneHand_Cube04.blend"))
(p/"cube_review.json").write_text(json.dumps({"dimensions_m":[.055,.12,.006],"source_attachment":"../OneHandRetarget01/cube_review.json","adjust_offset":[-.015,-.035,.0525],"rotation_deg":[90,0,0],"status":"Review candidate"},indent=2))
sys.argv.extend(["--stills","--no-shadows"])
runpy.run_path(str(root/"render_free_preview.py"))
