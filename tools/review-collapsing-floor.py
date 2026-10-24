"""Read saved floor settings and exercise its real overlap/break in PIE. Never saves the map."""
import json, time, traceback
from pathlib import Path
import unreal as u

OUT = Path(u.Paths.project_dir()) / 'Saved/Checks/CollapsingFloor_20261020/Play'
OUT.mkdir(parents=True, exist_ok=True)
report = {'checks': [], 'samples': []}
start = time.monotonic()
state = {'phase': 'startup', 'elapsed': 0, 'shots': set()}

def check(name, passed):
    report['checks'].append({'name': name, 'passed': bool(passed)})
    assert passed, name

def finish(error=None):
    if error:
        report['error'] = error
    (OUT / 'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    u.log('FLOOR_REVIEW_RESULT ' + json.dumps(report['checks']))
    if 'token' in globals():
        u.unregister_slate_post_tick_callback(token)
    u.SystemLibrary.quit_editor()

try:
    assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    floor = next(a for a in actors if a.get_name() == 'BP_Break_Floor_C_6')
    gc = floor.get_component_by_class(u.GeometryCollectionComponent)
    report['saved_profiles'] = [str(v) for v in gc.get_editor_property('collision_profile_per_level')]
    report['floor_transform'] = str(floor.get_actor_transform())
    check('Saved placed floor blocks Pawn after fracture', report['saved_profiles'] == ['None', 'Destructible'])
    check('Shrink on removal retained', gc.rest_collection.get_editor_property('scale_on_removal'))
    check('Sleep removal retained', gc.rest_collection.get_editor_property('remove_on_max_sleep'))
    u.CarryEditorLibrary.start_carry_review_play()
except Exception:
    finish(traceback.format_exc())
    raise

def tick(dt):
    try:
        if time.monotonic() - start > 150:
            raise RuntimeError('Review timeout')
        pawn = u.CarryEditorLibrary.get_carry_review_pawn()
        if not pawn:
            return
        if state['phase'] == 'startup':
            world = pawn.get_world()
            live = next(a for a in u.GameplayStatics.get_all_actors_of_class(world, floor.get_class()) if a.get_name() == floor.get_name())
            component = live.get_component_by_class(u.GeometryCollectionComponent)
            origin, extent = u.SystemLibrary.get_component_bounds(component)[:2]
            state.update(phase='settle', elapsed=0, floor=live, gc=component, origin=origin, extent=extent, pawn=pawn)
            report['bounds'] = {'origin': str(origin), 'extent': str(extent)}
            # Approach from above so the actual capsule overlap initiates the existing Blueprint.
            pawn.set_actor_location(u.Vector(origin.x, origin.y, origin.z + extent.z + 200), False, True)
            pc = u.GameplayStatics.get_player_controller(world, 0)
            pc.set_control_rotation(u.Rotator(pitch=-35, yaw=0))
        state['elapsed'] += dt
        gc_live = state['gc']
        transforms = gc_live.get_current_transforms()
        scales = [t.scale3d.x for t in transforms]
        broken = gc_live.is_root_broken()
        if broken and 'break_time' not in state:
            state['break_time'] = state['elapsed']
        age = state['elapsed'] - state.get('break_time', state['elapsed'])
        origin, extent = state['origin'], state['extent']
        # Trace the actual moving pieces, not an intact proxy floor.
        hits = 0
        hit_details = []
        hit_scales = []
        for xoff in (-.5, 0, .5):
            for yoff in (-.5, 0, .5):
                x, y = origin.x + extent.x*xoff, origin.y + extent.y*yoff
                hit = gc_live.line_trace_component(u.Vector(x,y,origin.z+extent.z+100), u.Vector(x,y,origin.z-3000), False, False, False)
                hits += int(bool(hit))
                if hit:
                    hit_details.append(str(hit))
                    hit_scales.append(gc_live.get_socket_transform(hit[2], u.RelativeTransformSpace.RTS_WORLD).scale3d.x)
        if not report['samples'] or state['elapsed'] - report['samples'][-1]['time'] > .1:
            report['samples'].append({'time': state['elapsed'], 'broken': broken, 'age': age, 'hits': hits,
                                      'min_scale': min(scales) if scales else None,
                                      'max_scale': max(scales) if scales else None,
                                      'scales': scales, 'hit_details': hit_details, 'hit_scales': hit_scales,
                                      'movement_base': str(pawn.get_movement_base()) if hasattr(pawn, 'get_movement_base') else None,
                                      'pawn': str(pawn.get_actor_location()), 'velocity': str(pawn.get_velocity())})
        for name, threshold in [('before',0),('broken',.1),('shrinking',1.5),('removed',5)]:
            if name not in state['shots'] and ((name=='before' and not broken) or (broken and age>=threshold)):
                u.CarryEditorLibrary.capture_carry_review(str(OUT/(name+'.png')),False)
                state['shots'].add(name)
                break
        if broken and age > 14 and (hits == 0 or age > 40):
            check('Actual player overlap broke the floor', True)
            check('Broken pieces retain trace collision', any(s['broken'] and .05<s['age']<1 and s['hits']>0 for s in report['samples']))
            check('Pieces shrink during removal', any(s['broken'] and s['min_scale'] is not None and 0<s['min_scale']<.95 for s in report['samples']))
            report['final_hit_details'] = hit_details
            report['trace_doc'] = gc_live.line_trace_component.__doc__
            check('Collision decreases as pieces disappear', hits < max(s['hits'] for s in report['samples']))
            check('No fully disappeared piece blocks sampled traces',
                  all(v > .0001 for s in report['samples'] for v in s['hit_scales']))
            report['remaining_visible_piece_hits'] = hits
            finish()
        elif state['elapsed']>25 and not broken:
            raise RuntimeError('Player did not trigger floor fracture')
    except Exception:
        finish(traceback.format_exc())

u.EditorPythonScripting.set_keep_python_script_alive(True)
token = u.register_slate_post_tick_callback(tick)
