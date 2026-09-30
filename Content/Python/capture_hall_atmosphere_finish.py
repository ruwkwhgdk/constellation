from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v020';r=load_current_json((OUT/'applied.json').read_text());L=u.get_editor_subsystem(u.LevelEditorSubsystem);assert L.load_level(r['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
for n in r['removed']:assert n not in actors
for n in load_current_json((OUT.parent/'v015/applied.json').read_text())['removed']:assert n not in actors
assert len([n for n in actors if n.startswith('OH_ClosedRoof_')])==50
assert len([n for n in actors if n.startswith('OH_Flock_Bird_')])==28
cam=actors['OH_ReferenceCamera'];p=cam.get_actor_location();assert [p.x,p.y,p.z]==[0,100,112];assert abs(cam.get_component_by_class(u.CameraComponent).field_of_view-72.7)<.001
assert actors['OH_Sun'].get_component_by_class(u.DirectionalLightComponent).intensity==5000
assert actors['OH_Finish_FocalSun'].get_component_by_class(u.SpotLightComponent).intensity==2200000
assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.get_material(0).get_path_name()==r['water_material']
assert actors['OH_WaterPlanarReflection'].get_component_by_class(u.PlanarReflectionComponent).get_editor_property('normal_distortion_strength')<.13
assert actors[r['new_light']].get_component_by_class(u.RectLightComponent).intensity==28000
baseline=load_current_json((OUT/'baseline.json').read_text());assert len(actors)==len(baseline)-len(r['removed'])+1
changed=set(r['removed']+r['reshaped']+r['wall_clusters']+['OH_Finish_FocalSun'])
preserved=0
for n,b in baseline.items():
    if n in changed:continue
    a=actors[n];p=a.get_actor_location();s=a.get_actor_scale3d();rot=a.get_actor_rotation()
    for expected,actual in [(b['position'],[p.x,p.y,p.z]),(b['scale'],[s.x,s.y,s.z]),(b['rotation'],[rot.pitch,rot.yaw,rot.roll])]:assert all(abs(v-w)<.001 for v,w in zip(expected,actual)),n
    if b.get('mesh'):assert a.static_mesh_component.static_mesh.get_path_name()==b['mesh'],n
    preserved+=1
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,actors=len(actors),removed_shrubs=len(r['removed']),reshaped_shrubs=len(r['reshaped']),wall_clusters=len(r['wall_clusters']),camera_preserved=True,closed_roof=50,birds=28,playtest=False),indent=2));u.log('HALL_ATMOSPHERE_FINISH_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v020').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',r['map']).replace('unreal_exposure_fixed.png','unreal_atmosphere_finish.png').replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_atmosphere_finish','exec'),globals())
