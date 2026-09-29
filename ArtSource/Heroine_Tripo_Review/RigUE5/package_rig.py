import json,shutil,zipfile,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;D=P/'Delivery'
chains={'retarget_root':'pelvis','coordinate_system':{'forward':'+X','up':'+Z','height_cm':160},'chains':{'Spine':['spine_01','spine_03'],'Neck':['neck_01','head']}}
for side in ['l','r']:
 for label,start,end in [('Arm','upperarm','hand'),('Leg','thigh','ball'),('Clavicle','clavicle','clavicle')]:chains['chains'][label+'_'+side]=[start+'_'+side,end+'_'+side]
 for f in ['thumb','index','middle','ring','pinky']:chains['chains'][f+'_'+side]=[f+'_01_'+side,f+'_03_'+side]
chains['secondary_chains']={**{f'skirt_{i:02}':[f'skirt_{i:02}_01',f'skirt_{i:02}_02'] for i in range(8)},**{n:[n+'_01',n+'_02'] for n in ['hair_side_l','hair_side_r','hair_back_l','hair_back_r']}}
(D/'retarget_chains.json').write_text(json.dumps(chains,indent=2))
(D/'renders').mkdir(exist_ok=True)
for name in ['rest','relaxed','bend','squat','hand']:shutil.copy2(P/'renders'/f'{name}.png',D/'renders'/f'{name}.png')
checks={n:json.loads((D/n).read_text()) for n in ['validation.json','control_validation.json','baked_pose_validation.json','surface_preservation.json','unreal_validation.json']}
assert checks['validation.json']['pass'] and checks['control_validation.json']['pass'] and checks['baked_pose_validation.json']['pass'] and checks['unreal_validation.json']['pass']
assert checks['surface_preservation.json']['surface_geometry_uv_material_indices_exact'] and checks['surface_preservation.json']['packed_texture_bytes_exact']
assert checks['unreal_validation.json']['fbx_sha256']==hashlib.sha256((D/'Heroine_Skeletal.fbx').read_bytes()).hexdigest()
report=checks['validation.json'];names={b['name'] for b in report['skeleton']}
assert all(n in names for pair in list(chains['chains'].values())+list(chains['secondary_chains'].values()) for n in pair)
files=[p for p in D.rglob('*') if p.is_file() and not any(s.endswith('.fbm') for s in p.parts) and p.suffix!='.blend1']
manifest={p.relative_to(D).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(D/'manifest_sha256.json').write_text(json.dumps(manifest,indent=2));files.append(D/'manifest_sha256.json')
out=P.parent/'Heroine_RigUE5_Package.zip'
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for p in files:z.write(p,'Heroine_RigUE5/'+p.relative_to(D).as_posix())
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print('PACKAGE_VERIFIED',out,out.stat().st_size,'files',len(files))
