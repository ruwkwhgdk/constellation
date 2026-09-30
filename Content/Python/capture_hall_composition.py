from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,hashlib
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v018';report=load_current_json((OUT/'applied.json').read_text())
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(report['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};assert len(actors)==report['actor_count']
source=(ROOT/'Content/Python/apply_hall_composition.py').read_text();exec(source[source.index('def scene_signature():'):source.index('\nsignature=')]);assert scene_signature()==report['scene_signature']
cam=actors['OH_ReferenceCamera'];p=cam.get_actor_location();r=cam.get_actor_rotation();cc=cam.get_component_by_class(u.CameraComponent)
assert max(abs(v-w) for v,w in zip([p.x,p.y,p.z],report['position']))<.001
assert abs(r.pitch-report['pitch'])<.001 and abs(cc.field_of_view-report['fov'])<.001
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,reference_camera=True,other_actor_transforms_and_meshes_unchanged=True,actor_count=len(actors),gameplay_camera_changed=False,playtest='user'),indent=2));u.log('HALL_COMPOSITION_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v018').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',report['map']).replace('unreal_exposure_fixed.png','unreal_composition.png').replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_composition','exec'),globals())
