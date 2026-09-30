from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
OUT=Path(u.Paths.project_dir())/'ArtSource/OvergrownHall/Bird/v001'
report=load_current_json((OUT/'unreal_import.json').read_text())
E=u.EditorAssetLibrary; mesh=E.load_asset(report['mesh']); skeleton=E.load_asset(report['skeleton'])
assert isinstance(mesh,u.SkeletalMesh) and mesh.get_editor_property('skeleton')==skeleton
for row,expected in zip(report['clips'],[.5,1,.25,.25]):
    a=E.load_asset(row['path']); assert isinstance(a,u.AnimSequence)
    assert a.get_editor_property('skeleton')==skeleton
    assert abs(a.get_editor_property('sequence_length')-expected)<1e-4
fly=E.load_asset(report['clips'][0]['path'])
u.load_module('AnimationBlueprintLibrary')
poses=[u.AnimationLibrary.get_bone_pose_for_time(fly,'shoulder_L',t,False) for t in [.125,.375]]
qs=[p.rotation for p in poses]
dot=abs(sum(getattr(qs[0],key)*getattr(qs[1],key) for key in ['x','y','z','w']))
assert dot<.99,dot
wrong='/Game/Constellation/Environments/OvergrownHall/Bird/Animations/A_OH_Pigeon_Fly'
registry=u.AssetRegistryHelpers.get_asset_registry(); registry.search_all_assets(True)
options=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=True,include_soft_management_references=True,include_hard_management_references=True)
refs=[str(p) for p in registry.get_referencers(wrong,options)]
out=dict(status='saved_skeleton_and_animation_pass',sampled_wing_rotation_dot=dot,clips=report['clips'],obsolete_misimport=wrong,obsolete_referencers=refs,obsolete_safe_to_delete=not refs,gameplay_path_test='not_run',appearance_review='pending')
(OUT/'unreal_saved_verification.json').write_text(json.dumps(out,indent=2))
u.log('PIGEON_SAVED_CHECK_PASS '+json.dumps(out))
