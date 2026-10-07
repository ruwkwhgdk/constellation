"""Configure existing school furniture for carrying, preserving its authored geometry."""
import json
import shutil
from pathlib import Path
import unreal as u

project = Path(u.Paths.project_dir()).resolve()
out = project / 'Saved/CarryReview/SchoolFurniture'
(out / 'backups').mkdir(parents=True, exist_ok=True)
sub = u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn = u.SubobjectDataBlueprintFunctionLibrary
assets = u.GeometryScript_AssetUtils
collision = u.GeometryScript_Collision
hold_class = u.EditorAssetLibrary.load_blueprint_class('/Game/Constellation/Gameplay/Interaction/Components/Ac_Holdable')
rows = []

for kind, weight, offset, grips in (
    ('Chair', 8., (60, 0, -35), ((-15, -27, 65), (-15, 27, 65))),
    ('Desk', 10., (60, 0, -70), ((-37, -26, 105), (-37, 26, 105))),
):
    name = 'BP_School_' + kind
    path = '/Game/Constellation/Environments/School/Blueprints/' + name
    disk = project / ('Content/' + path.removeprefix('/Game/') + '.uasset')
    backup = out / 'backups' / disk.name
    if not backup.exists():
        shutil.copy2(disk, backup)
    bp = u.load_asset(path)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    mesh_handle = next(h for h in handles if isinstance(fn.get_object(fn.get_data(h)), u.StaticMeshComponent))
    mesh = fn.get_object(fn.get_data(mesh_handle))
    baked_path = '/Game/Constellation/Environments/School/Meshes/SM_School' + kind + '_Holdable'
    if mesh.static_mesh.get_path_name().split('.')[0] != baked_path:
        source = mesh.static_mesh
        authored_transform = mesh.get_relative_transform()
        baked = u.load_asset(baked_path) if u.EditorAssetLibrary.does_asset_exist(baked_path) else u.EditorAssetLibrary.duplicate_asset(source.get_path_name(), baked_path)
        assert baked
        # Bake the former child transform into a dedicated copy. The root can then
        # stay identity, so existing actor placement and scale remain unchanged.
        lod_count = assets.get_num_static_mesh_lods_of_type(source, u.GeometryScriptLODType.SOURCE_MODEL)
        assert lod_count > 0
        for lod in range(lod_count):
            dynamic, outcome = assets.copy_mesh_from_static_mesh(source, u.DynamicMesh(), u.GeometryScriptCopyMeshFromAssetOptions(), u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL, lod_index=lod))
            assert outcome == u.GeometryScriptOutcomePins.SUCCESS, str(outcome)
            u.GeometryScript_MeshTransforms.transform_mesh(dynamic, authored_transform)
            _, outcome = assets.copy_mesh_to_static_mesh(dynamic, baked, u.GeometryScriptCopyMeshToAssetOptions(), u.GeometryScriptMeshWriteLOD(lod_index=lod))
            assert outcome == u.GeometryScriptOutcomePins.SUCCESS, str(outcome)
        shapes = collision.get_simple_collision_from_static_mesh(source)
        shapes, success = collision.transform_simple_collision_shapes(shapes, authored_transform, u.GeometryScriptTransformCollisionOptions())
        assert success and collision.get_simple_collision_shape_count(shapes) > 0
        collision.set_simple_collision_of_static_mesh(shapes, baked, u.GeometryScriptSetSimpleCollisionOptions())
        assert u.EditorAssetLibrary.save_loaded_asset(baked, False)
        assert sub.make_new_scene_root(handles[0], mesh_handle, bp)
        mesh.set_static_mesh(baked)
        mesh.set_editor_property('relative_location', u.Vector())
        mesh.set_editor_property('relative_rotation', u.Rotator())
        mesh.set_editor_property('relative_scale3d', u.Vector(1, 1, 1))
    mesh.set_mobility(u.ComponentMobility.MOVABLE)
    mesh.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS)
    mesh.set_mass_override_in_kg('', weight, True)
    mesh.set_linear_damping(.8)
    mesh.set_angular_damping(2.)
    mesh.set_simulate_physics(True)
    body = mesh.get_editor_property('body_instance')
    body.set_editor_property('override_max_depenetration_velocity', True)
    body.set_editor_property('max_depenetration_velocity', 100.)
    mesh.set_editor_property('body_instance', body)
    mesh.set_enable_gravity(True)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    hold = next((fn.get_object(fn.get_data(h)) for h in handles if isinstance(fn.get_object(fn.get_data(h)), u.HoldableComponent)), None)
    if hold is None:
        handle, reason = sub.add_new_subobject(u.AddNewSubobjectParams(parent_handle=handles[0], new_class=hold_class, blueprint_context=bp))
        hold = fn.get_object(fn.get_data(handle))
        assert hold, str(reason)
        sub.rename_subobject(handle, 'Ac_Holdable')
    # Runtime mass is authored in DT_PhysicsProps (setup-physics-props.py).
    hold.set_editor_property('carry_offset', u.Transform(location=u.Vector(*offset)))
    hold.set_editor_property('left_hand_grip', u.Transform(location=u.Vector(*grips[0])))
    hold.set_editor_property('right_hand_grip', u.Transform(location=u.Vector(*grips[1])))
    hold.set_editor_property('can_throw', True)
    u.BlueprintEditorLibrary.compile_blueprint(bp)
    assert u.EditorAssetLibrary.save_loaded_asset(bp, False)
    rows.append({'asset': path, 'weight_kg': weight, 'carry_offset': offset, 'mesh': mesh.static_mesh.get_path_name()})

(out / 'setup.json').write_text(json.dumps(rows, indent=2))
u.log('SCHOOL_HOLDABLE_SETUP ' + json.dumps(rows))
