"""Read-only render isolation. Never save the map or any assets."""
import unreal as u
import hashlib, json, time, traceback
from pathlib import Path

R = Path(u.Paths.project_dir())
O = R / 'Saved/S0WetFloor/JunctionIsolation_20261019'
O.mkdir(parents=True, exist_ok=True)
assert not (O / 'session.json').exists(), 'Use a fresh evidence directory'
mapfile = R / 'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
before = hashlib.sha256(mapfile.read_bytes()).hexdigest()
(O / 'session.json').write_text(json.dumps({'map_sha256': before}))
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A = u.get_editor_subsystem(u.EditorActorSubsystem)
actors = {a.get_name(): a for a in A.get_all_level_actors()}
protected = json.loads((R / 'ArtSource/SchoolOpening/WetFloor/PROTECTED_LAYOUT.json').read_text())
for row in protected['actors']:
    p = actors[row['name']].get_actor_location()
    assert all(abs(x-y) < .01 for x,y in zip((p.x,p.y,p.z),row['position_cm']))

names = ['StaticMeshActor_797', 'StaticMeshActor_788', 'StaticMeshActor_795',
         'StaticMeshActor_812', 'StaticMeshActor_818', 'StaticMeshActor_831']
targets = [actors[n] for n in names]
original = {a.get_name(): a.is_temporarily_hidden_in_editor() for a in targets}
phases = [('baseline', [])] + [('hide-'+n, [n]) for n in names] + [('hide-all', names)]
cam = A.spawn_actor_from_class(u.CameraActor, u.Vector(2600,900,700), u.Rotator(pitch=0,yaw=110), transient=True)
cam.camera_component.set_field_of_view(83)
u.EditorLevelLibrary.pilot_level_actor(cam)
u.EditorLevelLibrary.editor_set_game_view(True)
u.EditorPythonScripting.set_keep_python_script_alive(True)
state = {'i':0, 'start':0, 'sent':False, 'busy':False}

def finish(error=None):
    for a in targets:
        a.set_is_temporarily_hidden_in_editor(original[a.get_name()])
    unchanged = hashlib.sha256(mapfile.read_bytes()).hexdigest() == before
    (O / 'result.json').write_text(json.dumps({'map_unchanged':unchanged,'error':error,'phases':phases},indent=2))
    u.unregister_slate_post_tick_callback(handle)
    u.SystemLibrary.quit_editor()

def tick(dt):
    if state['busy']: return
    state['busy'] = True
    try:
        if state['i'] >= len(phases):
            finish(); return
        label, hidden = phases[state['i']]
        path = O / (label+'.png')
        if not state['start']:
            for a in targets:
                a.set_is_temporarily_hidden_in_editor(a.get_name() in hidden or original[a.get_name()])
            state['start'] = time.monotonic()
        if state['sent'] and path.exists() and path.stat().st_size:
            state.update(i=state['i']+1,start=0,sent=False); return
        elapsed = time.monotonic()-state['start']
        if elapsed > 120: raise RuntimeError('Screenshot timed out: '+label)
        if elapsed > 12 and not state['sent']:
            u.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),camera=cam,delay=1)
            state['sent'] = True
    except Exception:
        finish(traceback.format_exc())
    finally:
        state['busy'] = False

handle = u.register_slate_post_tick_callback(tick)
