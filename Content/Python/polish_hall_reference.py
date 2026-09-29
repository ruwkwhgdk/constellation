"""Final light direction and shallow-water pigment, without rebuilding forest or flock."""
import unreal as u,runpy,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v009';D='/Game/Environment/OvergrownHall/TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(D+'/Maps/L_OvergrownHall_TripoFull')
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
actors['OH_Sun'].set_actor_rotation(u.Rotator(pitch=-32,yaw=-55,roll=0),False)
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
m=E.load_asset(D+'/ReferenceMaterials/M_OH_QuietWater');m.modify();ML.delete_all_material_expressions(m);g=Graph(m)
g.prop(g.color((.62,.80,.70)),u.MaterialProperty.MP_BASE_COLOR);g.prop(g.c(1),u.MaterialProperty.MP_METALLIC);g.prop(g.color((3,9,8)),u.MaterialProperty.MP_EMISSIVE_COLOR)
t=g.n(u.MaterialExpressionTime);sine=g.n(u.MaterialExpressionSine);g.wire(g.mul(t,g.c(.035)),sine);g.prop(g.add(g.c(.035),g.mul(sine,g.c(.008))),u.MaterialProperty.MP_ROUGHNESS)
ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False);assert L.save_current_level()
report=json.loads((OUT/'applied.json').read_text());report['sun_yaw']=-55;report['water_pigment']=[.62,.80,.70];report['water_artistic_emission']=[3,9,8];(OUT/'applied.json').write_text(json.dumps(report,indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_reference.py'))
