import unreal as u,json,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/PlayRoute_20261018/UpperFinishV15';O.mkdir(parents=True,exist_ok=True)
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.EditorLevelLibrary.get_editor_world()
rows=[]
for x0,x1,y0,y1 in [(2400,3300,-2200,-1100),(300,1000,-2700,-1800)]:
 for x in range(x0,x1+1,100):
  for y in range(y0,y1+1,100):
   h=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,1300),u.Vector(x,y,-100),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],u.DrawDebugTrace.NONE,True)
   rows.append(dict(x=x,y=y,hit=h.export_text() if h else None))
(O/'surface-grid.json').write_text(json.dumps(rows,indent=2))
u.CarryEditorLibrary.start_carry_review_play();u.EditorPythonScripting.set_keep_python_script_alive(True)
S={'start':time.monotonic(),'ready':False}
def tick(dt):
 global pawn
 try:
  pawn=u.CarryEditorLibrary.get_carry_review_pawn()
  if not pawn:
   if time.monotonic()-S['start']>90:raise RuntimeError('PIE pawn timeout')
   return
  if not S['ready']:
   movement=pawn.get_component_by_class(u.CharacterMovementComponent);capsule=pawn.get_component_by_class(u.CapsuleComponent)
   (O/'player.json').write_text(json.dumps(dict(class_name=pawn.get_class().get_path_name(),location=str(pawn.get_actor_location()),max_step=movement.max_step_height,walkable_angle=movement.get_walkable_floor_angle(),radius=capsule.get_scaled_capsule_radius(),half_height=capsule.get_scaled_capsule_half_height()),indent=2));S['ready']=True;S['ready_at']=time.monotonic()
  if time.monotonic()-S['ready_at']<30:return
  command=O/'control.py'
  if command.exists():
   code=command.read_text(encoding='utf8');command.rename(O/('executed-'+str(time.time_ns())+'.py'));exec(code,globals())
 except:
  (O/'error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)

