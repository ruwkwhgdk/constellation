"""Compare untouched startup physics with real pickup/place. Never toggle physics in setup."""
import json
import time
import traceback
import re
from pathlib import Path
import unreal as u

out=Path(u.Paths.project_dir()).resolve()/'Saved/CarryReview/FirstContact'
out.mkdir(parents=True,exist_ok=True)
trial='-ContactForceTrial' in u.SystemLibrary.get_command_line()
rate_match=re.search(r'-FPS=(\d+)',u.SystemLibrary.get_command_line())
rate=int(rate_match.group(1)) if rate_match else 0
report={'trial':trial,'rows':[],'checks':[]}
force_trial=5000. if '-ContactForce5000' in u.SystemLibrary.get_command_line() else 10000.
editor=u.get_editor_subsystem(u.EditorActorSubsystem)
names=[]
for i,k in enumerate(('Chair','Desk')):
    cls=u.EditorAssetLibrary.load_blueprint_class('/Game/Constellation/Environments/School/Blueprints/BP_School_'+k)
    a=editor.spawn_actor_from_class(cls,u.Vector(180,i*500,3))
    names.append(a.get_name())
u.CarryEditorLibrary.start_carry_review_play()
phase='startup'
elapsed=0.
start=time.monotonic()
index=0
actors=[]
pawn=carry=item=mesh=movement=None
row=None
origin=None

def finish(error=None):
    if error: report['error']=error
    for r in report['rows']:
        report['checks'].append({'name':r['kind']+' '+r['stage']+' moves without launching',
                                'passed':r['physics'] and 5<r['displacement']<200 and r['max_height']<30 and r['max_speed']<300})
    (out/(('trial' if trial else 'baseline')+(str(rate) if rate else '')+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.log('FIRST_CONTACT_RESULT '+json.dumps(report))
    u.unregister_slate_post_tick_callback(token)
    u.SystemLibrary.quit_editor()

def approach(distance):
    p=item.get_actor_location()
    pawn.set_actor_location_and_rotation(u.Vector(p.x-distance,p.y,90),u.Rotator(),False,True)
    pawn.get_controller().set_control_rotation(u.Rotator())
    movement.stop_movement_immediately()
    movement.set_movement_mode(u.MovementMode.MOVE_WALKING)

def begin_contact(label):
    global row,origin
    origin=item.get_actor_location()
    row={'kind':('Chair','Desk')[index],'stage':label,'physics':mesh.is_simulating_physics(),
         'mass':mesh.get_mass(),'awake':mesh.is_any_rigid_body_awake(),
         'damping':mesh.get_linear_damping(),'push':movement.push_force_factor,
         'max_speed':0.,'max_up_speed':0.,'max_height':0.,'displacement':0.,'max_dt':0.,'initial_push':movement.initial_push_force_factor}
    report['rows'].append(row)

def tick(dt):
    global pawn,carry,item,mesh,movement,phase,elapsed,index,actors
    try:
        if time.monotonic()-start>180: raise RuntimeError('timeout '+phase)
        if phase=='startup':
            pawn=u.CarryEditorLibrary.get_carry_review_pawn()
            if not pawn: return
            carry=pawn.get_component_by_class(u.CarryComponent)
            movement=pawn.get_component_by_class(u.CharacterMovementComponent)
            if trial:
                movement.push_force_factor=force_trial
                movement.initial_push_force_factor=300.
            all_actors=u.GameplayStatics.get_all_actors_of_class(pawn,u.Actor)
            actors=[next(a for a in all_actors if a.get_name()==n) for n in names]
            for a in all_actors:
                if 'BP_Holdable_TestBox' in a.get_class().get_name(): a.destroy_actor()
            phase='setup'
        elapsed+=u.GameplayStatics.get_world_delta_seconds(pawn)
        if phase=='setup':
            item=actors[index]
            mesh=item.get_component_by_class(u.StaticMeshComponent)
            approach(180)
            phase='settle'; elapsed=0.
        elif phase=='settle' and elapsed>1:
            begin_contact('untouched_startup')
            phase='contact'; elapsed=0.
        elif phase in ('contact','recontact'):
            if elapsed<1.5: pawn.add_movement_input(u.Vector(1,0,0),1.,False)
            velocity=mesh.get_physics_linear_velocity()
            row['max_dt']=max(row['max_dt'],u.GameplayStatics.get_world_delta_seconds(pawn))
            row['max_speed']=max(row['max_speed'],velocity.length())
            row['max_up_speed']=max(row['max_up_speed'],velocity.z)
            row['max_height']=max(row['max_height'],item.get_actor_location().z-origin.z)
            row['displacement']=max(row['displacement'],(item.get_actor_location()-origin).length())
            if elapsed>3:
                if phase=='recontact':
                    index+=1
                    if index==2: finish(); return
                    phase='setup'; elapsed=0.
                else:
                    approach(105)
                    assert carry.handle_interact(),'pickup interaction'
                    phase='pickup'; elapsed=0.
        elif phase=='pickup' and elapsed>2:
            assert carry.get_held_actor()==item,'pickup did not hold item'
            assert carry.try_place(),'place blocked'
            phase='place'; elapsed=0.
        elif phase=='place' and elapsed>2:
            assert carry.state==u.CarryState.IDLE,'place did not finish'
            approach(180)
            begin_contact('after_pickup_and_place')
            phase='recontact'; elapsed=0.
    except Exception: finish(traceback.format_exc())

token=u.register_slate_post_tick_callback(tick)
