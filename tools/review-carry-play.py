"""Exercise saved player Blueprint input and animation contacts in a real PIE session."""
import json, traceback, time
from pathlib import Path
import unreal as u
out=Path(u.Paths.project_dir()).resolve()/'Saved/CarryReview'
out.mkdir(parents=True,exist_ok=True)
result={'checks':[],'snapshots':[]}; elapsed=0.; phase='startup'; pawn=None; carry=None; token=None; start=time.monotonic()
last_state=None
movie=out/'play-frames'; movie.mkdir(exist_ok=True)
for old in movie.glob('frame-*.png'): old.unlink()
movie_time=0.; frame_number=0
movie_elapsed=0.; frame_times=[]
thrown_item=None; preview_target=None
# Boundary-weight fixtures keep their per-instance body masses; production props use the table.
for fixture in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    if fixture.get_actor_label().startswith('Carry_Box_'):
        physics=fixture.get_component_by_class(u.PhysicsPropComponent)
        if physics: physics.set_editor_property('physics_row',u.DataTableRowHandle())
u.CarryEditorLibrary.start_carry_review_play()
def check(name,condition):
    result['checks'].append({'name':name,'passed':bool(condition)})
    assert condition,name
def shot(name):
    mesh=pawn.get_component_by_class(u.SkeletalMeshComponent)
    result['snapshots'].append({'name':name,'state':str(carry.state),'location':str(pawn.get_actor_location()),'aim_valid':carry.get_editor_property('aim_valid'),
        'bones':{x:str(mesh.get_socket_location(x)) for x in ('Hips','Head','LeftFoot','LeftHand')},'item':str(carry.get_held_actor().get_actor_transform()) if carry.get_held_actor() else None})
    u.CarryEditorLibrary.capture_carry_review(str(out/(name+'.png')))
def inject(action,value=(1,0,0)):
    assert u.CarryEditorLibrary.inject_carry_review_input('/Game/Constellation/Input/'+action,u.Vector(*value)),action
def finish(error=None):
    if error: result['error']=error
    result['frame_times']=frame_times
    (out/'play-verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    u.log('CARRY_PLAY_REVIEW_RESULT '+json.dumps(result,ensure_ascii=False))
    u.unregister_slate_post_tick_callback(token)
    u.SystemLibrary.quit_editor()
def tick(dt):
    global elapsed,phase,pawn,carry,last_state,thrown_item,preview_target,movie_time,frame_number,movie_elapsed
    try:
        if time.monotonic()-start>180: raise RuntimeError('PIE validation timeout at '+phase)
        if phase=='startup':
            pawn=u.CarryEditorLibrary.get_carry_review_pawn()
            if not pawn: return
            carry=pawn.get_component_by_class(u.CarryComponent)
            result['components']=[x.get_name()+' '+x.get_class().get_name() for x in pawn.get_components_by_class(u.SceneComponent)]
            result['attached_actors']=[x.get_name() for x in pawn.get_attached_actors()]
            result['collision']={x.get_name():str(x.get_collision_enabled()) for x in pawn.get_components_by_class(u.PrimitiveComponent)}
            check('Saved heroine has CarryComponent',carry is not None)
            phase='settle'; elapsed=0
        dt=u.GameplayStatics.get_world_delta_seconds(pawn)
        elapsed+=dt
        if phase not in ('startup','settle'):
            movie_time+=dt; movie_elapsed+=dt
            if movie_time>=1/15:
                movie_time=0; frame_number+=1
                frame_times.append(movie_elapsed)
                u.CarryEditorLibrary.capture_carry_review(str(movie/f'frame-{frame_number:04}.png'))
        if carry.state!=last_state:
            u.log('CARRY_PLAY_STATE '+phase+' '+str(carry.state)+' at '+str(pawn.get_actor_location()))
            last_state=carry.state
        if phase=='settle' and elapsed>2:
            check('Player starts idle',carry.state==u.CarryState.IDLE)
            u.CarryEditorLibrary.use_carry_review_camera(True)
            shot('play-idle')
            phase='pick'; elapsed=0
        elif phase=='pick':
            if elapsed<.15: inject('IA_Interact')
            if elapsed>2:
                if carry.state!=u.CarryState.CARRYING:
                    result['diagnostic']={'state':str(carry.state),'location':str(pawn.get_actor_location()),'ignored_move':pawn.get_controller().is_move_input_ignored(),
                        'direct_interact':carry.handle_interact(),'direct_state':str(carry.state)}
                check('Interact and animation notify reach Carrying',carry.state==u.CarryState.CARRYING)
                check('Held actor attached',carry.get_held_actor().get_attach_parent_actor()==pawn)
                mesh=pawn.get_component_by_class(u.SkeletalMeshComponent)
                errors=[(mesh.get_socket_location('LeftHand' if side else 'RightHand')-carry.get_hand_grip(side).translation).length() for side in (True,False)]
                result['hand_contact_error_cm']=errors
                check('Both hand grips are within 2 cm',max(errors)<=2)
                check('Holding keeps planted feet above floor',mesh.get_socket_location('LeftFoot').z>0 and mesh.get_socket_location('RightFoot').z>0)
                thrown_item=carry.get_held_actor()
                shot('play-holding'); phase='blocked'; elapsed=0
        elif phase=='blocked':
            if elapsed<.15:
                inject('IA_Jump'); inject('IA_Dodge'); inject('IA_Transform')
            if elapsed>.6:
                check('Jump dodge transform preserve carry',carry.state==u.CarryState.CARRYING and not pawn.get_component_by_class(u.CharacterMovementComponent).is_falling())
                phase='place'; elapsed=0
        elif phase=='place':
            if elapsed<.15: inject('IA_Interact')
            if elapsed>2:
                check('Interact and placement notify return to Idle',carry.state==u.CarryState.IDLE)
                shot('play-placed'); phase='repick'; elapsed=0
        elif phase=='repick':
            if elapsed<.15: inject('IA_Interact')
            if elapsed>2:
                check('Placed object can be picked up again',carry.state==u.CarryState.CARRYING)
                u.CarryEditorLibrary.use_carry_review_camera(False)
                phase='aim'; elapsed=0
        elif phase=='aim':
            inject('IA_Attack')
            if elapsed>1:
                check('Held attack enters Aiming',carry.state==u.CarryState.AIMING)
                check('Visible landing prediction valid',carry.get_editor_property('aim_valid'))
                shot('play-aiming'); phase='aim-hold'; elapsed=0
        elif phase=='aim-hold':
            inject('IA_Attack')
            if elapsed>.5:
                preview_target=carry.get_editor_property('aim_location')
                phase='release'; elapsed=0
        elif phase=='release' and elapsed>1.4:
            check('Attack release and notify throw exactly once',carry.state==u.CarryState.IDLE and carry.get_held_actor() is None)
            shot('play-thrown'); phase='end'; elapsed=0
        elif phase=='end' and elapsed>1:
            item=thrown_item.get_component_by_class(u.HoldableComponent)
            if not item.get_editor_property('has_throw_contact') and elapsed<8: return
            result['throw_diagnostic']={'position':str(thrown_item.get_actor_location()),'velocity':str(thrown_item.get_component_by_class(u.StaticMeshComponent).get_physics_linear_velocity())}
            if item.get_editor_property('has_throw_contact'):
                location=item.get_editor_property('throw_contact_location')
                result['first_contact']={'location':str(location),'preview':str(preview_target),'error_cm':(location-preview_target).length()}
            check('Actual first contact follows preview within 10 cm','first_contact' in result and result['first_contact']['error_cm']<=10)
            actors=u.GameplayStatics.get_all_actors_of_class(pawn,u.Actor)
            heavy=next(a for a in actors if a.get_component_by_class(u.HoldableComponent) and a.get_component_by_class(u.HoldableComponent).get_weight_kg()>10)
            heavy.set_actor_location(u.Vector(80,0,21),False,True)
            check('Too-heavy object rejected in PIE',not carry.try_pick_up(heavy.get_component_by_class(u.HoldableComponent)))
            phase='notice'; elapsed=0
        elif phase=='notice' and elapsed>.3:
            widgets=u.WidgetLibrary.get_all_widgets_of_class(pawn,u.CarryNoticeWidget,False)
            check('Too-heavy notice visible in viewport',len(widgets)==1 and widgets[0].is_in_viewport() and widgets[0].get_visibility()==u.SlateVisibility.HIT_TEST_INVISIBLE)
            u.CarryEditorLibrary.capture_carry_review(str(out/'play-too-heavy.png'),True)
            phase='notice-captured'; elapsed=0
        elif phase=='notice-captured' and elapsed>.3: finish()
    except Exception: finish(traceback.format_exc())
token=u.register_slate_post_tick_callback(tick)
