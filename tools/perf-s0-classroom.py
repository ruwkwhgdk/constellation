import unreal as u,json,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/PerfPass_20261018'
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem)
review=(R/'tools/review-s0-perf.py').read_text()
exec(review[review.index('rows=[];lights=[]'):review.index('cmd=u.SystemLibrary')])
(O/'baseline-actors.json').write_text(json.dumps(rows,indent=2));(O/'baseline-lights.json').write_text(json.dumps(lights,indent=2))
flags=list(pc.get_editor_property('show_flag_settings'));flags=[f for f in flags if f.show_flag_name!='DynamicShadows'];flags.append(u.EngineShowFlagsSetting(show_flag_name='DynamicShadows',enabled=False));pc.set_editor_property('show_flag_settings',flags)
exec(review[review.index('cmd=u.SystemLibrary'):])
