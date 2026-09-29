import unreal,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;B='/Game/Resources/Characters/PC/player_heroine_new'
audit=json.loads((P/'unreal_cleanup_audit.json').read_text())
for asset in audit:assert not unreal.EditorAssetLibrary.does_asset_exist(asset),asset
base=P.parent/'RunSoft'
for name in ['Natural','Retarget','Polish']:assert not (P.parent/('Run'+name)).exists()
for name in ['Run_Soft','Walk_Timid']:
 a=unreal.load_asset(B+'/Animations/AS_player_heroine_new_'+name);assert a
 if name=='Run_Soft':assert abs(a.sequence_length-1)<.001
m=unreal.load_asset(B+'/SK_player_heroine_new_RunPreview');src=m.get_editor_property('asset_import_data').get_first_filename()
assert Path(src).resolve()==(base/'SK_player_heroine_new_RunPreview.fbx').resolve()
assert Path(src).is_file()
old=json.loads((base/'unreal_verification.json').read_text())
assert old['source_sha256']==hashlib.sha256((base/'AS_player_heroine_new_Run_Soft.fbx').read_bytes()).hexdigest()
report={'pass':True,'removed_assets':[a for a,v in audit.items() if v['exists']],'mesh_source':src,'final_animation_unchanged':True,'walk_preserved':True}
(P/'cleanup_verified.json').write_text(json.dumps(report,indent=2))
print('CLEANUP_VERIFIED',json.dumps(report))
