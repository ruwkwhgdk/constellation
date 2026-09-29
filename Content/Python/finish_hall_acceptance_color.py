"""v028: restore cool architectural midtones and a localized warm shaft."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v028';OUT.mkdir(parents=True,exist_ok=True);D='/Game/Environment/OvergrownHall/TripoFull';MAP=D+'/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);assert L.load_level(MAP);actors={a.get_actor_label():a for a in A.get_all_level_actors()}
if not (OUT/'baseline.json').exists():(OUT/'baseline.json').write_text((OUT.parent/'v027/baseline.json').read_text())
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
p=D+'/AtmosphereFinish/M_OH_ReferenceCoolPillar';m=E.load_asset(p) if E.does_asset_exist(p) else E.duplicate_asset(D+'/AtmosphereFinish/M_OH_CoolPillar',p);assert m;m.modify();g=Graph(m);pos=g.n(u.MaterialExpressionWorldPosition);n=g.noise(g.mul(pos,g.color((1,1,.5))),.005);stone=g.lerp(g.color((.07,.18,.24)),g.color((.26,.38,.41)),n);peel=g.clamp(g.mul(g.sub(g.noise(pos,.013),g.c(.59)),g.c(4)));color=g.lerp(stone,g.color((.37,.43,.41)),g.mul(peel,g.c(.5)));g.prop(color,u.MaterialProperty.MP_BASE_COLOR);g.prop(g.mul(color,g.c(115)),u.MaterialProperty.MP_EMISSIVE_COLOR);ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False)
pillars=[]
for n,a in actors.items():
    if n.startswith('OH_FULL_02_'):a.modify();a.static_mesh_component.set_material(0,m);pillars.append(n)
for name,intensity,scatter,color in [('OH_Finish_FocalSun',2800000,8,(1,.60,.22,1)),('OH_Reference_LowerWindowShaft',900000,10,(1,.70,.32,1))]:
    a=actors[name];a.modify();c=a.get_component_by_class(u.SpotLightComponent);c.set_editor_property('intensity',intensity);c.set_editor_property('volumetric_scattering_intensity',scatter);c.set_light_color(u.LinearColor(*color))
assert L.save_current_level();(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,pillars=pillars,material=m.get_path_name(),playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_acceptance_color.py'))
