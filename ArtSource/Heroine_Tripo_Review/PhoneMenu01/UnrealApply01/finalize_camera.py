"""Save only the phone component's visually reviewed camera configuration."""
import unreal as u
import json
from pathlib import Path

P = Path(__file__).parent
bp = u.load_asset("/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine")
sub = u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn = u.SubobjectDataBlueprintFunctionLibrary
components = [
    fn.get_object_for_blueprint(fn.get_data(h), bp)
    for h in sub.k2_gather_subobject_data_for_blueprint(bp)
]
phone = next(o for o in components if isinstance(o, u.PhoneMenuComponent))
phone.set_editor_properties({
    "camera_local": u.Vector(30, -25, 35),
    "camera_rotation": u.Rotator(pitch=-52, yaw=130, roll=0),
    "camera_fov": 65.,
})
u.BlueprintEditorLibrary.compile_blueprint(bp)
assert u.EditorAssetLibrary.save_loaded_asset(bp, False)
(P / "camera-saved.json").write_text(json.dumps({
    "blueprint": bp.get_path_name(),
    "local_cm": [30, -25, 35],
    "rotation_pitch_yaw_roll": [-52, 130, 0],
    "fov": 65,
    "known_alignment_issue_preserved": True,
}, indent=2))
