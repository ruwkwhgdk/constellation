"""Read-only map diagnosis: no map or asset is saved."""
import unreal as u
import json
import traceback
from pathlib import Path
out = Path(u.Paths.project_dir()).resolve() / 'Saved/CarryReview/SchoolPickup'
all_furniture = '-AllSchoolFurniture' in u.SystemLibrary.get_command_line()
if all_furniture:
    out = Path(u.Paths.project_dir()).resolve() / 'Saved/CarryReview/DeskPickup'
out.mkdir(parents=True, exist_ok=True)
report = {'attempts': []}
def diagnose(player):
    actors = u.GameplayStatics.get_all_actors_of_class(player, u.Actor)
    fixtures = [a for a in actors if a.get_class().get_name() in ('BP_School_Chair_C', 'BP_School_Desk_C')]
    fixtures.sort(key=lambda a: (a.get_actor_location() - player.get_actor_location()).length())
    carry = player.get_component_by_class(u.CarryComponent)
    # These same-frame probes test geometry; avoid interrupted montage callbacks
    # from an earlier probe changing the next probe's state. PIE animation is
    # covered separately by review-school-holdables.py.
    for prop in ('pickup_montage', 'hold_montage', 'place_montage', 'aim_montage', 'throw_montage'):
        setattr(carry, prop, None)
    report['count'] = len(fixtures)
    report['player'] = str(player.get_actor_transform())
    report['walk_speed'] = player.get_component_by_class(u.CharacterMovementComponent).max_walk_speed
    for actor in fixtures if all_furniture else fixtures[:32]:
        mesh = actor.get_component_by_class(u.StaticMeshComponent)
        hold = actor.get_component_by_class(u.HoldableComponent)
        original = actor.get_actor_transform()
        origin, extent = actor.get_actor_bounds(False)
        for distance, yaw in [(d, y) for d in ((65, 105) if all_furniture else (105,)) for y in (0, 90, 180, 270)]:
            forward = u.Rotator(yaw=yaw).get_forward_vector()
            pos = actor.get_actor_location() - forward * distance + u.Vector(0, 0, 90)
            player.set_actor_location_and_rotation(pos, u.Rotator(yaw=yaw), False, True)
            player.get_component_by_class(u.CharacterMovementComponent).set_movement_mode(u.MovementMode.MOVE_WALKING)
            row = {'actor': actor.get_name(), 'class': actor.get_class().get_name(), 'yaw': yaw,
                   'distance': distance,
                   'item_transform': str(original), 'bounds': str((origin, extent)), 'carry_offset': str(hold.carry_offset) if hold else None}
            row['selected'] = bool(hold and carry.try_pick_up(hold))
            if row['selected']:
                u.log('SCHOOL_PICKUP_ATTEMPT ' + actor.get_name() + ' yaw=' + str(yaw))
                carry.on_pickup_contact()
                carry.finish_action()
                row['held'] = carry.get_held_actor() == actor
                if not row['held']:
                    try:
                        bounds = mesh.static_mesh.get_bounds()
                        scale = mesh.get_world_transform().scale3d
                        target = u.MathLibrary.transform_location(player.get_actor_transform(), hold.carry_offset.translation)
                        center = u.MathLibrary.transform_location(u.Transform(location=target, rotation=u.Rotator(yaw=yaw)), bounds.origin * scale)
                        extent = bounds.box_extent * scale
                        if yaw in (90,270):
                            extent = u.Vector(extent.y, extent.x, extent.z)
                        overlaps = u.SystemLibrary.box_overlap_actors(player, center, extent, [u.ObjectTypeQuery.OBJECT_TYPE_QUERY1, u.ObjectTypeQuery.OBJECT_TYPE_QUERY2, u.ObjectTypeQuery.OBJECT_TYPE_QUERY3, u.ObjectTypeQuery.OBJECT_TYPE_QUERY4], u.Actor, [player, actor])
                        row['target_overlaps'] = [{'actor': a.get_name(), 'components': [{'name': c.get_name(), 'response': str(c.get_collision_response_to_channel(mesh.get_collision_object_type()))} for c in a.get_components_by_class(u.PrimitiveComponent)]} for a in (overlaps or [])]
                        exact = u.SystemLibrary.component_overlap_actors(mesh, u.Transform(location=target, rotation=u.Rotator(yaw=yaw), scale=scale), [u.ObjectTypeQuery.OBJECT_TYPE_QUERY1, u.ObjectTypeQuery.OBJECT_TYPE_QUERY2, u.ObjectTypeQuery.OBJECT_TYPE_QUERY3, u.ObjectTypeQuery.OBJECT_TYPE_QUERY4], u.Actor, [player, actor])
                        row['target_geometry_overlaps'] = [a.get_name() for a in (exact or [])]
                    except Exception:
                        row['trace_error'] = traceback.format_exc()
                    if all_furniture and actor.get_class().get_name() == 'BP_School_Desk_C':
                        saved_offset = hold.carry_offset
                        row['closer_carry_trials'] = []
                        for x in (60, 50):
                            trial = u.Transform(location=u.Vector(x, 0, -70))
                            hold.carry_offset = trial
                            selected = carry.try_pick_up(hold)
                            if selected:
                                carry.on_pickup_contact()
                                carry.finish_action()
                            row['closer_carry_trials'].append({'x': x, 'selected': selected, 'held': carry.get_held_actor() == actor})
                            carry.abort_carry()
                            mesh.set_simulate_physics(False)
                            actor.set_actor_transform(original, False, True)
                        hold.carry_offset = saved_offset
                carry.abort_carry()
                mesh.set_simulate_physics(False)
                actor.set_actor_transform(original, False, True)
            report['attempts'].append(row)

elapsed = 0
def tick(dt):
    global elapsed
    player = u.CarryEditorLibrary.get_carry_review_pawn()
    if not player:
        return
    elapsed += dt
    if elapsed < 2:
        return
    u.unregister_slate_post_tick_callback(token)
    try:
        diagnose(player)
        cases = [r for r in report['attempts'] if r['distance'] == 105 and (r['actor'], r['yaw']) in (
            ('BP_AbandonedSchool_Chair_C_2', 0), ('BP_AbandonedSchool_Chair_C_2', 90),
            ('BP_AbandonedSchool_Chair_C_5', 0), ('BP_AbandonedSchool_Chair_C_5', 270))]
        report['floor_contact_regression'] = {'count': len(cases), 'passed': len(cases) == 4 and all(r.get('held', False) for r in cases)}
        assert report['floor_contact_regression']['passed'], 'Existing chairs touching the school floor must lift in all four clear approaches'
    except Exception:
        report['error'] = traceback.format_exc()
    (out / 'map-diagnosis.json').write_text(json.dumps(report, indent=2))
    u.log('SCHOOL_PICKUP_DIAGNOSIS_DONE ' + str(len(report['attempts'])))
    u.SystemLibrary.quit_editor()

u.CarryEditorLibrary.start_carry_review_play()
token = u.register_slate_post_tick_callback(tick)
