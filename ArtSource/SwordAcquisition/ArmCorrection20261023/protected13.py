import bpy,json,math
from pathlib import Path
P=Path(__file__).parent
names=['pelvis','thigh_l','thigh_r','calf_l','calf_r','foot_l','foot_r','ball_l','ball_r']
vals={}
for label,file in [('source',P.parent/'GripRevision20261023/Heroine_Sword_RightUpper06.blend'),('final',P/'Heroine_Sword_ArmCorrection13.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(file));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];sw=bpy.data.objects['Sword_proxy'];rows=[]
 for f in range(1,740):
  s.frame_set(f);rows.append({n:[list(row) for row in r.pose.bones[n].matrix] for n in names})
 s.frame_set(1);vals[label]={'rows':rows,'first_sword':[list(row) for row in sw.matrix_world]}
maximum=max(abs(a-b) for x,y in zip(vals['source']['rows'],vals['final']['rows']) for n in names for ar,br in zip(x[n],y[n]) for a,b in zip(ar,br));sword=max(abs(a-b) for ar,br in zip(vals['source']['first_sword'],vals['final']['first_sword']) for a,b in zip(ar,br))
out={'frames':739,'protected_bones':names,'max_world_matrix_difference':maximum,'first_sword_max_matrix_difference':sword};(P/'protected_motion13.json').write_text(json.dumps(out,indent=2));print(out);assert maximum<1e-5 and sword<1e-5
