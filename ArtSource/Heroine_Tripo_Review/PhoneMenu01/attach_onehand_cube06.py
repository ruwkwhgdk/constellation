import bpy,json,math,sys,runpy
from pathlib import Path
from mathutils import Matrix,Euler,Vector
root=Path(__file__).parent;p=root/"OneHandReview02";p.mkdir(exist_ok=False);s=bpy.context.scene
r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
offset=Matrix(json.loads((root/"OneHandRetarget01/cube_review.json").read_text())["offset"])
bpy.ops.mesh.primitive_cube_add(size=1);c=bpy.context.object;c.name="Phone_Portrait_ReviewCube"
c.scale=(.055,.12,.006);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
c.rotation_mode="QUATERNION";previous=None
call_position=Vector((0,0,.04));text_position=Vector((-.015,-.035,.0525))
call_rotation=Euler((0,0,0)).to_quaternion()
text_rotation=Euler((math.radians(60),0,0)).to_quaternion()
for f in range(1,s.frame_end+1):
 s.frame_set(f)
 weight=0 if f<=60 or f>=218 else ((f-60)/12 if f<=72 else (1 if f<=206 else (218-f)/12))
 adjust=Matrix.LocRotScale(call_position.lerp(text_position,weight),call_rotation.slerp(text_rotation,weight),Vector((1,1,1)))
 c.matrix_world=r.matrix_world@r.pose.bones["hand_r"].matrix@offset@adjust
 if previous and c.rotation_quaternion.dot(previous)<0:c.rotation_quaternion.negate()
 previous=c.rotation_quaternion.copy()
 for channel in ("location","rotation_quaternion","scale"):c.keyframe_insert(channel,frame=f)
 c.hide_render=not 31<=f<=245;c.keyframe_insert("hide_render",frame=f)
s.frame_set(120)
bpy.ops.wm.save_as_mainfile(filepath=str(p/"Heroine_Mixamo_OneHand_Cube06.blend"))
(p/"cube_review.json").write_text(json.dumps({"dimensions_m":[.055,.12,.006],"source_attachment":"../OneHandRetarget01/cube_review.json","call_offset":list(call_position),"text_offset":list(text_position),"text_rotation_deg":[60,0,0],"transition_frames":[[61,72],[207,218]],"status":"Review candidate; character poses unchanged"},indent=2))
sys.argv.extend(["--stills","--no-shadows"])
runpy.run_path(str(root/"render_free_preview.py"))
