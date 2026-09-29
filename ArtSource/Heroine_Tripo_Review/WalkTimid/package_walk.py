from pathlib import Path
import json,zipfile,hashlib
P=Path(__file__).resolve().parent
for name in ['validation.json','preview_mesh_audit.json','unreal_import.json','unreal_live_verification.json']:
 assert json.loads((P/name).read_text())['pass'],name
assert json.loads((P/'unreal_import.json').read_text())['source_sha256']==hashlib.sha256((P/'AS_player_heroine_new_Walk_Timid.fbx').read_bytes()).hexdigest()
files=[P/n for n in ['README.md','Heroine_Walk_Timid.blend','AS_player_heroine_new_Walk_Timid.fbx','SK_player_heroine_new_WalkPreview.fbx','Walk_Timid_Preview.gif','Walk_Timid_KeyPoses.jpg','validation.json','preview_mesh_audit.json','unreal_import.json','motion_design.json','garment_weight_fix.json']]
files += [p for p in (P/'SK_player_heroine_new_WalkPreview.fbm').rglob('*') if p.is_file()]
files += [P/'unreal_live_verification.json']
out=P.parent/'Heroine_Walk_Timid_Package.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
 for p in files:z.write(p,p.relative_to(P))
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print(out, out.stat().st_size, 'bytes; CRC verified')
