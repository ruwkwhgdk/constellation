import unreal as u,json,hashlib,time
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/WindowShadowV21_20261019';O.mkdir(parents=True,exist_ok=True)
if '-Polishfinal' not in u.SystemLibrary.get_command_line():
 assert not (O/'session.json').exists()
 (O/'session.json').write_text(json.dumps(dict(map_sha256=hashlib.sha256((R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap').read_bytes()).hexdigest())))
s=(R/'tools/review-s0-shallow-rock.py').read_text().replace('ShallowRock_20261019','WindowShadowV21_20261019')
exec(compile(s,'review-s0-shallow-rock.py','exec'),globals())
if '-Polishfinal' not in cmd:shots=[]
else:shots=[('floor',(2600,0,180),(-8,180)),('reverse',(3050,-2650,1650),(-25,130))]
