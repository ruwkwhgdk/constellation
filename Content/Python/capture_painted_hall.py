"""Fresh-process render and saved-state verification; no material rebuild."""
import unreal as u
import runpy,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir())
MAP='/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull'
OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v004'
runpy.run_path(str(ROOT/'Content/Python/verify_tripo_full_hall.py'))
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
count=0
for actor in actors:
    label=actor.get_actor_label()
    if label.startswith(('OH_FULL_','OH_Tripo_Tree_','OH_STRUCTURE_Roof_')):
        assert '/PaintedMaterials/' in actor.static_mesh_component.get_material(0).get_path_name(),label
        count+=1
    if label=='OH_Exposure':
        pp=actor.get_editor_property('settings')
        assert abs(pp.color_contrast.x-.90)<.001 and pp.override_color_contrast
        assert abs(pp.color_gamma.x-1.06)<.001 and pp.override_color_gamma
    if label=='OH_Sun':
        assert actor.get_component_by_class(u.DirectionalLightComponent).light_source_angle==10
assert count==532
(OUT/'verification.json').write_text(json.dumps(dict(fresh_process=True,saved_material_overrides=count,geometry_and_collision_checks='passed',saved_color_grade='passed',playtest=False),indent=2))
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text()
script=script.replace("out=root/'ArtSource/OvergrownHall/Scene/v001'","out=root/'ArtSource/OvergrownHall/TripoReplacement/v004'").replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',MAP).replace('unreal_exposure_fixed.png','unreal_painted.png')
exec(compile(script,'capture_saved_painted_hall','exec'),globals())
