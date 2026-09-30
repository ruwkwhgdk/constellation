from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v009';D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(MAP)
report=load_current_json((OUT/'applied.json').read_text());actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
for p in report['added']:
    a=actors[p['label']];assert a.static_mesh_component.static_mesh.get_path_name()==p['mesh'];assert a.static_mesh_component.get_collision_profile_name()=='NoCollision'
assert len([n for n in actors if n.startswith(('OH_FULL_','OH_Tripo_Tree_','OH_STRUCTURE_Roof_'))])==532
assert len([n for n in actors if n.startswith('OH_Growth_')])==53
birds=28 if report['stage']==2 else 12
flock=(ROOT/'Content/Python/verify_overgrown_flock.py').read_text().replace('==12','=='+str(birds))
exec(compile(flock,'verify_reference_flock','exec'),dict(FLOCK_DEST=D,FLOCK_MAP='L_OvergrownHall_TripoFull',FLOCK_OUT=OUT/'Flock'))
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
if report['stage']==2:
    for n in report['chipped']:assert actors[n].static_mesh_component.static_mesh.get_name().startswith('SM_OH_Chipped_')
    assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.static_mesh.get_name()=='SM_OH_ShallowOutline'
    assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.get_material(0).get_name()=='M_OH_QuietWater'
    center,extent=actors['OH_SM_OH_Blockout_21'].get_actor_bounds(False)
    assert abs(center.y-700)<1 and extent.y>850,(center,extent)
    base=load_current_json((OUT/'baseline.json').read_text())
    for n in report['submerged_floor_tiles']:
        assert abs(actors[n].get_actor_location().z-(base[n]['position'][2]-1))<.01,n
    for n,a in actors.items():
        if n.startswith('OH_Flock_Bird_'):assert .47<a.get_actor_scale3d().x<.69,n
    assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.get_collision_profile_name()=='NoCollision'
assert 'OH_WaterPlanarReflection' in actors
(OUT/'verification.json').write_text(json.dumps(dict(stage=report['stage'],existing=532,growth=53,added=len(report['added']),birds=birds,flock_evaluation=True,water_bounds_and_floor_heights=report['stage']==2,bird_scale_verified=report['stage']==2,playtest=False),indent=2))
u.log('HALL_REFERENCE_VERIFIED')
filename='unreal_forest.png' if report['stage']==1 else 'unreal_reference.png'
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v009').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',MAP).replace('unreal_exposure_fixed.png',filename)
script=script.replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next")
script=script.replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_reference','exec'),globals())
