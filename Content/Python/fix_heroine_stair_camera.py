"""Enable short spring-arm position lag; safe to run in the existing editor."""
import unreal as u, json
from pathlib import Path
E=u.EditorAssetLibrary
path='/Game/Blueprints/Character/PC/BP_Player_Heroine'
bp=E.load_asset(path)
backup='/Game/Blueprints/Character/PC/CameraBackups/BP_Player_Heroine_BeforeStairCamera'
if not E.does_asset_exist(backup):
    assert E.duplicate_asset(path,backup); assert E.save_asset(backup,only_if_is_dirty=False)
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem); lib=u.SubobjectDataBlueprintFunctionLibrary
arms=[]
for h in sub.k2_gather_subobject_data_for_blueprint(bp):
    obj=lib.get_object_for_blueprint(lib.get_data(h),bp)
    if isinstance(obj,u.SpringArmComponent) and obj.get_name().startswith('SpringArmFollowCamera'): arms.append(obj)
assert len(arms)==1, len(arms)
arm=arms[0]
keys=['enable_camera_lag','camera_lag_speed','camera_lag_max_distance','use_camera_lag_substepping','camera_lag_max_time_step']
before={k:arm.get_editor_property(k) for k in keys}
expected=dict(enable_camera_lag=True,camera_lag_speed=10.0,camera_lag_max_distance=60.0,use_camera_lag_substepping=True,camera_lag_max_time_step=1/120)
for k,v in expected.items(): arm.set_editor_property(k,v)
u.BlueprintEditorLibrary.compile_blueprint(bp)
assert E.save_loaded_asset(bp,only_if_is_dirty=False),'Save blocked; run this script in the editor that owns the asset'
after={k:arm.get_editor_property(k) for k in keys}
for k,v in expected.items():
    assert abs(float(after[k])-float(v))<.00001,(k,after[k],v)
out=Path(u.Paths.project_dir())/'Saved/CameraDiagnostics'; out.mkdir(parents=True,exist_ok=True)
(out/'stair_camera_fix.json').write_text(json.dumps(dict(status='saved_and_properties_verified',asset=path,before=before,after=after,rotation_lag_unchanged=True,collision_test_unchanged=True,playtest='pending'),indent=2))
u.log('STAIR_CAMERA_LAG_SAVED_AND_VERIFIED')
