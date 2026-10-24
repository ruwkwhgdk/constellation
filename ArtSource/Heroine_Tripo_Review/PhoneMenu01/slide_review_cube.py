import bpy,json,sys,runpy
from pathlib import Path
from mathutils import Matrix
root=Path(__file__).parent;p=root/"OneHandReview04";p.mkdir(exist_ok=False)
s=bpy.context.scene;c=bpy.data.objects["Phone_Portrait_ReviewCube"];poses={}
for f in range(1,s.frame_end+1):
 s.frame_set(f);poses[f]=c.matrix_world.copy()
for f,m in poses.items():
 s.frame_set(f)
 weight=0 if f<=60 or f>=218 else ((f-60)/12 if f<=72 else (1 if f<=206 else (218-f)/12))
 c.matrix_world=m@Matrix.Translation((0,.03*weight,0))
 for channel in ("location","rotation_quaternion","scale"):c.keyframe_insert(channel,frame=f)
s.frame_set(120)
bpy.ops.wm.save_as_mainfile(filepath=str(p/"Heroine_Mixamo_OneHand_Cube08.blend"))
(p/"provenance.json").write_text(json.dumps({"source":"../OneHandReview03/Heroine_Mixamo_OneHand_Cube07.blend","change":"Cube attachment slide by 0.03m along long axis in Texting segment only, using same source crossfades. Character animation unchanged.","status":"Review candidate"},indent=2))
sys.argv.extend(["--stills","--no-shadows"])
runpy.run_path(str(root/"render_free_preview.py"))
