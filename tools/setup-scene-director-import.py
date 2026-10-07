import unreal as u
asset = u.SceneDirectorLibrary.create_import_example()
assert asset, 'Import example failed'
result = u.SceneDirectorLibrary.compile_director(asset)
assert not asset.get_editor_property('needs_compile'), result
target = '/Game/SceneDirector/Examples/L_ImportedPerformance'
if not u.EditorAssetLibrary.does_asset_exist(target):
    assert u.EditorAssetLibrary.duplicate_asset('/Game/SceneDirector/Examples/L_SequenceReuse', target)
world = u.EditorLoadingAndSavingUtils.load_map(target)
assert world
players = [a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a, u.SceneDirectorPlayer)]
assert len(players) == 1
players[0].set_editor_property('director', asset)
players[0].set_editor_property('event_key', u.Name('None'))
players[0].set_editor_property('auto_play', True)
assert u.EditorLoadingAndSavingUtils.save_map(world, target)
assert u.EditorAssetLibrary.save_loaded_asset(asset, False)
u.log('DIRECTOR_IMPORT_READY ' + asset.get_path_name())
