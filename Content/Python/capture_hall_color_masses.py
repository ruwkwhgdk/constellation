from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v022';r=load_current_json((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(r['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};baseline=load_current_json((OUT/'baseline.json').read_text());assert set(actors)==set(baseline)
for n,b in baseline.items():
    a=actors[n];p=a.get_actor_location();s=a.get_actor_scale3d();rot=a.get_actor_rotation()
    for expected,actual in [(b['position'],[p.x,p.y,p.z]),(b['scale'],[s.x,s.y,s.z]),(b['rotation'],[rot.pitch,rot.yaw,rot.roll])]:assert all(abs(v-w)<.001 for v,w in zip(expected,actual)),n
    if b.get('mesh'):assert a.static_mesh_component.static_mesh.get_path_name()==b['mesh'],n
for n in r['plants']:assert actors[n].static_mesh_component.get_material(0).get_name()=='M_OH_LeafColorMass'
for n in r['pillars']:assert actors[n].static_mesh_component.get_material(0).get_name()=='M_OH_CoolPillar'
assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.get_material(0).get_path_name()==r['water_material']
assert actors['OH_Finish_FocalSun'].get_component_by_class(u.SpotLightComponent).intensity==2800000
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,actors=len(actors),all_transforms_and_meshes_preserved=True,plants=len(r['plants']),pillars=len(r['pillars']),playtest=False),indent=2));u.log('HALL_COLOR_MASSES_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v022').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',r['map']).replace('unreal_exposure_fixed.png','unreal_color_masses.png').replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_color_masses','exec'),globals())
