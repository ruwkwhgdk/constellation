"""PIE contact regression. Uses review map fixtures; never saves the map."""
import json
import time
import traceback
from pathlib import Path
import unreal as u

out = Path(u.Paths.project_dir()).resolve() / 'Saved/CarryReview/FurniturePhysics'
out.mkdir(parents=True, exist_ok=True)
baseline = '-FurnitureBaseline' in u.SystemLibrary.get_command_line()
report = {'baseline': baseline, 'items': [], 'checks': []}
editor = u.get_editor_subsystem(u.EditorActorSubsystem)
classes = [u.EditorAssetLibrary.load_blueprint_class('/Game/Constellation/Environments/School/Blueprints/BP_School_' + kind) for kind in ('Chair', 'Desk')]
for i, cls in enumerate(classes):
    assert editor.spawn_actor_from_class(cls, u.Vector(1000+i*400, 0, 3))
u.CarryEditorLibrary.start_carry_review_play()
phase = 'startup'
elapsed = 0.
index = 0
start = time.monotonic()
pawn = item = mesh = None
row = None

def finish(error=None):
    if error:
        report['error'] = error
    (out / ('push-before.json' if baseline else 'push-after.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
    u.log('FURNITURE_PHYSICS_RESULT ' + json.dumps(report))
    u.unregister_slate_post_tick_callback(token)
    u.SystemLibrary.quit_editor()

def tick(dt):
    global pawn, item, mesh, phase, elapsed, index, row
    try:
        if time.monotonic() - start > 180:
            raise RuntimeError('Timeout at ' + phase)
        if phase == 'startup':
            pawn = u.CarryEditorLibrary.get_carry_review_pawn()
            if not pawn:
                return
            for a in u.GameplayStatics.get_all_actors_of_class(pawn, u.Actor):
                if 'BP_Holdable_TestBox' in a.get_class().get_name():
                    a.destroy_actor()
            phase = 'setup'
        if phase == 'setup':
            movement = pawn.get_component_by_class(u.CharacterMovementComponent)
            movement.stop_movement_immediately()
            pawn.set_actor_location_and_rotation(u.Vector(0,0,90), u.Rotator(), False, True)
            pawn.get_controller().set_control_rotation(u.Rotator())
            movement.set_movement_mode(u.MovementMode.MOVE_WALKING)
            item = u.GameplayStatics.get_all_actors_of_class(pawn, classes[index])[0]
            mesh = item.get_component_by_class(u.StaticMeshComponent)
            initial_physics = mesh.is_simulating_physics()
            # Baseline reproduces a previously released object, which was the only
            # way these assets enabled simulation and applied their lifting mass.
            mesh.set_simulate_physics(False)
            item.set_actor_transform(u.Transform(location=u.Vector(180,0,3)), False, True)
            if baseline:
                mesh.set_mass_override_in_kg('', 5 if index == 0 else 9, True)
            mesh.set_simulate_physics(True)
            mesh.set_physics_linear_velocity(u.Vector())
            mesh.set_physics_angular_velocity_in_degrees(u.Vector())
            row = {'kind': ('Chair','Desk')[index], 'initial_physics': initial_physics,
                   'mass': mesh.get_mass(), 'push_force': movement.push_force_factor,
                   'max_height': 0., 'max_up_speed': 0., 'max_speed': 0., 'min_distance': 9999.}
            report['items'].append(row)
            phase = 'settle'
            elapsed = 0.
        elapsed += u.GameplayStatics.get_world_delta_seconds(pawn)
        if phase == 'settle' and elapsed > 1:
            phase = 'push'
            elapsed = 0.
        elif phase == 'push':
            if elapsed < 1.0:
                pawn.add_movement_input(u.Vector(1,0,0), 1., False)
            velocity = mesh.get_physics_linear_velocity()
            row['max_height'] = max(row['max_height'], item.get_actor_location().z)
            row['max_up_speed'] = max(row['max_up_speed'], velocity.z)
            row['max_speed'] = max(row['max_speed'], velocity.length())
            row['min_distance'] = min(row['min_distance'], (item.get_actor_location()-pawn.get_actor_location()).length())
            if elapsed > 3:
                for name, passed in [('Initial physics active', row['initial_physics']),
                                     ('Walking contact does not launch furniture', row['max_height'] < 100 and row['max_up_speed'] < 300 and row['max_speed'] < 700)]:
                    report['checks'].append({'name': row['kind'] + ': ' + name, 'passed': bool(passed)})
                item.destroy_actor()
                index += 1
                if index == 2:
                    finish()
                    return
                phase = 'setup'
    except Exception:
        finish(traceback.format_exc())

token = u.register_slate_post_tick_callback(tick)
