"""Apply consistent furniture mass and moderate heroine contact forces."""
import json
import shutil
from pathlib import Path
import unreal as u

root = Path(u.Paths.project_dir()).resolve()
out = root / 'Saved/CarryReview/FurniturePhysics'
(out / 'backups').mkdir(parents=True, exist_ok=True)
sub = u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn = u.SubobjectDataBlueprintFunctionLibrary
report = []

def load(path):
    disk = root / ('Content/' + path.removeprefix('/Game/') + '.uasset')
    backup = out / 'backups' / disk.name
    if not backup.exists():
        shutil.copy2(disk, backup)
    bp = u.load_asset(path)
    objects = [fn.get_object(fn.get_data(h)) for h in sub.k2_gather_subobject_data_for_blueprint(bp)]
    return bp, objects

for kind, mass in (('Chair', 8.), ('Desk', 10.)):
    bp, objects = load('/Game/Constellation/Environments/School/Blueprints/BP_School_' + kind)
    mesh = next(c for c in objects if isinstance(c, u.StaticMeshComponent))
    hold = next(c for c in objects if isinstance(c, u.HoldableComponent))
    # Runtime mass is authored in DT_PhysicsProps (setup-physics-props.py).
    mesh.set_mass_override_in_kg('', mass, True)
    mesh.set_linear_damping(.8)
    mesh.set_angular_damping(2.)
    mesh.set_enable_gravity(True)
    mesh.set_simulate_physics(True)
    body = mesh.get_editor_property('body_instance')
    body.set_editor_property('override_max_depenetration_velocity', True)
    body.set_editor_property('max_depenetration_velocity', 100.)
    mesh.set_editor_property('body_instance', body)
    u.BlueprintEditorLibrary.compile_blueprint(bp)
    assert u.EditorAssetLibrary.save_loaded_asset(bp, False)
    report.append({'kind': kind, 'mass_kg': mass, 'initial_physics': True})

bp, objects = load('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine')
movement = next(c for c in objects if isinstance(c, u.CharacterMovementComponent))
for prop, value in {'initial_push_force_factor': 360., 'push_force_factor': 6000.,
                    'push_force_scaled_to_mass': False, 'touch_force_factor': .1,
                    'touch_force_scaled_to_mass': False, 'max_touch_force': 50.}.items():
    movement.set_editor_property(prop, value)
u.BlueprintEditorLibrary.compile_blueprint(bp)
assert u.EditorAssetLibrary.save_loaded_asset(bp, False)
(out / 'settings.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
u.log('FURNITURE_PHYSICS_SETTINGS_SAVED')
