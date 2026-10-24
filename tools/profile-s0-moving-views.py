"""Moving editor-camera A/B/A profile; never saves scene, not a player test."""
import hashlib,math,traceback,re
for row in json.loads((O/'additions.json').read_text()):
 a=next(a for a in A.get_all_level_actors() if a.get_name()==row['name']);A.destroy_actor(a)
actors={a.get_name():a for a in A.get_all_level_actors()}
def norm(v):return re.sub(r'0x[0-9A-Fa-f]+','PTR',str(v)).replace('-0.000000','0.000000')
for row in json.loads((O/'baseline-actors.json').read_text()):
 a=actors[row['name']]
 assert norm(a.get_actor_transform())==norm(row['transform'])
 assert a.get_actor_enable_collision()==row['collision']
 meshes=[dict(name=c.get_name(),mesh=c.static_mesh.get_path_name() if c.static_mesh else '',materials=[m.get_path_name() if m else '' for m in c.get_materials()]) for c in a.get_components_by_class(u.StaticMeshComponent)]
 assert meshes==row['meshes']
(O/'rejected.json').write_text(json.dumps(dict(adopted=False,reason='Additional lumps worsen close-up composition; no clear improvement in main view',baseline_actors_preserved=True,map_saved=False)))
u.unregister_slate_post_tick_callback(handle)
O=R/'Saved/S0WetFloor/MovingViews_20261020';O.mkdir(parents=True,exist_ok=True)
assert not (O/'session.json').exists()
before=hashlib.sha256(mapfile.read_bytes()).hexdigest()
(O/'session.json').write_text(json.dumps(dict(map_sha256=before,scope='editor camera moving; not PIE, player input, or gameplay FPS')))
world=u.EditorLevelLibrary.get_editor_world()
c=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='S0_WetFloor_PlanarReflection').get_component_by_class(u.PlanarReflectionComponent)
visible=c.is_visible()
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_viewport_realtime(True)
for command in ['t.MaxFPS 0','r.VSync 0','r.GPUCsvStatsEnabled 1']:u.SystemLibrary.execute_console_command(world,command)
phases=['on','off','repeat'];S=dict(i=0,start=None,csv=False)
def motion_tick(dt):
 try:
  now=time.monotonic()
  if now<S.get('cooldown',0):return
  if S['i']==len(phases):
   c.set_visibility(visible)
   assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==before
   (O/'completed.json').write_text(json.dumps(dict(phases=phases,map_unchanged=True,map_saved=False)))
   u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
  name=phases[S['i']]
  if S['start'] is None:
   c.set_visibility(False if name=='off' else visible)
   u.SystemLibrary.execute_console_command(world,'csvprofile STARTFILE=S0MovingViews_'+name+'.csv')
   S.update(start=now,csv=False);(O/'phase.json').write_text(json.dumps(dict(phase=name)))
  elapsed=now-S['start'];t=max(0,elapsed-12)/24;angle=2*math.pi*t
  pos=(2450+450*math.cos(angle),350+1250*math.sin(angle),210+80*math.sin(angle))
  cam.set_actor_location(u.Vector(*pos),False,True)
  cam.set_actor_rotation(u.Rotator(pitch=-8,yaw=-150+40*math.sin(angle)),False)
  u.EditorLevelLibrary.editor_invalidate_viewports()
  if elapsed>=12 and not S['csv']:
   u.SystemLibrary.execute_console_command(world,'csvprofile START');S['csv']=True
  if elapsed>=36:
   u.SystemLibrary.execute_console_command(world,'csvprofile STOP');S.update(i=S['i']+1,start=None,cooldown=now+8)
 except:
  c.set_visibility(visible);(O/'error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(motion_tick)
