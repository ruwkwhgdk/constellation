import bpy,math,json,sys,runpy
from pathlib import Path
from mathutils import Matrix,Euler
root=Path(__file__).parent
out=root/"OneHandProp03"
out.mkdir(exist_ok=False)
s=bpy.context.scene;c=bpy.data.objects["Phone_Portrait_ReviewCube"]
poses={}
for f in range(1,s.frame_end+1):
 s.frame_set(f);poses[f]=c.matrix_world.copy()
c.animation_data_clear()
for v in c.data.vertices:
 v.co.x*=.055/.065;v.co.y*=.12/.13;v.co.z*=.006/.008
adjust=Matrix.Translation((0,-.015,.04))@Euler((math.radians(90),0,0)).to_matrix().to_4x4()
previous=None
for f,m in poses.items():
 s.frame_set(f);c.matrix_world=m@adjust;c.rotation_mode="QUATERNION"
 if previous and c.rotation_quaternion.dot(previous)<0:c.rotation_quaternion.negate()
 previous=c.rotation_quaternion.copy()
 for channel in ("location","rotation_quaternion","scale"):c.keyframe_insert(channel,frame=f)
 c.hide_render=not 31<=f<=245;c.keyframe_insert("hide_render",frame=f)
s.frame_set(120)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"Heroine_Mixamo_OneHand_Cube03.blend"))
(out/"provenance.json").write_text(json.dumps({"character_animation":"../OneHandRetarget01/Heroine_Mixamo_OneHand_Cube01.blend","changes":"Cube geometry and attachment only; no character or animation edits","dimensions_m":[.055,.12,.006],"offset":[0,-.015,.04],"rotation_deg":[90,0,0],"status":"Visual contact review required"},indent=2))
sys.argv.append("--stills")
runpy.run_path(str(root/"render_free_preview.py"))

