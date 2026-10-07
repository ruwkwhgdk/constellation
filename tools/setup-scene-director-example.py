"""Creates only /Game/SceneDirector/Examples assets; never overwrites an existing map."""
import unreal as u
asset = u.SceneDirectorLibrary.create_example()
if not asset:
    raise RuntimeError('Scene Director example creation failed')
map_path = '/Game/SceneDirector/Examples/L_FirstScene'
if not u.EditorAssetLibrary.does_asset_exist(map_path):
    if not u.EditorLevelLibrary.new_level(map_path):
        raise RuntimeError('Example map creation failed')
    ground = u.EditorLevelLibrary.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, -20))
    ground.set_actor_label('SceneDirector_Ground')
    ground.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
    ground.set_actor_scale3d(u.Vector(20, 20, 0.2))
    sun = u.EditorLevelLibrary.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 500), u.Rotator(-45, -25, 0))
    sun.set_actor_label('SceneDirector_Light')
    player = u.EditorLevelLibrary.spawn_actor_from_class(u.SceneDirectorPlayer, u.Vector(0, 0, 0))
    player.set_editor_property('director', asset)
    player.set_actor_label('SceneDirector_ExamplePlayer')
    start = u.EditorLevelLibrary.spawn_actor_from_class(u.PlayerStart, u.Vector(-600, 0, 150), u.Rotator(0, 0, 0))
    if not u.EditorLevelLibrary.save_current_level():
        raise RuntimeError('Example map save failed')
u.log('SCENE_DIRECTOR_EXAMPLE_READY ' + asset.get_path_name())
