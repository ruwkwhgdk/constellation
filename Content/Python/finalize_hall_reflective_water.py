"""Use the minimal opaque reflection path established by the mirror probe."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v006'
D='/Game/Constellation/Environments/OvergrownHall/TripoFull';E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.load_level('/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull')
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
path=D+'/GrowthMaterials/M_OH_ReflectivePuddle'
mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset('M_OH_ReflectivePuddle',D+'/GrowthMaterials',u.Material,u.MaterialFactoryNew())
ML.delete_all_material_expressions(mat)
for cls,value,p in [(u.MaterialExpressionConstant3Vector,(.42,.58,.52),u.MaterialProperty.MP_BASE_COLOR),(u.MaterialExpressionConstant,1,u.MaterialProperty.MP_METALLIC),(u.MaterialExpressionConstant,.018,u.MaterialProperty.MP_ROUGHNESS)]:
    n=ML.create_material_expression(mat,cls)
    if isinstance(value,tuple):n.constant=u.LinearColor(*value,1)
    else:n.r=value
    assert ML.connect_material_property(n,'',p)
ML.recompile_material(mat);assert E.save_loaded_asset(mat,only_if_is_dirty=False)
w=actors['OH_SM_OH_Blockout_21'];w.modify();w.static_mesh_component.set_material(0,mat)
assert L.save_current_level()
report=load_current_json((OUT/'applied.json').read_text());report.update(water_material=mat.get_path_name(),water_roughness=.018,animated_ripples=False)
(OUT/'applied.json').write_text(json.dumps(report,indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_growth_water.py'))
