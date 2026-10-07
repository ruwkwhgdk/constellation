"""Exercise saved furniture in L_Carry_Review PIE; launch with -RenderOffscreen."""
import json
import time
import traceback
from pathlib import Path
import unreal as u

assert '-RenderOffscreen' in u.SystemLibrary.get_command_line(), 'Use -RenderOffscreen so viewport focus loss does not cancel aiming.'

out = Path(u.Paths.project_dir()).resolve() / 'Saved/CarryReview/SchoolFurniture'
out.mkdir(parents=True, exist_ok=True)
physics_table=u.load_asset('/Game/Constellation/Gameplay/Interaction/Data/DT_PhysicsProps')
assert u.DataTableFunctionLibrary.export_data_table_to_json_file(physics_table,str(out/'physics-rows.json'))
physics_rows={r['Name']:r for r in json.loads((out/'physics-rows.json').read_text(encoding='utf-8-sig'))}
report = {'checks': []}
phase = 'startup'
elapsed = 0.
index = 0
pawn = carry = item = None
start = time.monotonic()
names = ['Chair', 'Desk']
base = '/Game/Constellation/Environments/School/Blueprints/'
report['asset_base'] = base
actual_map = '-SchoolActualMap' in u.SystemLibrary.get_command_line()
report['actual_school_map'] = actual_map
pickup_only = '-SchoolPickupOnly' in u.SystemLibrary.get_command_line()
report['pickup_only'] = pickup_only
editor = u.get_editor_subsystem(u.EditorActorSubsystem)
fixture_classes = []
report['editor_fixtures'] = []
for fixture_index, kind in enumerate(names):
    cls = u.EditorAssetLibrary.load_blueprint_class(base + 'BP_School_' + kind)
    fixture_classes.append(cls)
    if actual_map:
        continue
    fixture = editor.spawn_actor_from_class(cls, u.Vector(1000 + fixture_index * 300, 0, 3))
    assert fixture
    report['editor_fixtures'].append({'path': fixture.get_path_name(), 'class': fixture.get_class().get_path_name(), 'location': str(fixture.get_actor_location()), 'editor_only': fixture.get_editor_property('is_editor_only_actor')})
u.CarryEditorLibrary.start_carry_review_play()

def check(name, passed):
    report['checks'].append({'name': names[index] + ': ' + name, 'passed': bool(passed)})
    assert passed, name

def snapshot():
    mesh = item.get_component_by_class(u.StaticMeshComponent)
    movement = pawn.get_component_by_class(u.CharacterMovementComponent)
    return {'item': str(item.get_actor_transform()), 'pawn': str(pawn.get_actor_transform()),
            'distance': (item.get_actor_location() - pawn.get_actor_location()).length(),
            'velocity': str(mesh.get_physics_linear_velocity()), 'mass': mesh.get_mass(),
            'physics': mesh.is_simulating_physics(), 'collision': str(mesh.get_collision_enabled()),
            'falling': movement.is_falling(), 'state': str(carry.state),
            'push_force': movement.push_force_factor, 'initial_push': movement.initial_push_force_factor,
            'touch_force': movement.touch_force_factor}

def finish(error=None):
    if error:
        report['error'] = error
    (out / 'play-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    u.log('SCHOOL_PLAY_RESULT ' + json.dumps({k: v for k, v in report.items() if k != 'pie_actors'}))
    u.unregister_slate_post_tick_callback(token)
    u.SystemLibrary.quit_editor()

def spawn():
    cls = fixture_classes[index]
    if actual_map:
        target_name = 'BP_AbandonedSchool_' + names[index] + '_C_2'
        actor = next(a for a in u.GameplayStatics.get_all_actors_of_class(pawn, cls) if a.get_name() == target_name)
        yaw = 0 if index == 0 else 180
        rotation = u.Rotator(yaw=yaw)
        distance = 65 if index == 1 and '-SchoolClosePickup' in u.SystemLibrary.get_command_line() else 105
        pos = actor.get_actor_location() - rotation.get_forward_vector() * distance + u.Vector(0, 0, 90)
        pawn.set_actor_location_and_rotation(pos, rotation, False, True)
        pawn.get_controller().set_control_rotation(rotation)
        pawn.get_component_by_class(u.CharacterMovementComponent).set_movement_mode(u.MovementMode.MOVE_WALKING)
        return actor
    pos = pawn.get_actor_location() + pawn.get_actor_forward_vector() * 105
    pos.z = 3
    transform = u.Transform(location=pos, rotation=pawn.get_actor_rotation())
    actor = u.GameplayStatics.get_all_actors_of_class(pawn, cls)[0]
    if '-SchoolTiltedPickup' in u.SystemLibrary.get_command_line():
        bounds = actor.get_component_by_class(u.StaticMeshComponent).static_mesh.get_bounds()
        transform = u.Transform(location=pos, rotation=u.Rotator(roll=90))
        center = u.MathLibrary.transform_location(transform, bounds.origin)
        transform.translation = u.Vector(pos.x, pos.y, bounds.box_extent.y - (center.z-pos.z) + .1)
    actor.set_actor_transform(transform, False, True)
    return actor

def tick(dt):
    global phase, elapsed, index, pawn, carry, item
    try:
        if time.monotonic() - start > 180:
            raise RuntimeError('PIE timeout at ' + phase)
        if phase == 'startup':
            pawn = u.CarryEditorLibrary.get_carry_review_pawn()
            if not pawn:
                return
            carry = pawn.get_component_by_class(u.CarryComponent)
            report['normal_walk_speed'] = pawn.get_component_by_class(u.CharacterMovementComponent).max_walk_speed
            assert carry.settings_row.data_table and str(carry.settings_row.row_name) == 'Default'
            assert str(carry.get_carry_message('TooHeavy')) == '너무 무거워서 들 수 없습니다.'
            report['carry_settings_table'] = carry.settings_row.data_table.get_path_name()
            for actor in u.GameplayStatics.get_all_actors_of_class(pawn, u.Actor):
                if 'BP_Holdable_TestBox' in actor.get_class().get_name():
                    actor.destroy_actor()
            phase = 'settle'
            elapsed = 0
        elapsed += u.GameplayStatics.get_world_delta_seconds(pawn)
        if phase == 'settle' and elapsed > 2:
            item = spawn()
            hold = item.get_component_by_class(u.HoldableComponent)
            mesh = item.get_component_by_class(u.StaticMeshComponent)
            report[names[index] + '_initial'] = snapshot()
            check('Physics active before first pickup', mesh.is_simulating_physics())
            check('Physical mass matches lifting weight', abs(mesh.get_mass() - physics_rows['School'+names[index]]['MassKg']) < .01)
            check('Ac_Holdable component exists', hold and hold.get_class().get_name() == 'Ac_Holdable_C')
            check('Item settings row assigned', bool(hold.item_row.data_table) and str(hold.item_row.row_name) == 'School' + names[index])
            check('Static mesh is root', item.root_component == mesh)
            check('Within player lifting limit', hold.get_weight_kg() <= carry.character_weight_kg * carry.lift_weight_ratio + .0001)
            check('Interaction accepts furniture', carry.handle_interact())
            anim = pawn.get_component_by_class(u.SkeletalMeshComponent).get_anim_instance()
            check('Pickup montage plays at double speed', abs(anim.montage_get_play_rate(carry.pickup_montage)-2.) < .01)
            phase = 'pick'
            elapsed = 0
        elif phase == 'pick' and elapsed > 2:
            check('Pickup animation reaches Carrying', carry.state == u.CarryState.CARRYING and carry.get_held_actor() == item)
            check('Other actions blocked; walking allowed', carry.blocks_other_actions() and carry.allows_walking())
            check('Normal walking speed preserved', abs(pawn.get_component_by_class(u.CharacterMovementComponent).max_walk_speed - report['normal_walk_speed']) < .01)
            check('Held mesh collision disabled', item.get_component_by_class(u.StaticMeshComponent).get_collision_enabled() == u.CollisionEnabled.NO_COLLISION)
            if pickup_only:
                carry.abort_carry()
                if index == len(names)-1:
                    finish()
                    return
                index += 1
                phase = 'settle'
                elapsed = 0
                return
            check('Placement accepted', carry.try_place())
            anim = pawn.get_component_by_class(u.SkeletalMeshComponent).get_anim_instance()
            check('Place montage plays at double speed', abs(anim.montage_get_play_rate(carry.place_montage)-2.) < .01)
            phase = 'place'
            elapsed = 0
        elif phase == 'place' and elapsed > 2:
            report[names[index] + '_placed'] = snapshot()
            check('Placement releases furniture', carry.state == u.CarryState.IDLE and item.get_component_by_class(u.StaticMeshComponent).is_simulating_physics())
            check('Can pick up again through interaction', carry.handle_interact())
            phase = 'repick'
            elapsed = 0
        elif phase == 'repick' and elapsed > 2:
            check('Re-pick reaches Carrying', carry.state == u.CarryState.CARRYING and carry.get_held_actor() == item)
            check('Aim starts', carry.begin_aim())
            phase = 'aim'
            elapsed = 0
        elif phase == 'aim' and elapsed > .5:
            report[names[index] + '_aim'] = {'valid': carry.aim_valid, 'target': str(carry.aim_location), 'item_transform': str(item.get_actor_transform()), 'pawn_transform': str(pawn.get_actor_transform())}
            check('Landing preview has valid trajectory', carry.aim_valid)
            check('Throw accepted', carry.commit_throw())
            phase = 'throw'
            elapsed = 0
        elif phase == 'throw' and elapsed > 2:
            check('Throw releases to physics and unlocks player', carry.state == u.CarryState.IDLE and item.get_component_by_class(u.StaticMeshComponent).is_simulating_physics())
            item.destroy_actor()
            if index == len(names)-1:
                finish()
                return
            index += 1
            phase = 'settle'
            elapsed = 0
    except Exception:
        finish(traceback.format_exc())

token = u.register_slate_post_tick_callback(tick)
