import unreal as u,json
from pathlib import Path
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/'
checked=[]
for name in ['M_S0_WoodCaveFloor','M_S0_ShallowWater']:
 m=u.EditorAssetLibrary.load_asset(D+name);assert m
 m.set_editor_property('used_with_static_lighting',True)
 u.MaterialEditingLibrary.recompile_material(m)
 assert u.EditorAssetLibrary.save_loaded_asset(m,False)
 assert m.get_editor_property('used_with_static_lighting')
 checked.append(m.get_path_name())
(Path(u.Paths.project_dir())/'Saved/S0WetFloor/20261017/material-usage.json').write_text(json.dumps(dict(static_lighting=True,materials=checked),indent=2))
u.log('S0_WET_USAGE_VERIFIED')
