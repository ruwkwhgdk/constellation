movement=pawn.get_component_by_class(u.CharacterMovementComponent)
import math
routes=[('lower-up',(2800,-1050,95),(2800,-2200,495)),('lower-down',(2800,-2200,495),(2800,-1050,95)),('lower-edge-up',(3000,-1050,95),(3000,-2200,495)),('lower-edge-down',(3000,-2200,495),(3000,-1050,95)),('upper-up',(1250,-2300,495),(250,-2300,895)),('upper-down',(250,-2300,895),(1250,-2300,495))]
T={'i':0,'stage':'start','elapsed':0,'samples':[],'results':[]}
def route_tick(dt):
 try:
  if T['i']>=len(routes):
   (O/'walk-results.json').write_text(json.dumps(T['results'],indent=2));u.unregister_slate_post_tick_callback(route_handle);return
  name,start,end=routes[T['i']]
  if T['stage']=='capture':
   if time.monotonic()-T['capture_start']>1.5:T.update(i=T['i']+1,stage='start')
   return
  if T['stage']!='start' and time.monotonic()-T['wall_start']>50:raise RuntimeError('Route timed out without game time advancing: '+name)
  if T['stage']=='start':
   movement.stop_movement_immediately();pawn.set_actor_location(u.Vector(*start),False,True);movement.set_movement_mode(u.MovementMode.MOVE_WALKING)
   pc=u.GameplayStatics.get_player_controller(pawn,0);pc.set_control_rotation(u.Rotator(yaw=math.degrees(math.atan2(end[1]-start[1],end[0]-start[0]))))
   T.update(stage='settle',elapsed=0,samples=[],wall_start=time.monotonic());return
  T['elapsed']+=u.GameplayStatics.get_world_delta_seconds(pawn)
  if T['stage']=='settle':
   if T['elapsed']>2:T.update(stage='walk',elapsed=0)
   return
  pos=pawn.get_actor_location();dx=end[0]-pos.x;dy=end[1]-pos.y;dist=(dx*dx+dy*dy)**.5
  pc=u.GameplayStatics.get_player_controller(pawn,0);camera=pc.player_camera_manager.get_camera_location()
  T['samples'].append(dict(t=T['elapsed'],pos=[pos.x,pos.y,pos.z],mode=str(movement.movement_mode),camera=[camera.x,camera.y,camera.z]))
  if dist<45 or T['elapsed']>14:
   movement.stop_movement_immediately();T['results'].append(dict(name=name,reached=dist<45 and abs(pos.z-end[2])<45,distance=dist,final_z=pos.z,expected_z=end[2],samples=T['samples']));u.CarryEditorLibrary.capture_carry_review(str(O/(name+'.png')));T.update(stage='capture',capture_start=time.monotonic());return
  pawn.add_movement_input(u.Vector(dx/dist,dy/dist,0),1.0,True)
 except:
  (O/'walk-error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(route_handle)
route_handle=u.register_slate_post_tick_callback(route_tick)

