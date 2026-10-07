"""Create the conversation review map without overwriting existing maps."""
import unreal as u
asset=u.SceneDirectorLibrary.create_conversation_example()
if not asset:
    raise RuntimeError('Conversation example creation failed')
for graph in [asset, asset.find_event('ExistingActors')]:
    message = u.SceneDirectorLibrary.compile_director(graph)
    if graph.get_editor_property('needs_compile'):
        raise RuntimeError(message)
u.EditorAssetLibrary.save_loaded_asset(asset)
path='/Game/SceneDirector/Examples/L_Conversation'
if not u.EditorAssetLibrary.does_asset_exist(path):
    if not u.EditorLevelLibrary.new_level(path):
        raise RuntimeError('Conversation map creation failed')
    ground=u.EditorLevelLibrary.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,-10))
    ground.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
    ground.set_actor_scale3d(u.Vector(20,20,.2))
    ground.set_actor_label('Conversation_Ground')
    light=u.EditorLevelLibrary.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,500),u.Rotator(-35,180,0))
    light.light_component.set_mobility(u.ComponentMobility.MOVABLE)
    u.EditorLevelLibrary.get_editor_world().get_world_settings().set_editor_property('default_game_mode',u.GameModeBase)
    start=u.EditorLevelLibrary.spawn_actor_from_class(u.PlayerStart,u.Vector(-450,0,120))
    runner=u.EditorLevelLibrary.spawn_actor_from_class(u.SceneDirectorPlayer,u.Vector(0,0,0))
    runner.set_editor_property('director',asset)
    runner.set_actor_label('Conversation_Director')
    if not u.EditorLevelLibrary.save_current_level():
        raise RuntimeError('Conversation map save failed')
u.log('SCENE_DIRECTOR_CONVERSATION_READY '+asset.get_path_name())
