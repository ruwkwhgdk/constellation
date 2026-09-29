import unreal as u,json
from pathlib import Path
OUT=Path(u.Paths.project_dir())/'ArtSource/OvergrownHall/Bird/Tripo_Rig_v001'
report=json.loads((OUT/'unreal_import.json').read_text())
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
slots=mesh.get_editor_property('materials')
u.log('ACTUAL_MATERIAL '+str([s.material_interface.get_path_name() for s in slots]))
assert slots and '/Tripo/Materials/M_Pigeon_Tripo' in slots[0].material_interface.get_path_name()
out=dict(status='saved_skeleton_material_and_animation_pass',sampled_wing_rotation_dot=dot,clips=report['clips'],material=slots[0].material_interface.get_path_name(),gameplay_path_test='not_run')
(OUT/'unreal_saved_verification.json').write_text(json.dumps(out,indent=2))
u.log('TRIPO_PIGEON_SAVED_PASS '+json.dumps(out))
