"""Read-only PIE contact/data audit of the broad school rock ramps."""
import unreal as u
import time, json, traceback, re
from pathlib import Path
from datetime import datetime
root = Path(u.Paths.project_dir())
assert 'Minimap/PIE' in Path(u.Paths.project_saved_dir()).as_posix(), 'Use an isolated minimap PIE UserDir'
out = root / 'Saved/Minimap' / ('ramp-validation-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
out.mkdir(parents=True,exist_ok=False)
verify = '-VerifyRockRamps' in u.SystemLibrary.get_command_line()
suffix = 'after' if verify else 'before'
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
level = u.get_editor_subsystem(u.LevelEditorSubsystem)
points = [(-2350, 0, 600), (-2140, 0, 600), (-1900, 0, 700),
          (-1600, 0, 1000), (-1320, 0, 1000), (-1000, 0, 1050),
          (-5800, 0, 650), (-6580, 0, 1050),
          # Exact user-captured Mesa_09 failure and neighboring slope samples.
          (2744.6981119522484, -1446.2583221765303, 152.13431853086357),
          (2695, -1446, 300), (2795, -1446, 300),
          (2745, -1395, 300), (2745, -1495, 300)]
state = dict(start=time.monotonic(), phase=0, index=0, results=[])
def finish(error=''):
    (out/('rock-ramp-probes-'+suffix+'.json')).write_text(json.dumps(dict(success=not error, error=error, results=state['results']), ensure_ascii=False, indent=2), encoding='utf8')
    u.unregister_slate_post_tick_callback(handle)
    level.editor_request_end_play()
    u.SystemLibrary.quit_editor()
def tick(dt):
    try:
        if time.monotonic()-state['start'] > 240: raise RuntimeError('Probe timeout')
        world=editor.get_game_world()
        if not world: return
        now=u.GameplayStatics.get_time_seconds(world)
        pc=u.GameplayStatics.get_player_controller(world,0)
        pawn=pc.get_controlled_pawn() if pc else None
        if not pawn or now<2: return
        if state['phase']==0:
            for actor in u.GameplayStatics.get_all_actors_of_class(world,u.SchoolOpeningSceneActor): actor.call_method('DirectorStopped',(False,))
            for widget in u.ObjectIterator(u.UserWidget):
                if widget.is_in_viewport() and widget.get_class().get_name() in ('WBP_Fade_C','WBP_Tutorial_C'): widget.remove_from_parent()
            pc.player_camera_manager.stop_camera_fade()
            u.SystemLibrary.execute_console_command(world,'DisableAllScreenMessages')
            pc.set_control_rotation(u.Rotator(pitch=-15,yaw=180,roll=0))
            state['phase']=1
        if state['phase']==1:
            x,y,z=points[state['index']]
            pawn.set_actor_location(u.Vector(x,y,z+pawn.capsule_component.get_scaled_capsule_half_height()+5),False,False)
            state.update(phase=2,at=now)
        elif now-state['at']>3:
            pos=pawn.get_actor_location()
            feet=pos.z-pawn.capsule_component.get_scaled_capsule_half_height()
            data=u.GameplayStatics.get_actor_of_class(world,u.MinimapRegionActor).get_editor_property('data')
            sub=next(o for o in u.ObjectIterator(u.MinimapWorldSubsystem) if o.get_outer()==world)
            report=dict(probe=points[state['index']], position=[pos.x,pos.y,feet], grounded=pawn.character_movement.is_moving_on_ground(),
                        contact=u.MinimapEditorLibrary.describe_pawn_ground(world), samples=u.MinimapEditorLibrary.describe_floor_samples(data,u.Vector(pos.x,pos.y,feet)),
                        floor=str(sub.get_current_floor_id()), discovered=sub.get_discovered_cell_count())
            state['results'].append(report)
            u.log('ROCK_RAMP_PROBE '+str(report))
            if verify:
                assert report['grounded'], 'Pawn not grounded: '+str(report)
                assert report['floor']!='None', 'Walkable rock ramp missing floor: '+str(report)
                sample=re.search(re.escape(report['floor'])+r'=1@(-?[\d.]+)', report['samples'])
                assert sample and abs(float(sample.group(1))-feet)<=75, 'Exact grounded cell is not Floor: '+str(report)
                assert report['discovered']>=10, 'Ramp has no meaningful revealed area: '+str(report)
                assert abs(pos.x-points[state['index']][0])<75 and abs(pos.y-points[state['index']][1])<75, 'Wrong probe location'
            u.SystemLibrary.execute_console_command(world,'Shot showui filename='+(out/('rock-ramp-'+suffix+'-'+str(state['index']))).as_posix())
            state['index']+=1
            if state['index']==len(points): finish(); return
            state['phase']=1
    except Exception: finish(traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
u.CarryEditorLibrary.start_carry_review_play()
