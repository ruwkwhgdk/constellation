"""Run inside Unreal Editor after the QTE plugin build. Creates isolated review assets only.
Four real QTE decisions rejoin the next prompt on either outcome. The first camera move
continues under the first timed prompt. No production map or scene is modified.
"""
import unreal as u
import uuid

ROOT = '/Game/SceneDirector/Examples/QTE'
ASSET = ROOT + '/DA_QTE_Example'
MAP = ROOT + '/L_QTE_Review'
assert not u.EditorAssetLibrary.does_asset_exist(ASSET), 'Review asset already exists; inspect it instead of overwriting.'
assert not u.EditorAssetLibrary.does_asset_exist(MAP), 'Review map already exists; inspect it instead of overwriting.'

def guid():
    v = uuid.uuid4().int
    values = [(v >> shift) & 0xffffffff for shift in (96, 64, 32, 0)]
    return u.Guid(*[x if x < 0x80000000 else x - 0x100000000 for x in values])

def step(kind, x, y=0):
    s = u.DirectorStep()
    s.set_editor_property('id', guid())
    s.set_editor_property('type', kind)
    s.set_editor_property('editor_position', u.Vector2D(x, y))
    return s

def link(a, b):
    a.set_editor_property('next_nodes', [b.get_editor_property('id')])

factory = u.DataAssetFactory()
factory.set_editor_property('data_asset_class', u.SceneDirectorAsset)
asset = u.AssetToolsHelpers.get_asset_tools().create_asset('DA_QTE_Example', ROOT, u.SceneDirectorAsset, factory)
assert asset
steps = [step(u.DirectorNodeType.START, 0)]
move = step(u.DirectorNodeType.CAMERA_MOVE, 220)
move.set_editor_property('camera_key', 'ReviewCamera')
move.set_editor_property('duration', 8.0)
move.set_editor_property('wait_for_completion', False)
destination = move.get_editor_property('destination')
destination.set_editor_property('value', u.Vector(-650, 160, 160))
move.set_editor_property('destination', destination)
steps.append(move)
link(steps[0], move)
last = move
success_sound = u.load_asset('/Game/Constellation/UI/AbilityAcquisition/S_StarChime')
failure_sound = u.load_asset('/Game/Constellation/UI/AbilityAcquisition/S_Dismiss')
for index, kind in enumerate([u.DirectorQTEType.SINGLE_CLICK, u.DirectorQTEType.REPEAT_CLICK, u.DirectorQTEType.DIRECTION_DRAG, u.DirectorQTEType.TRACE_PATH]):
    x = 480 + index * 720
    prompt = step(u.DirectorNodeType.QTE, x)
    settings = prompt.get_editor_property('qte')
    settings.set_editor_property('type', kind)
    settings.set_editor_property('timed', True)
    settings.set_editor_property('time_limit', 6.0)
    settings.set_editor_property('scene_policy', u.DirectorQTEScenePolicy.CONTINUE if index == 0 else u.DirectorQTEScenePolicy.HOLD)
    settings.set_editor_property('success_sound', success_sound)
    settings.set_editor_property('failure_sound', failure_sound)
    prompt.set_editor_property('qte', settings)
    good = step(u.DirectorNodeType.WAIT, x + 240, -150)
    bad = step(u.DirectorNodeType.WAIT, x + 240, 150)
    good.set_editor_property('duration', .6)
    bad.set_editor_property('duration', .9)
    join = step(u.DirectorNodeType.HUB, x + 480)
    prompt.set_editor_property('choice_targets', {u.Name('Success'): good.get_editor_property('id'), u.Name('Failure'): bad.get_editor_property('id')})
    link(last, prompt); link(good, join); link(bad, join)
    steps.extend([prompt, good, bad, join]); last = join
end = step(u.DirectorNodeType.END, 3500)
link(last, end);steps.append(end)
asset.set_editor_property('steps', steps)
cam = u.DirectorCameraEntry()
cam.set_editor_property('key', 'ReviewCamera')
cam.set_editor_property('transform', u.Transform(location=u.Vector(-650, -160, 160)))
asset.set_editor_property('cameras', [cam])
u.SceneDirectorLibrary.compile_director(asset)
assert not asset.get_editor_property('needs_compile'), 'QTE example compile failed'
assert u.EditorAssetLibrary.save_loaded_asset(asset, False)
assert u.EditorLevelLibrary.new_level(MAP)
sub = u.get_editor_subsystem(u.EditorActorSubsystem)
ground = sub.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, 0, -30))
ground.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
ground.set_actor_scale3d(u.Vector(25, 25, .25))
for y in (-250, 0, 250):
    marker = sub.spawn_actor_from_class(u.StaticMeshActor, u.Vector(0, y, 100))
    marker.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cylinder'))
    marker.set_actor_scale3d(u.Vector(1, 1, 2))
sub.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 500), u.Rotator(-40, -30, 0))
sub.spawn_actor_from_class(u.SkyLight, u.Vector(0, 0, 300))
sub.spawn_actor_from_class(u.PlayerStart, u.Vector(-650, 0, 160))
runner = sub.spawn_actor_from_class(u.SceneDirectorPlayer, u.Vector())
runner.set_editor_property('director', asset)
runner.set_editor_property('auto_play', True)
runner.set_actor_label('QTE Review Player')
assert u.EditorLevelLibrary.save_current_level()
u.log('QTE_REVIEW_READY ' + ASSET + ' ' + MAP)
