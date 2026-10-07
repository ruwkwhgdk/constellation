"""Check actual school furniture, remapped input and modal suppression without saving the map."""
import json,time,traceback
from pathlib import Path
import unreal as u
out=Path(u.Paths.project_dir()).resolve()/'Saved/InteractionPromptReview'
report={'checks':[]}; phase='startup'; elapsed=0.; start=time.monotonic(); pawn=prompt=target=sub=None
chair_class=u.EditorAssetLibrary.load_blueprint_class('/Game/Constellation/Environments/School/Blueprints/BP_School_Chair')
u.CarryEditorLibrary.start_carry_review_play()
def check(name,condition):
 report['checks'].append({'name':name,'passed':bool(condition)})
 assert condition,name
def finish(error=None):
 if error:report['error']=error
 (out/'school.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 u.log('SCHOOL_PROMPT_RESULT '+json.dumps(report,ensure_ascii=False))
 u.unregister_slate_post_tick_callback(token);u.SystemLibrary.quit_editor()
def tick(dt):
 global pawn,prompt,target,phase,elapsed,sub
 try:
  if time.monotonic()-start>180:raise RuntimeError('Timeout '+phase)
  if phase=='startup':
   pawn=u.CarryEditorLibrary.get_carry_review_pawn()
   if not pawn:return
   prompt=pawn.get_component_by_class(u.InteractionPromptComponent)
   check('Actual school heroine contains prompt',prompt is not None)
   phase='settle';elapsed=0
  elapsed+=dt
  if phase=='settle' and elapsed>2:
   for widget in u.WidgetLibrary.get_all_widgets_of_class(pawn,u.TutorialPromptWidget,False):widget.dismiss()
   u.WidgetLibrary.set_input_mode_game_only(pawn.get_controller())
   cls=chair_class
   actors=u.GameplayStatics.get_all_actors_of_class(pawn,cls)
   if not actors:
    actors=[a for a in u.GameplayStatics.get_all_actors_of_class(pawn,u.Actor) if a.get_component_by_class(u.HoldableComponent) and 'Chair' in a.get_name()]
   if not actors:
    if elapsed<15:return
    report['actors']=[a.get_path_name()+' '+a.get_class().get_name() for a in u.GameplayStatics.get_all_actors_of_class(pawn,u.Actor)]
    raise RuntimeError('No school chairs in active PIE world '+pawn.get_path_name())
   target=next((a for a in actors if a.get_name()=='BP_AbandonedSchool_Chair_C_2'),actors[0])
   rot=u.Rotator(yaw=0)
   pawn.set_actor_location_and_rotation(target.get_actor_location()-rot.get_forward_vector()*105+u.Vector(0,0,90),rot,False,True)
   pawn.get_controller().set_control_rotation(rot)
   pawn.get_component_by_class(u.CharacterMovementComponent).set_movement_mode(u.MovementMode.MOVE_WALKING)
   u.SystemLibrary.execute_console_command(pawn,'DisableAllScreenMessages')
   u.CarryEditorLibrary.use_carry_review_camera(True)
   phase='chair';elapsed=0
  elif phase=='chair' and elapsed>1:
   carry=pawn.get_component_by_class(u.CarryComponent)
   report['chair']={'action':str(prompt.current_action),'target':str(prompt.current_target),'pawn':str(pawn.get_actor_location()),'item':target.get_path_name(),'can_pick_up':carry.can_pick_up(target.get_component_by_class(u.HoldableComponent)),'sweep':str(carry.find_interaction_item()),'carry_state':str(carry.state),'move_ignored':pawn.get_controller().is_move_input_ignored(),'mouse':pawn.get_controller().get_editor_property('show_mouse_cursor')}
   check('Placed school chair offers pickup',prompt.current_action==u.InteractionAction.PICK_UP and prompt.current_target==target)
   u.CarryEditorLibrary.capture_carry_review(str(out/'school-prompt-pickup.png'),True)
   phase='capture';elapsed=0
  elif phase=='capture' and elapsed>.3:
   u.GameplayStatics.set_game_paused(pawn,True)
   phase='paused';elapsed=0
  elif phase=='paused' and elapsed>.3:
   check('Pausing hides a visible prompt',prompt.current_action==u.InteractionAction.NONE)
   u.GameplayStatics.set_game_paused(pawn,False)
   phase='resume';elapsed=0
  elif phase=='resume' and elapsed>.3:
   check('Resuming restores the prompt',prompt.current_action==u.InteractionAction.PICK_UP)
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
   u.CarryEditorLibrary.capture_carry_review(str(out/'school-prompt-remapped.png'),True)
   phase='capture-remap';elapsed=0
  elif phase=='capture-remap' and elapsed>.3:
   sub.clear_all_mappings();phase='unbound';elapsed=0
  elif phase=='unbound' and elapsed>.3:
   check('Unbound input does not display stale F',str(prompt.get_interaction_key_text())=='')
   widgets=u.WidgetLibrary.get_all_widgets_of_class(pawn,u.InteractionPromptWidget,False)
   check('Unbound interaction hides widget',len(widgets)==1 and widgets[0].get_visibility()==u.SlateVisibility.COLLAPSED)
   pawn.get_controller().set_ignore_move_input(True)
   phase='modal';elapsed=0
  elif phase=='modal' and elapsed>.2:
   check('Blocked player hides interaction',prompt.current_action==u.InteractionAction.NONE)
   finish()
 except Exception:finish(traceback.format_exc())
token=u.register_slate_post_tick_callback(tick)
