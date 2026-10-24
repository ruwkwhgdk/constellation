import unreal as u
import time,json,traceback
from pathlib import Path
r=Path(u.Paths.project_dir());out=r/'Saved/PlayerHUD';level=u.get_editor_subsystem(u.LevelEditorSubsystem);editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert 'PlayerHUD/PIE' in Path(u.Paths.project_saved_dir()).as_posix()
s={'phase':0,'start':time.monotonic(),'checks':[]}
def finish(ok,error=''):
 (out/'pie-result.json').write_text(json.dumps({'success':ok,'error':error,'checks':s['checks']},ensure_ascii=False,indent=2),encoding='utf8')
 u.log('STARLIGHT_PIE_RESULT '+str(ok)+' '+error);u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.SystemLibrary.quit_editor()
def shot(w,name):u.SystemLibrary.execute_console_command(w,'Shot showui nosuffix filename='+(out/(name+'.png')).as_posix())
def stats(p):return next(c for c in p.get_components_by_class(u.ActorComponent) if c.get_class().get_name()=='Ac_Stats_C')
def tick(dt):
 try:
  if time.monotonic()-s['start']>180:raise RuntimeError('HUD PIE timeout')
  w=editor.get_game_world()
  if not w:return
  now=u.GameplayStatics.get_time_seconds(w)
  if s['phase']==0:
   pc=u.GameplayStatics.get_player_controller(w,0);pawn=pc.get_controlled_pawn();hud=next((o for o in u.ObjectIterator(u.StarlightPlayerHUDWidget) if o.is_in_viewport()),None)
   if not hud or not pawn:return
   a=stats(pawn)
   for k,v in [('MaxHP',125.),('CurrentHP',100.),('MaxStamina',80.),('CurrentStamina',60.),('StaminaRestorePerSec',0.),('DefensePoint',0.)]:a.set_editor_property(k,v,notify_mode=u.PropertyAccessChangeNotifyMode.NEVER)
   s.update(pc=pc,pawn=pawn,hud=hud,stats=a,at=now,phase=1,cursor=pc.get_editor_property('show_mouse_cursor'),move=pc.is_move_input_ignored(),look=pc.is_look_input_ignored());return
  hud=s['hud'];pc=s['pc'];a=s['stats'];pawn=s['pawn']
  assert pc.get_editor_property('show_mouse_cursor')==s['cursor']
  if s['phase'] not in (3,4,9,10):assert pc.is_move_input_ignored()==s['move'] and pc.is_look_input_ignored()==s['look']
  assert not u.GameplayStatics.is_game_paused(w)
  if s['phase']==1 and now-s['at']>.5:
   assert abs(hud.get_health_ratio()-.8)<.001 and abs(hud.get_stamina_ratio()-.75)<.001, str((hud.get_health_ratio(),hud.get_stamina_ratio(),a.get_editor_property('CurrentHP'),a.get_editor_property('CurrentStamina'),a.get_editor_property('MaxHP'),a.get_editor_property('MaxStamina'),pawn.get_name(),hud.get_owning_player_pawn()))
   shot(w,'hud-normal');s['checks'].append('legacy current/max ratios and input untouched');s.update(phase=2,at=now);return
  if s['phase']==2 and now-s['at']>.3:
   attacker=u.GameplayStatics.get_all_actors_of_class(w,u.StaticMeshActor)[0]
   pawn.call_method('TakeDamage',(75.,pawn.get_actor_location(),attacker,False,0.,False))
   s.update(phase=3,at=now);return
  if s['phase']==3 and now-s['at']>.06:
   assert abs(hud.get_health_ratio()-.2)<.001,str((hud.get_health_ratio(),a.get_editor_property("CurrentHP"),a.get_editor_property("DefensePoint"),a.get_path_name()))
   assert hud.get_damage_trail_ratio()>hud.get_health_ratio()
   shot(w,'hud-damage');s['checks'].append('actual BPI_Damageable TakeDamage hook and independent damage trail');s.update(phase=4,at=now);return
  if s['phase']==4 and now-s['at']>1.1:
   assert abs(hud.get_damage_trail_ratio()-hud.get_health_ratio())<.001
   a.set_editor_property('CurrentStamina',0.,notify_mode=u.PropertyAccessChangeNotifyMode.NEVER);assert u.PlayerHUDStyleEditorLibrary.inject_sprint_review(pc)
   s.update(phase=5,at=now);return
  if s['phase']==5 and now-s['at']>.06:
   assert hud.is_failure_feedback_active(),'Actual IA_Dash rejection did not trigger star feedback'
   assert hud.get_stamina_ratio()==0
   s['offset']=hud.get_star_offset().x;shot(w,'hud-stamina-rejected');s.update(phase=6,at=now);return
  if s['phase']==6 and now-s['at']>.06:
   assert abs(hud.get_star_offset().x-s['offset'])>.01,'Star shake did not animate'
   s.update(phase=7,at=now);return
  if s['phase']==7 and now-s['at']>.5:
   assert not hud.is_failure_feedback_active() and hud.get_star_offset().x==0
   col=hud.get_star_color();assert col.r>col.g*2,'Low HP pulse did not resume'
   s['checks'].append('real sprint failure orange/shake/zero track then low HP pulse resumes')
   a.set_editor_property('CurrentHP',125.,notify_mode=u.PropertyAccessChangeNotifyMode.NEVER);a.set_editor_property('CurrentStamina',40.,notify_mode=u.PropertyAccessChangeNotifyMode.NEVER)
   s.update(phase=8,at=now);return
  if s['phase']==8 and now-s['at']>.15:
   assert hud.get_health_ratio()==1 and abs(hud.get_stamina_ratio()-.5)<.001
   assert hud.get_damage_trail_ratio()==1
   shot(w,'hud-recovered');s['checks'].append('recovery ratios without damage trail')
   transform=next(c for c in pawn.get_components_by_class(u.ActorComponent) if c.get_class().get_name()=='Ac_Transform_C')
   transform.call_method('Execute Transform');s.update(phase=9,at=now);return
  if s['phase']==9 and now-s['at']>.3:
   current=pc.get_controlled_pawn()
   if current==pawn and now-s['at']<15:return
   assert current!=pawn,'Actual transform possession did not change'
   if not s.get('transformed_at'):s['transformed_at']=now;return
   if now-s['transformed_at']<.15:return
   other=stats(current);hp=float(other.get_editor_property('CurrentHP'))/float(other.get_editor_property('MaxHP'));st=float(other.get_editor_property('CurrentStamina'))/float(other.get_editor_property('MaxStamina'))
   assert abs(hud.get_health_ratio()-hp)<.001 and abs(hud.get_stamina_ratio()-st)<.02
   s['checks'].append('actual transform rebinds to active form stats')
   other.call_method('Calculate Damage',(float(other.get_editor_property('DefensePoint'))+10.,));s.update(phase=10,at=now);return
  if s['phase']==10 and now-s['at']>.06:
   assert hud.get_damage_trail_ratio()>hud.get_health_ratio(),'Transformed form missing common damage trail'
   s['checks'].append('transformed form common Calculate Damage triggers trail');finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);level.editor_request_begin_play()



