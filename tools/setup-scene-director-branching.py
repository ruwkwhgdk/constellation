import unreal as u
asset=u.SceneDirectorLibrary.create_branching_example()
assert asset, 'Branching example creation failed'
u.SceneDirectorLibrary.compile_director(asset)
assert not asset.get_editor_property('needs_compile')
source='/Game/SceneDirector/Examples/L_Conversation'
target='/Game/SceneDirector/Examples/L_Branching'
if not u.EditorAssetLibrary.does_asset_exist(target):
    assert u.EditorAssetLibrary.duplicate_asset(source,target)
world=u.EditorLoadingAndSavingUtils.load_map(target)
assert world
sub=u.get_editor_subsystem(u.EditorActorSubsystem)
players=[a for a in sub.get_all_level_actors() if isinstance(a,u.SceneDirectorPlayer)]
assert len(players)==1, 'Expected a single director player'
players[0].set_editor_property('director',asset)
players[0].set_editor_property('event_key',u.Name('None'))
players[0].set_editor_property('auto_play',True)
assert u.EditorLoadingAndSavingUtils.save_map(world,target)
assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
u.log('BRANCHING_EXAMPLE_READY '+asset.get_path_name()+' '+target)
