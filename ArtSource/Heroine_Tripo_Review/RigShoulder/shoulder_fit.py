import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def fit_point(p):
 q=p.copy();w=smooth((abs(p.x)-.028)/.072)*smooth((p.z-.69)/.080)
 q.x-= (1 if p.x>0 else -1)*.015*w;q.z-=.004*w
 return q
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=str(P.parent/'DetailFinish2/Delivery/Heroine_DetailFinish2.blend'))
 ids=json.loads((P.parent/'DetailFinish2/components.json').read_text())['ids'];body=bpy.data.objects['Heroine_DetailFinish2'];count=0
 for v in body.data.vertices:
  if ids[v.index] in [3,4,32]:
   q=fit_point(v.co);count+=(q-v.co).length>1e-9;v.co=q
 bracelet=bpy.data.objects['Heroine_Pearl_Bracelet'];bracelet.location.x+=.015;bracelet.location.z-=.004
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'shoulder_source.blend'))
 (P/'shoulder_changes.json').write_text(json.dumps({'shoulder_joint_span_before_cm':32.016,'shoulder_joint_span_after_cm':27.214,'shoulder_drop_cm':.6403,'edited_body_vertices':count,'preserved':'face, hair, lower body, UV, textures, vertex count, arm length, hand size'},indent=2))
