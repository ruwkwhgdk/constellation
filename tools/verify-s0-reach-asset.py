import unreal as u,json,math
from pathlib import Path
O=Path(u.Paths.project_dir())/'ArtSource/SchoolOpening/ReachPose';d=json.loads((O/'source.json').read_text());r=json.loads((O/'reach-tracks.json').read_text())
folder='/Game/Constellation/Characters/Heroine/GamePilot/Locker/';src=u.load_asset(folder+'AS_Locker_ExitFall');out=u.load_asset(folder+'AS_Locker_ExitFall_Reach');E=u.AnimPoseExtensions
assert src.get_skeleton()==out.get_skeleton() and abs(src.get_play_length()-out.get_play_length())<1e-6
def desc(n):
 while n:
  if n=='clavicle_r':return True
  n=d['parents'][n]
 return False
max_other=max_contact=max_target=0
for i in range(201):
 t=i/120;poses=[E.get_anim_pose_at_time(a,t,u.AnimPoseEvaluationOptions(should_retarget=False)) for a in [src,out]]
 for n in d['parents']:
  ts=[E.get_bone_pose(p,n,u.AnimPoseSpaces.WORLD) for p in poses];err=ts[0].translation.distance(ts[1].translation)
  if not desc(n):max_other=max(max_other,err)
  if t>=1.06667:max_contact=max(max_contact,err)
for row in r['audit']:
 p=E.get_anim_pose_at_time(out,row['t'],u.AnimPoseEvaluationOptions(should_retarget=False));hand=E.get_bone_pose(p,'hand_r',u.AnimPoseSpaces.WORLD).translation
 max_target=max(max_target,hand.distance(u.Vector(*row['target'])))
result=dict(duration=out.get_play_length(),samples=201,other_bones_max_cm=max_other,restored_contact_max_cm=max_contact,hand_target_max_cm=max_target)
(O/'verified.json').write_text(json.dumps(result,indent=2));assert max_other<.01 and max_contact<.01 and max_target<.1,result
u.log('S0_REACH_ASSET_VERIFIED '+str(result))
