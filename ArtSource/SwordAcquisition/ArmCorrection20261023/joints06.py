import bpy,json,math
from pathlib import Path
P=Path(__file__).parent;bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Sword_ArmCorrection06.blend'));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];names=[n for n in r.pose.bones.keys() if any(n.startswith(k) for k in ['upperarm','lowerarm','hand_'])];rows=[];prev={};pe={};maxq={};maxp={}
for half in range(2,1479):
 f=half/2;s.frame_set(int(f),subframe=f%1);row={'frame':f,'bones':{}}
 for n in names:
  b=r.pose.bones[n];q=b.matrix_basis.to_quaternion();swing,twist=q.to_swing_twist('Y');world=b.matrix.to_quaternion();p=b.matrix.translation;delta=math.degrees(world.rotation_difference(prev[n]).angle) if n in prev else 0;delta=min(delta,360-delta);move=(p-pe[n]).length*1000 if n in pe else 0
  row['bones'][n]={'twist':math.degrees(twist),'swing':math.degrees(swing.angle),'step_world_deg':delta,'step_position_mm':move,'local_t':list(b.location),'world_position':list(p),'world_q':list(world),'local_q':list(q)};prev[n]=world;pe[n]=p.copy()
  if delta>maxq.get(n,{}).get('value',-1):maxq[n]={'value':delta,'frame':f}
  if move>maxp.get(n,{}).get('value',-1):maxp[n]={'value':move,'frame':f}
 rows.append(row)
(P/'local-joints06.json').write_text(json.dumps(rows));(P/'continuity-summary06.json').write_text(json.dumps({'max_half_frame_world_degrees':maxq,'max_half_frame_position_mm':maxp},indent=2));print(json.dumps({'q':maxq,'p':maxp},indent=2))

