"""Verify the saved gate in transient PIE using its real Blueprint interaction."""
import unreal as u
import json, time, traceback
from pathlib import Path

out = Path(u.Paths.project_dir()) / 'Saved/GateUI20261019'
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
state = dict(start=time.monotonic(), phase=0, checks=[])
u.EditorPythonScripting.set_keep_python_script_alive(True)

def check(name, value):
    state['checks'].append(dict(name=name, passed=bool(value)))
    assert value, name

def finish(error=''):
    (out/'pie-result.json').write_text(json.dumps(dict(success=not error, error=error, checks=state['checks']), indent=2), encoding='utf-8')
    u.log('GATE_UI_RESULT '+str(not error)+' '+error)
    u.unregister_slate_post_tick_callback(handle)
    u.get_editor_subsystem(u.LevelEditorSubsystem).editor_request_end_play()
    u.SystemLibrary.quit_editor()

def tick(dt):
    try:
        now=time.monotonic()
        if now-state['start']>100: raise RuntimeError('PIE timeout')
        world=editor.get_game_world()
        if not world: return
        pc=u.GameplayStatics.get_player_controller(world,0)
        pawn=pc.get_controlled_pawn() if pc else None
        if not pawn: return
        if state['phase']==0:
            gates=[a for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor) if a.get_class().get_name()=='BP_School_Gate_C']
            gate=next(a for a in gates if a.get_name()=='BP_School_Gate_C_3')
            check('Saved start gate is one-shot',gate.get_editor_property('InteractOnce'))
            check('Other gates retain their settings',all(not a.get_editor_property('InteractOnce') for a in gates if a!=gate))
            check('Saved gate starts unopened',not gate.get_editor_property('bIsInteracted'))
            prompt=pawn.get_component_by_class(u.InteractionPromptComponent)
            check('Unopened gate offers Open',prompt.get_target_action(gate)==u.InteractionAction.OPEN)
            check('Unopened gate accepts input',u.InteractionAvailabilityComponent.can_actor_interact(gate))
            for opening in u.GameplayStatics.get_all_actors_of_class(world,u.SchoolOpeningSceneActor): opening.destroy_actor()
            pawn.set_actor_location(gate.get_actor_location()+gate.get_actor_forward_vector()*250+u.Vector(0,0,110),False,True)
            state.update(phase=10,at=now,gate=gate,prompt=prompt)
        elif state['phase']==10 and now-state['at']>2:
            pawn.get_component_by_class(u.SkeletalMeshComponent).get_anim_instance().montage_stop(0)
            state['gate'].call_method('Interact',(pawn,None))
            state.update(phase=1,at=now)
        elif state['phase']==1 and now-state['at']>2:
            gate=state['gate']; prompt=state['prompt']
            check('Real Blueprint interaction marks gate completed',gate.get_editor_property('bIsInteracted'))
            check('Completed gate has no Open prompt',prompt.get_target_action(gate)==u.InteractionAction.NONE)
            check('Completed gate rejects interaction',not u.InteractionAvailabilityComponent.can_actor_interact(gate))
            finish()
    except Exception: finish(traceback.format_exc())

handle=u.register_slate_post_tick_callback(tick)
u.CarryEditorLibrary.start_carry_review_play()
