import unreal as u,json,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/ShadowPass_20261018'
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem)
review=(R/'tools/review-s0-shadow.py').read_text()
exec(review[review.index('rows=[];lights=[]'):review.index('cmd=u.SystemLibrary')])
(O/'baseline-actors.json').write_text(json.dumps(rows,indent=2));(O/'baseline-lights.json').write_text(json.dumps(lights,indent=2))
selected=[]
for actor in A.get_all_level_actors():
 if actor.get_actor_label() in ['S0_WetPolish_RockFill','S0_WetPolish_CoolCeilingBounce','S0_InteriorFill']:
  light=actor.get_component_by_class(u.LightComponent);assert light
  light.set_cast_shadows(False);selected.append(actor.get_actor_label())
assert len(selected)==3
(O/'selected-lights.json').write_text(json.dumps(selected,indent=2))
exec((R/'tools/save-s0-shadow.py').read_text(),globals())
u.SystemLibrary.quit_editor()
