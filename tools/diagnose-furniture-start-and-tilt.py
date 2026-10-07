"""Read-only PIE diagnostics for actual startup motion and overturned pickup."""
import json
import time
import traceback
from pathlib import Path
import unreal as u

out = Path(u.Paths.project_dir()).resolve() / 'Saved/CarryReview/StartupAndTilt'
out.mkdir(parents=True, exist_ok=True)
report = {'startup': [], 'drops': [], 'pickup': []}
editor = u.get_editor_subsystem(u.EditorActorSubsystem)
classes = [u.EditorAssetLibrary.load_blueprint_class('/Game/Constellation/Environments/School/Blueprints/BP_School_' + k) for k in ('Chair', 'Desk')]
fixtures = []
for i, cls in enumerate(classes):
    actor = editor.spawn_actor_from_class(cls, u.Vector(2600+i*300,-700,150))
    fixtures.append(actor.get_name())
u.CarryEditorLibrary.start_carry_review_play()
phase = 'startup'
elapsed = 0.
start = time.monotonic()
actors = []

def finish():
    (out / 'diagnosis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    u.log('STARTUP_TILT_DONE ' + json.dumps({k:v for k,v in report.items() if k != 'startup'}))
    u.unregister_slate_post_tick_callback(token)
    u.SystemLibrary.quit_editor()

def tick(dt):
    global phase, elapsed, actors
    try:
        if time.monotonic()-start > 180:
            raise RuntimeError('Timeout '+phase)
        pawn = u.CarryEditorLibrary.get_carry_review_pawn()
        if not pawn:
            return
        elapsed += u.GameplayStatics.get_world_delta_seconds(pawn)
        if phase == 'startup':
            for cls in classes:
                for a in u.GameplayStatics.get_all_actors_of_class(pawn,cls):
                    m = a.get_component_by_class(u.StaticMeshComponent)
                    report['startup'].append({'name':a.get_name(),'physics':m.is_simulating_physics(),'gravity':m.is_gravity_enabled(),'awake':m.is_any_rigid_body_awake(),'z':a.get_actor_location().z})
                    if a.get_name() in fixtures:
                        actors.append(a)
                        report['drops'].append({'name':a.get_name(),'start_z':a.get_actor_location().z})
            phase='fall'
            elapsed=0.
        elif phase == 'fall' and elapsed > 2:
            for a,row in zip(actors, report['drops']):
                row['end_z']=a.get_actor_location().z
                row['fell']=row['start_z']-row['end_z']>50
            carry=pawn.get_component_by_class(u.CarryComponent)
            for prop in ('pickup_montage','hold_montage','place_montage','aim_montage','throw_montage'):
                setattr(carry,prop,None)
            for a in actors:
                m=a.get_component_by_class(u.StaticMeshComponent)
                h=a.get_component_by_class(u.HoldableComponent)
                b=m.static_mesh.get_bounds()
                for pitch,roll in ((0,0),(0,90),(0,-90),(0,180),(90,0),(-90,0)):
                    m.set_simulate_physics(False)
                    t=u.Transform(location=u.Vector(2600,-700,0),rotation=u.Rotator(pitch=pitch,roll=roll))
                    center=u.MathLibrary.transform_location(t,b.origin)
                    axes=[u.MathLibrary.transform_direction(t,v) for v in (u.Vector(1,0,0),u.Vector(0,1,0),u.Vector(0,0,1))]
                    support=abs(axes[0].z)*b.box_extent.x+abs(axes[1].z)*b.box_extent.y+abs(axes[2].z)*b.box_extent.z
                    t.translation=u.Vector(2600,-700,support-center.z+.1)
                    a.set_actor_transform(t,False,True)
                    center=u.MathLibrary.transform_location(t,b.origin)
                    pawn.set_actor_location_and_rotation(u.Vector(center.x-105,center.y,90),u.Rotator(),False,True)
                    pawn.get_component_by_class(u.CharacterMovementComponent).set_movement_mode(u.MovementMode.MOVE_WALKING)
                    row={'kind':a.get_class().get_name(),'pitch':pitch,'roll':roll,'selected':carry.try_pick_up(h),'transform':str(t)}
                    if row['selected']:
                        carry.on_pickup_contact()
                        carry.finish_action()
                    row['held']=carry.get_held_actor()==a
                    report['pickup'].append(row)
                    carry.abort_carry()
                a.destroy_actor()
            finish()
    except Exception:
        report['error']=traceback.format_exc()
        finish()

token=u.register_slate_post_tick_callback(tick)
