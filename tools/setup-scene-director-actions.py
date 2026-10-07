import unreal as u
asset = u.SceneDirectorLibrary.create_actions_example()
assert asset, 'Action example creation failed'
u.SceneDirectorLibrary.compile_director(asset)
assert not asset.get_editor_property('needs_compile')
source = '/Game/SceneDirector/Examples/L_Branching'
target = '/Game/SceneDirector/Examples/L_Actions'
if not u.EditorAssetLibrary.does_asset_exist(target):
    assert u.EditorAssetLibrary.duplicate_asset(source, target)
world = u.EditorLoadingAndSavingUtils.load_map(target)
assert world
sub = u.get_editor_subsystem(u.EditorActorSubsystem)
players = [a for a in sub.get_all_level_actors() if isinstance(a, u.SceneDirectorPlayer)]
assert len(players) == 1
players[0].set_editor_property('director', asset)
players[0].set_editor_property('event_key', u.Name('None'))
players[0].set_editor_property('auto_play', True)
assert u.EditorLoadingAndSavingUtils.save_map(world, target)
assert u.EditorAssetLibrary.save_loaded_asset(asset, False)
for name in ('BP_ActionSetNPCTag', 'BP_ActionAcceptQuest'):
    bp = u.EditorAssetLibrary.load_asset('/Game/SceneDirector/Examples/' + name)
    assert bp
u.log('ACTIONS_EXAMPLE_READY ' + asset.get_path_name() + ' ' + target)
