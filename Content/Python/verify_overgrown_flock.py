import unreal as u, json
from pathlib import Path
P=globals().get('FLOCK_DEST','/Game/Environment/OvergrownHall/Production')
map_path=P+'/Maps/'+globals().get('FLOCK_MAP','L_OvergrownHall_Detail')
E=u.EditorAssetLibrary; L=u.get_editor_subsystem(u.LevelEditorSubsystem); A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert E.does_asset_exist(P+'/Sequences/LS_OvergrownHall_Flock'), 'Flock sequence missing'
assert L.load_level(map_path)
seq=E.load_asset(P+'/Sequences/LS_OvergrownHall_Flock')
birds=[a for a in A.get_all_level_actors() if a.get_actor_label().startswith('OH_Flock_Bird_')]
players=[a for a in A.get_all_level_actors() if a.get_actor_label()=='OH_Flock_Sequence']
assert len(birds)==12 and len(players)==1,(len(birds),len(players))
settings=players[0].get_editor_property('playback_settings')
assert settings.auto_play and settings.loop_count.value==-1
assert players[0].get_sequence()==seq
assert len(seq.get_bindings())==12
for b in birds:
    c=b.skeletal_mesh_component
    assert '/Bird/Tripo/' in c.get_skeletal_mesh_asset().get_path_name()
    assert str(c.get_collision_profile_name())=='NoCollision'
for binding in seq.get_bindings():
    tracks=binding.get_tracks()
    assert len(tracks)==2
    for track in tracks:
        assert track.get_sections()
        if isinstance(track,u.MovieScene3DTransformTrack):
            channels=track.get_sections()[0].get_all_channels()
            assert len(channels)>=9
            for channel in channels[:6]: assert len(channel.get_keys())>=121
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
runtime,temp_actor=u.LevelSequencePlayer.create_level_sequence_player(world,seq,u.MovieSceneSequencePlaybackSettings())
before={a.get_actor_label():a.get_actor_location() for a in birds}
params=u.MovieSceneSequencePlaybackParams(); params.frame=u.FrameTime(u.FrameNumber(240)); params.position_type=u.MovieScenePositionType.FRAME; params.update_method=u.UpdatePositionMethod.JUMP
runtime.set_playback_position(params)
moved=[(a.get_actor_location()-before[a.get_actor_label()]).length() for a in birds]
assert min(moved)>100,moved
out=dict(status='saved_flock_structure_and_evaluation_pass',birds=len(birds),autoplay=True,infinite_loop=True,evaluated_frame=240,min_actor_displacement_cm=min(moved),sequence=seq.get_path_name(),map=map_path,visual_playtest='not_run')
folder=Path(globals().get('FLOCK_OUT',Path(u.Paths.project_dir())/'ArtSource/OvergrownHall/Bird/Flock_v001')); folder.mkdir(exist_ok=True)
(folder/'unreal_saved_verification.json').write_text(json.dumps(out,indent=2))
u.log('FLOCK_SAVED_PASS '+json.dumps(out))
