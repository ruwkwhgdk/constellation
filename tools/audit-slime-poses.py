import unreal as u,json
from pathlib import Path
out={}
for path in ['/Game/Constellation/Characters/Enemies/Slime_Normal/Animation/AS_Slime_Idle','/Game/Constellation/Characters/Enemies/Slime_Normal/Animation/AS_Slime_Attack','/Game/Constellation/Characters/Enemies/Slime_Normal/Animation/AS_Slime_Damaged']:
 a=u.load_asset(path); poses={}
 for t in [0,.25,.4,.5,.75,1]:
  poses[str(t)]={str(b):str(u.AnimationLibrary.get_bone_pose_for_time(a,b,t,False)) for b in ['root','center','top']}
 out[path]=poses
bp=u.load_asset('/Game/Constellation/Characters/Enemies/Blueprints/BP_Slime_Base');cdo=u.get_default_object(bp.generated_class());cap=cdo.get_component_by_class(u.CapsuleComponent)
out['sourcecap']=[cap.get_scaled_capsule_radius(),cap.get_scaled_capsule_half_height()]
sk=u.load_asset('/Game/Constellation/Characters/Enemies/Slime_Normal/SKM_Slime_Normal');out['skeletal_mesh_skeleton']=str(sk.get_editor_property('skeleton'));out['physics']=str(sk.get_editor_property('physics_asset'))
Path(u.Paths.project_dir(),'Saved/VFXImplementation/slime-bone-audit.json').write_text(json.dumps(out,indent=2),encoding='utf8')
