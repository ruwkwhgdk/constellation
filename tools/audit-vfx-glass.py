import unreal as u
from pathlib import Path
out=Path(u.Paths.project_dir())/'Saved/VFXImplementation'
for n in ['BP_Glass','BP_GlassWindow']:
 p='/Game/Constellation/Gameplay/Interaction/Actors/'+n
 (out/(n+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(u.load_asset(p)),encoding='utf8')
(out/'trail-parameters.txt').write_text(u.ConstellationFXLibrary.describe_niagara(u.load_asset('/Game/Constellation/VFX/NS_SwordTrail')),encoding='utf8')
