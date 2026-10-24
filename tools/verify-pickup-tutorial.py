"""PIE regression: local-player area entry, nonblocking toast, timeout, and once per visit."""
import json, time, traceback
from pathlib import Path
import unreal as u

out = Path(u.Paths.project_dir()) / 'Saved/PickupTutorial'
out.mkdir(parents=True, exist_ok=True)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
level = u.get_editor_subsystem(u.LevelEditorSubsystem)
state = dict(start=time.monotonic(), phase=0, checks=[])
assert 'PickupTutorial/PIE' in u.Paths.project_saved_dir()
assert hasattr(u, 'PickupTutorialTrigger'), 'Missing pickup tutorial trigger'
u.EditorPythonScripting.set_keep_python_script_alive(True)

def check(name, ok):
    state['checks'].append(dict(name=name, passed=bool(ok)))
    assert ok, name

def finish(error=''):
    (out/'pie-result.json').write_text(json.dumps(dict(success=not error,error=error,checks=state['checks']),ensure_ascii=False,indent=2),encoding='utf-8')
    u.log('PICKUP_TUTORIAL_RESULT '+str(not error)+' '+error)
    u.unregister_slate_post_tick_callback(handle)
    level.editor_request_end_play()
    u.SystemLibrary.quit_editor()

def pickup_widgets(world):
    return [w for w in u.WidgetLibrary.get_all_widgets_of_class(world,u.TutorialPromptWidget,False)
            if w.get_editor_property('action') == u.TutorialPromptAction.PICK_UP and w.is_in_viewport()]

def tick(dt):
    try:
        if time.monotonic()-state['start'] > 100: raise RuntimeError('Timeout')
        world=editor.get_game_world()
        if not world:return
        pc=u.GameplayStatics.get_player_controller(world,0)
        pawn=pc.get_controlled_pawn() if pc else None
        if not pawn:return
        phase=state['phase']
        if phase==0:
            triggers=u.GameplayStatics.get_all_actors_of_class(world,u.PickupTutorialTrigger)
            check('Exactly one authored pickup area',len(triggers)==1)
            state.update(trigger=triggers[0], pawn=pawn, pc=pc, phase=1, at=time.monotonic())
            return
        trigger=state['trigger']; now=time.monotonic()
        if phase==1 and now-state['at']>2:
            check('Spawn does not show pickup toast',not pickup_widgets(world))
            check('Spawn is outside area',not trigger.get_editor_property('has_shown'))
            state['cursor']=pc.get_editor_property('show_mouse_cursor')
            state['paused']=u.GameplayStatics.is_game_paused(world)
            center=trigger.get_actor_location()
            pawn.set_actor_location(center,False,True)
            state.update(phase=10,at=now)
        elif phase==10 and now-state['at']>1:
            check('Opening prevents pickup toast even inside area',not pickup_widgets(world))
            pawn.set_actor_location(trigger.get_actor_location()+u.Vector(1000,0,0),False,True)
            # Only this transient PIE world skips the opening; the saved scene is untouched.
            for opening in u.GameplayStatics.get_all_actors_of_class(world,u.SchoolOpeningSceneActor):
                opening.destroy_actor()
            state.update(phase=11,at=now)
        elif phase==11 and now-state['at']>1:
            check('Outside area remains unconsumed after opening',not pickup_widgets(world) and not trigger.get_editor_property('has_shown'))
            pawn.set_actor_location(trigger.get_actor_location(),False,True)
            state.update(phase=2,at=now)
        elif phase==2 and now-state['at']>1:
            widgets=pickup_widgets(world)
            check('Entering the marked area shows one pickup toast',len(widgets)==1)
            widget=widgets[0]
            check('Requested pickup text',str(widget.get_instruction_text())=='F를 눌러 물건을 들 수 있습니다.')
            check('Eight second hold',widget.get_editor_property('hold_seconds')==8)
            check('Player input stays enabled',not pc.is_move_input_ignored())
            check('Cursor is unchanged',pc.get_editor_property('show_mouse_cursor')==state['cursor'])
            check('World is not paused',u.GameplayStatics.is_game_paused(world)==state['paused'])
            state['widget']=widget
            u.SystemLibrary.execute_console_command(world,'Shot SHOWUI -nosuffix filename="'+str(out/'pickup-toast.png')+'"')
            state.update(phase=3,at=now)
        elif phase==3 and now-state['at']>1 and not state.get('remapped'):
            interaction=pawn.get_component_by_class(u.InteractionPromptComponent)
            sub=next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if not x.get_name().startswith('Default__'))
            sub.clear_all_mappings()
            context=u.new_object(u.InputMappingContext)
            key=u.Key();assert key.import_text('G')
            context.map_key(interaction.interact_input_action,key)
            sub.add_mapping_context(context,100)
            state.update(remapped=True,context=context)
        elif phase==3 and state.get('remapped') and not state.get('remap_checked') and now-state['at']>2:
            check('Toast follows remapped interaction key',str(state['widget'].get_instruction_text())=='G를 눌러 물건을 들 수 있습니다.')
            state['remap_checked']=True
        elif phase==3 and now-state['at']>9:
            check('Toast expires automatically',not pickup_widgets(world))
            pawn.set_actor_location(trigger.get_actor_location()+u.Vector(1000,0,0),False,True)
            state.update(phase=4,at=now)
        elif phase==4 and now-state['at']>.5:
            pawn.set_actor_location(trigger.get_actor_location(),False,True)
            state.update(phase=5,at=now)
        elif phase==5 and now-state['at']>1:
            check('Re-entry does not repeat toast',not pickup_widgets(world))
            check('Trigger records once-per-visit completion',trigger.get_editor_property('has_shown'))
            finish()
    except Exception:finish(traceback.format_exc())

handle=u.register_slate_post_tick_callback(tick)
u.CarryEditorLibrary.start_carry_review_play()
