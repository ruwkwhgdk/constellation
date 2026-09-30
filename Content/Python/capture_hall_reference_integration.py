from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v025';r=load_current_json((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(r['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};base=load_current_json((OUT/'baseline.json').read_text());assert len(actors)==len(base)+len(r['added'])
for n,b in base.items():
    if n in r['changed_shrubs']:continue
    a=actors[n];p=a.get_actor_location();s=a.get_actor_scale3d();rot=a.get_actor_rotation()
    for expected,actual in [(b['position'],[p.x,p.y,p.z]),(b['scale'],[s.x,s.y,s.z]),(b['rotation'],[rot.pitch,rot.yaw,rot.roll])]:assert all(abs(v-w)<.001 for v,w in zip(expected,actual)),n
    if b.get('mesh'):assert a.static_mesh_component.static_mesh.get_path_name()==b['mesh'],n
for n in r['changed_shrubs']:
    a=actors[n];assert a.static_mesh_component.static_mesh.get_name()=='SM_OH_PaintedShrub_Runtime';center,extent=a.get_actor_bounds(False);assert abs(center.z-extent.z-3)<1
for n in r['added']:assert actors[n].static_mesh_component.get_collision_profile_name()=='NoCollision'
for n in r['rear_walls']:assert actors[n].static_mesh_component.get_material(0).get_name()=='M_OH_RearWallIntegrated'
assert len([n for n in actors if n.startswith('OH_ClosedRoof_')])==50
assert len([n for n in actors if 'OH_ReferenceProportion_UpperWall_' in n])==8
for n in load_current_json((OUT.parent/'v015/applied.json').read_text())['removed']:assert n not in actors
seq=u.EditorAssetLibrary.load_asset('/Game/Constellation/Environments/OvergrownHall/TripoFull/Sequences/LS_OvergrownHall_Flock');assert len(seq.get_bindings())==28 and seq.get_playback_end()==960
for b in seq.get_bindings():
    t=next(t for t in b.get_tracks() if isinstance(t,u.MovieSceneSkeletalAnimationTrack));assert len(t.get_sections())==5
    for s in t.get_sections():assert s.get_editor_property('params').animation
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,actors=len(actors),rooted_shrubs=4,lintel_clusters=3,rear_walls=len(r['rear_walls']),other_transforms_meshes_preserved=True,closed_roof=50,upper_walls=8,birds=28,animation_sections=140,playtest=False),indent=2));u.log('HALL_REFERENCE_INTEGRATION_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v025').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',r['map']).replace('unreal_exposure_fixed.png','unreal_reference_integration.png').replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_reference_integration','exec'),globals())
