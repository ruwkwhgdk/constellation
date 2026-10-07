import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent; r=bpy.data.objects['Heroine_AnimationRig']; bpy.context.scene.frame_set(18)
rows={}
for s in ['L','R']:
 for prefix in ['thigh_parent','thigh_fk','shin_fk','foot_fk','foot_ik','thigh_ik_target','DEF-thigh','DEF-shin','DEF-foot']:
  n=prefix+'.'+s
  if n not in r.pose.bones: continue
  b=r.pose.bones[n]
  rows[n]={'length':b.bone.length,'head':list(b.head),'tail':list(b.tail),'props':{k:str(v) for k,v in b.items()},
   'constraints':[{'name':c.name,'type':c.type,'influence':c.influence} for c in b.constraints]}
(P/'pose_debug.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
