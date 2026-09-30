from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v021';r=load_current_json((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(r['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};baseline=load_current_json((OUT/'baseline.json').read_text())
for n in r['changed_meshes']:assert actors[n].static_mesh_component.static_mesh.get_name().startswith('SM_OH_Fractured')
for n in r['added']:
    a=actors[n];assert a.static_mesh_component.get_collision_profile_name()=='NoCollision';center,extent=a.get_actor_bounds(False);assert center.z-extent.z>700
assert len([n for n in actors if n.startswith('OH_ClosedRoof_')])==50
assert len(actors)==len(baseline)+len(r['added'])
for n,b in baseline.items():
    if n.startswith('OH_Flock_Bird_'):continue
    a=actors[n];p=a.get_actor_location();s=a.get_actor_scale3d();rot=a.get_actor_rotation()
    for expected,actual in [(b['position'],[p.x,p.y,p.z]),(b['scale'],[s.x,s.y,s.z]),(b['rotation'],[rot.pitch,rot.yaw,rot.roll])]:assert all(abs(v-w)<.001 for v,w in zip(expected,actual)),n
    if b.get('mesh') and n not in r['changed_meshes']:assert a.static_mesh_component.static_mesh.get_path_name()==b['mesh'],n
for n,scale in r['bird_scales'].items():assert abs(actors[n].get_actor_scale3d().x-scale)<.001
seq=u.EditorAssetLibrary.load_asset('/Game/Constellation/Environments/OvergrownHall/TripoFull/Sequences/LS_OvergrownHall_Flock');assert len(seq.get_bindings())==28 and seq.get_playback_end()==960
for binding in seq.get_bindings():
    track=next(t for t in binding.get_tracks() if isinstance(t,u.MovieSceneSkeletalAnimationTrack));assert len(track.get_sections())==5
    for section in track.get_sections():assert section.get_editor_property('params').animation
    t=next(t for t in binding.get_tracks() if isinstance(t,u.MovieScene3DTransformTrack))
    for c in t.get_sections()[0].get_all_channels()[6:9]:assert all(abs(k.get_value()-r['bird_scales'][binding.get_name()])<.001 for k in c.get_keys())
for n in load_current_json((OUT.parent/'v015/applied.json').read_text())['removed']:assert n not in actors
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,changed_meshes=len(r['changed_meshes']),hanging_members=len(r['added']),birds=28,animation_sections=140,closed_roof=50,other_transforms_preserved=True,playtest=False),indent=2));u.log('HALL_SILHOUETTES_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v021').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',r['map']).replace('unreal_exposure_fixed.png','unreal_silhouettes.png').replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_silhouettes','exec'),globals())
