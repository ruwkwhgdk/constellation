import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/RoutePass_20261017'
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem)
review=(R/'tools/review-s0-route.py').read_text()
exec(review[review.index('rows=[];lights=[]'):review.index('cmd=u.SystemLibrary')])
(O/'baseline-actors.json').write_text(json.dumps(rows,indent=2));(O/'baseline-lights.json').write_text(json.dumps(lights,indent=2))
targets=[a for a in A.get_all_level_actors() if a.get_actor_label().startswith(('S0_Art_Relief_','S0_Ref_RockFace_'))]
assert len(targets)==13
(O/'removed.json').write_text(json.dumps([dict(name=a.get_name(),label=a.get_actor_label(),bounds=str(a.get_actor_bounds(False))) for a in targets],indent=2))
for a in targets:assert A.destroy_actor(a)
import time,traceback
exec(review[review.index('cmd=u.SystemLibrary'):])
