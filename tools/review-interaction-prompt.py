"""Verify saved player prompt in PIE using real Enhanced Input and capture the UI."""
import json,time,traceback
from pathlib import Path
import unreal as u
out=Path(u.Paths.project_dir()).resolve()/'Saved/InteractionPromptReview'
report={'checks':[]}; phase='startup'; elapsed=0.; start=time.monotonic()
pawn=carry=prompt=sub=None
u.CarryEditorLibrary.start_carry_review_play()
def check(name,value):
    report['checks'].append({'name':name,'passed':bool(value)})
    assert value,name

def shot(name):
    u.CarryEditorLibrary.capture_carry_review(str(out/(name+'.png')),True)

def finish(error=None):
    if error: report['error']=error
    (out/'play.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    u.log('INTERACTION_PROMPT_PLAY_RESULT '+json.dumps(report,ensure_ascii=False))
    u.unregister_slate_post_tick_callback(token)
    u.SystemLibrary.quit_editor()

def tick(dt):
    global pawn,carry,prompt,phase,elapsed,sub
    try:
        if time.monotonic()-start>180: raise RuntimeError('Timeout '+phase)
        if phase=='startup':
            pawn=u.CarryEditorLibrary.get_carry_review_pawn()
            if not pawn:return
            prompt=pawn.get_component_by_class(u.InteractionPromptComponent)
            carry=pawn.get_component_by_class(u.CarryComponent)
            check('Saved heroine contains interaction prompt component',prompt is not None)
            check('Saved actor rules loaded',len(prompt.rules)==15)
            phase='settle';elapsed=0
        elapsed+=dt
        if phase=='settle' and elapsed>3:
            report['initial']={'pawn':str(pawn.get_actor_location()),'action':str(prompt.current_action),'key':str(prompt.get_interaction_key_text()),'target':str(prompt.current_target)}
            check('F is mapped interaction key',str(prompt.get_interaction_key_text())=='F')
            check('Pickup offered before input',prompt.current_action==u.InteractionAction.PICK_UP)
            widgets=u.WidgetLibrary.get_all_widgets_of_class(pawn,u.InteractionPromptWidget,False)
            check('One visible noninteractive prompt',len(widgets)==1 and widgets[0].get_visibility()==u.SlateVisibility.HIT_TEST_INVISIBLE)
            shot('prompt-pickup');phase='capture-pickup';elapsed=0
        elif phase=='capture-pickup' and elapsed>.3:
            u.GameplayStatics.set_game_paused(pawn,True)
            phase='paused';elapsed=0
        elif phase=='paused' and elapsed>.3:
            check('Pausing hides a visible prompt',prompt.current_action==u.InteractionAction.NONE)
            u.GameplayStatics.set_game_paused(pawn,False)
            phase='resume';elapsed=0
        elif phase=='resume' and elapsed>.3:
            check('Resuming restores prompt',prompt.current_action==u.InteractionAction.PICK_UP)
            check('Actual Enhanced Input accepted',u.CarryEditorLibrary.inject_carry_review_input('/Game/Constellation/Input/IA_Interact',u.Vector(1,0,0)))
            phase='picking';elapsed=0
        elif phase=='picking' and elapsed>.12:
            check('Transition hides prompt',prompt.current_action==u.InteractionAction.NONE)
            phase='holding';elapsed=0
        elif phase=='holding' and elapsed>2:
            check('Actual input picked up the object',carry.state==u.CarryState.CARRYING)
            check('Valid placement offers PutDown',prompt.current_action==u.InteractionAction.PUT_DOWN)
            shot('prompt-putdown');phase='capture-holding';elapsed=0
        elif phase=='capture-holding' and elapsed>.3:
            carry.begin_aim();phase='aiming';elapsed=0
        elif phase=='aiming' and elapsed>.2:
            check('Aim offers CancelAim',prompt.current_action==u.InteractionAction.CANCEL_AIM)
            shot('prompt-cancel');phase='capture-aim';elapsed=0
        elif phase=='capture-aim' and elapsed>.3:
            u.CarryEditorLibrary.inject_carry_review_input('/Game/Constellation/Input/IA_Interact',u.Vector(1,0,0))
            phase='cancelled';elapsed=0
        elif phase=='cancelled' and elapsed>.3:
            check('F cancels aiming',carry.state==u.CarryState.CARRYING)
            u.CarryEditorLibrary.inject_carry_review_input('/Game/Constellation/Input/IA_Interact',u.Vector(1,0,0))
            phase='placed';elapsed=0
        elif phase=='placed' and elapsed>2:
            check('F places the carried object',carry.state==u.CarryState.IDLE)
            pawn.set_actor_rotation(u.Rotator(yaw=180),True)
            phase='away';elapsed=0
        elif phase=='away' and elapsed>.3:
            check('Turning away hides prompt',prompt.current_action==u.InteractionAction.NONE)
            shot('prompt-hidden');phase='finish';elapsed=0
        elif phase=='finish' and elapsed>.3:
            sub=next(x for x in u.ObjectIterator(u.EnhancedInputLocalPlayerSubsystem) if not x.get_name().startswith('Default__'))
            check('Local input subsystem available',sub is not None)
            sub.clear_all_mappings()
            context=u.new_object(u.InputMappingContext)
            key=u.Key();assert key.import_text('G')
            context.map_key(prompt.interact_input_action,key)
            sub.add_mapping_context(context,100)
            phase='remap';elapsed=0
        elif phase=='remap' and elapsed>.3:
            check('Rebound interaction displays G',str(prompt.get_interaction_key_text())=='G')
            sub.clear_all_mappings();phase='unbound';elapsed=0
        elif phase=='unbound' and elapsed>.3:
            check('Unbound key does not display stale F',str(prompt.get_interaction_key_text())=='')
            widgets=u.WidgetLibrary.get_all_widgets_of_class(pawn,u.InteractionPromptWidget,False)
            check('Unbound interaction hides widget',widgets[0].get_visibility()==u.SlateVisibility.COLLAPSED)
            finish()
    except Exception:finish(traceback.format_exc())
token=u.register_slate_post_tick_callback(tick)
