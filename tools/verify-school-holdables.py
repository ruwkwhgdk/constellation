"""Reload furniture assets; verify preserved bounds/materials and physics setup."""
import json
from pathlib import Path
import unreal as u

sub = u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn = u.SubobjectDataBlueprintFunctionLibrary
rows = []
base = '/Game/Constellation/Environments/School/Blueprints/'
for kind, weight in (('Chair', 8), ('Desk', 10)):
    bp = u.load_asset(base + 'BP_School_' + kind)
    objects = {fn.get_object(fn.get_data(h)).get_path_name(): fn.get_object(fn.get_data(h)) for h in sub.k2_gather_subobject_data_for_blueprint(bp)}.values()
    mesh = next(o for o in objects if isinstance(o, u.StaticMeshComponent))
    hold = next(o for o in objects if isinstance(o, u.HoldableComponent))
    source = u.load_asset('/Game/ModulAbandJPSchool/Meshes/Props/SM_School' + kind)
    original = source.get_bounds()
    current = mesh.static_mesh.get_bounds()
    y_offset = -5 if kind == 'Chair' else 0
    expected_origin = u.Vector(original.origin.y * 1.5, -original.origin.x * 1.5 + y_offset, original.origin.z * 1.5)
    expected_extent = u.Vector(original.box_extent.y * 1.5, original.box_extent.x * 1.5, original.box_extent.z * 1.5)
    error = max((current.origin - expected_origin).length(), (current.box_extent - expected_extent).length())
    assert error < .1, (kind, error)
    assert mesh.get_relative_transform().translation.length() < .001
    assert (mesh.get_relative_transform().scale3d - u.Vector(1, 1, 1)).length() < .001
    assert hold.can_throw
    assert mesh.mobility == u.ComponentMobility.MOVABLE
    assert mesh.get_collision_enabled() == u.CollisionEnabled.QUERY_AND_PHYSICS
    body = mesh.get_editor_property('body_instance')
    assert body.get_editor_property('simulate_physics')
    assert body.get_editor_property('override_mass')
    assert abs(body.get_editor_property('mass_in_kg_override') - weight) < .01
    shapes = u.GeometryScript_Collision.get_simple_collision_from_static_mesh(mesh.static_mesh)
    count = u.GeometryScript_Collision.get_simple_collision_shape_count(shapes)
    assert count > 0
    source_materials = [str(m.material_interface) for m in source.get_editor_property('static_materials')]
    current_materials = [str(m.material_interface) for m in mesh.static_mesh.get_editor_property('static_materials')]
    assert source_materials == current_materials
    rows.append({'kind': kind, 'weight_kg': weight, 'bounds_error_cm': error, 'simple_collision_shapes': count, 'materials_preserved': True})
out = Path(u.Paths.project_dir()).resolve() / 'Saved/CarryReview/SchoolFurniture'
(out / 'reload-verification.json').write_text(json.dumps(rows, indent=2))
u.log('SCHOOL_ASSETS_VERIFIED ' + json.dumps(rows))
