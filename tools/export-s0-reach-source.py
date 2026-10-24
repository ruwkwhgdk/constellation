import unreal as u,json
from pathlib import Path
O=Path(u.Paths.project_dir())/'ArtSource/SchoolOpening/ReachPose';O.mkdir(parents=True,exist_ok=True)
a=u.load_asset('/Game/Constellation/Characters/Heroine/GamePilot/Locker/AS_Locker_ExitFall');E=u.AnimPoseExtensions
parents=json.loads(Path('C:/Users/User/Documents/Constellation_ArtWorkspace/ArtSource/Heroine_Rebuild/GamePilot/LockerAnimation/motion_delivery.json').read_text())['parents']
def vec(v):return [v.x,v.y,v.z]
def tr(t):return dict(t=vec(t.translation),q=[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w],s=vec(t.scale3d))
rows=[]
for f in range(round(a.get_play_length()*30)+1):
 pose=E.get_anim_pose_at_time(a,f/30,u.AnimPoseEvaluationOptions(should_retarget=False))
 rows.append({n:dict(local=tr(E.get_bone_pose(pose,n,u.AnimPoseSpaces.LOCAL)),world=tr(E.get_bone_pose(pose,n,u.AnimPoseSpaces.WORLD))) for n in parents})
(O/'source.json').write_text(json.dumps(dict(asset=a.get_path_name(),duration=a.get_play_length(),fps=30,parents=parents,rows=rows)))
u.log('S0_REACH_SOURCE_EXPORTED '+str(a.get_play_length()))
