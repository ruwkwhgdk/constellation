from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v019';report=load_current_json((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(report['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
for n in report['removed_shrubs']:assert n not in actors
for n in report['added']:assert actors[n].static_mesh_component.get_collision_profile_name()=='NoCollision'
for n in report['spalled_pillars']:assert actors[n].static_mesh_component.static_mesh.get_name().startswith('SM_OH_SpalledPillar')
for n in report['reshaped_shrubs']:assert actors[n].static_mesh_component.static_mesh.get_name()=='SM_OH_PaintedShrub_Runtime'
assert len([n for n in actors if n.startswith('OH_ClosedRoof_')])==50
for n in load_current_json((OUT.parent/'v015/applied.json').read_text())['removed']:assert n not in actors
cam=actors['OH_ReferenceCamera'];p=cam.get_actor_location();assert [round(p.x),round(p.y),round(p.z)]==[0,100,112];assert abs(cam.get_component_by_class(u.CameraComponent).field_of_view-72.7)<.001
light=actors['OH_Finish_FocalSun'];assert (light.get_actor_location()-cam.get_actor_location()).dot(cam.get_actor_right_vector())>0
assert light.get_component_by_class(u.SpotLightComponent).get_editor_property('intensity')==1450000
assert actors['OH_WindowFill'].get_component_by_class(u.RectLightComponent).get_editor_property('intensity')==110000
assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.get_material(0).get_path_name()==report['water_material']
assert actors['OH_Painterly_DistantHaze_000'].static_mesh_component.get_material(0).get_name()=='M_OH_ReferenceHaze'
assert len([n for n in actors if n.startswith('OH_Flock_Bird_')])==28
routes=load_current_json((OUT/'Flock/routes.json').read_text());assert routes['minimum_center_distance_cm']>15
seq=u.EditorAssetLibrary.load_asset('/Game/Constellation/Environments/OvergrownHall/TripoFull/Sequences/LS_OvergrownHall_Flock');assert len(seq.get_bindings())==28 and seq.get_playback_end()==960
for binding in seq.get_bindings():
    tracks=[t for t in binding.get_tracks() if isinstance(t,u.MovieSceneSkeletalAnimationTrack)];assert len(tracks)==1
    assert len(tracks[0].get_sections())==5
    for section in tracks[0].get_sections():assert section.get_editor_property('params').animation
assert len(actors)==744
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,camera_v018=True,screen_right_light=True,roof_count=50,rear_trees_absent=True,added=len(report['added']),removed_shrubs=len(report['removed_shrubs']),reshaped_shrubs=len(report['reshaped_shrubs']),spalled_pillars=len(report['spalled_pillars']),trimmed_bases_caps=len(report['trimmed_bases_caps']),birds=28,minimum_bird_spacing_cm=routes['minimum_center_distance_cm'],playtest='user'),indent=2));u.log('HALL_REFERENCE_FINISH_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v019').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',report['map']).replace('unreal_exposure_fixed.png','unreal_reference_finish.png').replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_reference_finish','exec'),globals())
