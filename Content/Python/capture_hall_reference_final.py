from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v023';r=load_current_json((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(r['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};base=load_current_json((OUT/'baseline.json').read_text());assert len(actors)==len(base)+len(r['added'])
for n,b in base.items():
    a=actors[n];p=a.get_actor_location();s=a.get_actor_scale3d();rot=a.get_actor_rotation()
    expected_position=[1600 if b['position'][0]>0 else -1600,b['position'][1],b['position'][2]] if n in r['moved_side_trees'] else b['position']
    for expected,actual in [(expected_position,[p.x,p.y,p.z]),(b['scale'],[s.x,s.y,s.z]),(b['rotation'],[rot.pitch,rot.yaw,rot.roll])]:assert all(abs(v-w)<.001 for v,w in zip(expected,actual)),n
    if b.get('mesh'):assert a.static_mesh_component.static_mesh.get_path_name()==b['mesh'],n
for n in r['added']:
    c=actors[n].static_mesh_component;assert c.get_collision_profile_name()=='NoCollision';center,extent=actors[n].get_actor_bounds(False);assert abs(center.y+extent.y-1960)<1;assert center.z-extent.z<16
assert len([n for n in actors if n.startswith('OH_ClosedRoof_')])==50
for n in load_current_json((OUT.parent/'v015/applied.json').read_text())['removed']:assert n not in actors
assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.get_material(0).get_path_name()==r['water_material']
assert actors['OH_Painterly_DistantHaze_000'].static_mesh_component.get_material(0).get_name()=='M_OH_FinalBackdrop'
seq=u.EditorAssetLibrary.load_asset('/Game/Constellation/Environments/OvergrownHall/TripoFull/Sequences/LS_OvergrownHall_Flock');assert len(seq.get_bindings())==28 and seq.get_playback_end()==960
for b in seq.get_bindings():
    t=next(t for t in b.get_tracks() if isinstance(t,u.MovieSceneSkeletalAnimationTrack));assert len(t.get_sections())==5
    for s in t.get_sections():assert s.get_editor_property('params').animation
light=actors['OH_Finish_FocalSun'].get_component_by_class(u.SpotLightComponent);assert light.intensity==2200000;assert abs(light.get_editor_property('volumetric_scattering_intensity')-4.3)<.001
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,actors=len(actors),unrelated_transforms_and_all_meshes_preserved=True,moved_side_trees=len(r['moved_side_trees']),wall_growth=len(r['added']),closed_roof=50,birds=28,animation_sections=140,rear_trees_absent=True,playtest=False),indent=2));u.log('HALL_REFERENCE_FINAL_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v023').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',r['map']).replace('unreal_exposure_fixed.png','unreal_reference_final.png').replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_reference_final','exec'),globals())
