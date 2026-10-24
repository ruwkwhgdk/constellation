"""Background PIE integration: real interaction, UI cancellation/retry, commit and toast."""
import unreal as u,json,time,traceback,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();O=R/'Saved/SwordAcquisition'/('FunctionalReview-'+time.strftime('%Y%m%d-%H%M%S'));O.mkdir(parents=True)
(R/'Saved/SwordAcquisition/latest-functional-review.txt').write_text(str(O))
MAP=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap';before=hashlib.sha256(MAP.read_bytes()).hexdigest()
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem)
for a in list(A.get_all_level_actors()):
 if isinstance(a,u.SceneEventBinding) and a.get_actor_label()!='SwordAcquisition_Interaction':a.set_editor_property('enabled',False)
 if isinstance(a,u.SchoolOpeningSceneActor):A.destroy_actor(a)
 if isinstance(a,u.PlayerStart):a.set_actor_location(u.Vector(-10810,0,1030),False,True);a.set_actor_rotation(u.Rotator(yaw=180),False)
S={'start':time.monotonic(),'phase':'startup','frames':[],'last_capture':0,'cancelled':False}
u.EditorPythonScripting.set_keep_python_script_alive(True);u.CarryEditorLibrary.start_carry_review_play()
def finish(error=None):
 S['finished']=True
 (O/'result.json').write_text(json.dumps({'error':error,'cancel_retry':S['cancelled'],'completed':S.get('complete',False),'toast_after_controls':S.get('toast',False),'duplicate_suppressed':S.get('duplicate',False),'attack_montage':S.get('attack_played'),'attack_blocked_during_return':S.get('blocked_attack_injected',False),'map_unchanged':before==hashlib.sha256(MAP.read_bytes()).hexdigest(),'qte':'engine outcome injection, physical swipe not tested','save_directory':u.Paths.project_saved_dir()},ensure_ascii=False,indent=2),encoding='utf8')
 (O/'recording.json').write_text(json.dumps(S['frames'],ensure_ascii=False),encoding='utf8')
 u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  if S.get('finished'):return
  now=time.monotonic()
  if now-S['start']>240:raise RuntimeError('Timeout: '+S['phase'])
  pawn=u.CarryEditorLibrary.get_carry_review_pawn()
  if not pawn:return
  w=pawn.get_world();pc=u.GameplayStatics.get_player_controller(w,0)
  assert u.SwordAcquisitionReviewLibrary.prepare_background_tick(w)
  if S['phase']=='startup':
   if now-S['start']<12:return
   stage=u.GameplayStatics.get_actor_of_class(w,u.SwordAcquisitionStage);assert stage
   ability=pawn.get_editor_property('Ac_Ability');assert u.SwordAcquisitionReviewLibrary.configure_sword_review(pawn)
   sword=stage.get_editor_property('sword');pawn.set_actor_location(u.Vector(-10810,0,1030),False,True);pawn.set_actor_rotation(u.Rotator(yaw=180),False)
   assert all(not c.static_mesh for c in sword.get_components_by_class(u.StaticMeshComponent) if 'Star_Object' in c.get_name()),'Sword star mesh restored after reload'
   pc.set_control_rotation(u.Rotator(pitch=-10,yaw=180));S.update(stage=stage,sword=sword,ability=ability,phase='settle',ready=now);return
  if S['phase']=='settle':
   if now-S['ready']<3:return
   u.SystemLibrary.execute_console_command(w,'SceneDirector.SkipCinematics 0');u.SystemLibrary.execute_console_command(w,'DisableAllScreenMessages')
   # A pre-existing input lease must survive cancellation.
   pc.set_ignore_move_input(True);S['sword'].call_method('Interact',(pawn,None));S.update(phase='running',run_start=now)
  stage=S['stage'];ability=S['ability'];item_ui=next(o for o in u.ObjectIterator(u.ItemAcquisitionSubsystem) if o.get_outer()==w);ui=item_ui.is_presenting()
  active=next((a for a in u.GameplayStatics.get_all_actors_of_class(w,u.SceneDirectorPlayer) if a.is_director_playing()),None)
  if active and str(stage.get_editor_property('phase')) not in ['None','Cancelled']:assert not u.SwordAcquisitionReviewLibrary.pawn_input_enabled(pawn),'Gameplay actions leaked during scene'
  if active and str(stage.get_editor_property('phase'))=='Commit':
   assert not pawn.mesh.get_anim_instance().get_current_active_montage(),'Attack montage began before handoff'
   if not S.get('blocked_attack_injected'):
    assert u.CarryEditorLibrary.inject_carry_review_input('/Game/Constellation/Input/IA_Attack',u.Vector(1,0,0));S['blocked_attack_injected']=True
  if S['phase']=='cancelled':
   assert not ui and not ability.get_editor_property('IsCombatUnlocked'),'Cancellation granted or leaked UI'
   assert not ability.get_editor_property('IsAttackUnlocked'),'Cancellation granted attack'
   assert pc.is_move_input_ignored() and not pc.is_look_input_ignored(),'Previous input lease was lost or scene lock leaked'
   assert not S['sword'].get_editor_property('hidden'),'Sword not restored'
   pc.set_ignore_move_input(False);S['sword'].call_method('Interact',(pawn,None));S.update(phase='running',run_start=now);return
  if active and active.is_waiting_for_qte():
   if not S.get('qte_start'):S['qte_start']=now
   if now-S['qte_start']>2:u.SceneDirectorLibrary.resolve_qte_for_review(active,True);S['qte_start']=None
  if ui:
   assert active and not ability.get_editor_property('IsCombatUnlocked'),'Combat unlocked before UI/narration'
   assert not ability.get_editor_property('IsAttackUnlocked'),'Attack unlocked before UI/narration'
   assert pc.is_move_input_ignored() and pc.is_look_input_ignored(),'UI lost scene locks'
   if not S['cancelled']:
    if not S.get('early_at'):
     S['early_at']=now;S['confirm_key']=item_ui.current_confirm_key();u.ItemAcquisitionReviewLibrary.send_review_key(S['confirm_key'],True)
    if now-S['early_at']>1:
     assert item_ui.is_presenting(),'Held early confirmation accepted'
     u.ItemAcquisitionReviewLibrary.send_review_key(S['confirm_key'],False);active.stop_director();S.update(cancelled=True,phase='cancelled')
    return
   if not S.get('ui_at'):S['ui_at']=now
   if now-S['ui_at']>4 and not S.get('confirmed'):
    key=item_ui.current_confirm_key();u.ItemAcquisitionReviewLibrary.send_review_key(key,True);u.ItemAcquisitionReviewLibrary.send_review_key(key,False);S['confirmed']=True
  if active and active.is_waiting_for_dialogue():
   assert not ability.get_editor_property('IsCombatUnlocked'),'Combat unlocked before narration confirmation'
   if not S.get('dialogue_at'):S['dialogue_at']=now
   if now-S['dialogue_at']>3:active.advance_dialogue()
  if S['cancelled'] and now-S['last_capture']>.1:
   i=len(S['frames']);u.CarryEditorLibrary.capture_carry_review(str(O/('frame-%05d.png'%i)),True)
   S['frames'].append({'t':now-S['run_start'],'ui':bool(ui),'phase':str(stage.get_editor_property('phase')),'dialogue':str(active.current_dialogue) if active else ''});S['last_capture']=now
  if stage.get_editor_property('attack_toast') and not S.get('toast'):
   assert not active and not ui,'Toast overlaps scene/UI'
   assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored(),'Toast appeared before input restoration'
   assert u.SwordAcquisitionReviewLibrary.pawn_input_enabled(pawn),'Pawn input not restored before toast'
   assert ability.get_editor_property('IsCombatUnlocked') and stage.get_editor_property('completed')
   assert ability.get_editor_property('IsAttackUnlocked')
   assert not u.GameplayStatics.is_game_paused(w)
   S['toast']=True
  if not active and S['cancelled'] and stage.get_editor_property('completed'):
   with (O/'attack-input-diagnostic.txt').open('a',encoding='utf8') as diag:
    diag.write(str(now)+': '+u.SwordAcquisitionReviewLibrary.review_input_state(pawn)+'\n')
    for c in pawn.get_components_by_class(u.ActorComponent):
     if 'Attack' in c.get_class().get_name():
      try:diag.write(c.get_name()+' IsAttacking='+str(c.get_editor_property('IsAttacking'))+'\n')
      except:pass
   if not S.get('complete'):
    S.update(complete=True,done_at=now);S['sword'].call_method('Interact',(pawn,None))
   if now-S['done_at']>1.5 and not S.get('attack_injected'):
    assert u.CarryEditorLibrary.inject_carry_review_input('/Game/Constellation/Input/IA_Attack',u.Vector(1,0,0));S['attack_injected']=True
   montage=pawn.mesh.get_anim_instance().get_current_active_montage()
   if montage and 'attack' in montage.get_name().lower():S['attack_played']=montage.get_name()
   if now-S['done_at']>4:
    assert not any(a.is_director_playing() for a in u.GameplayStatics.get_all_actors_of_class(w,u.SceneDirectorPlayer)),'Duplicate replay'
    assert S.get('toast'),'Toast missing';assert S.get('attack_played'),'Unlocked attack did not play';S['duplicate']=True;finish()
 except:finish(traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
