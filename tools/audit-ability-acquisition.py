import unreal as u
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'Saved/AbilityAcquisition';out.mkdir(exist_ok=True)
for path in ['/Game/Constellation/Gameplay/Interaction/Components/Ac_Ability','/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object','/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object_Sequence']:
 b=u.load_asset(path);assert b,path
 (out/(path.split('/')[-1]+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(b),encoding='utf8')
u.log('ABILITY_AUDIT_COMPLETE')
