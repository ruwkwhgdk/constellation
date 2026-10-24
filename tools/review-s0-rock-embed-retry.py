"""Fresh session guard before loading map; use -Polishfinal for reload review."""
import unreal as u,hashlib,json,time
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/RockEmbedRetry_20261020'
O.mkdir(parents=True,exist_ok=True)
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
if '-Polishfinal' not in u.SystemLibrary.get_command_line():
 assert not (O/'session.json').exists(),'Use a new output directory for another session'
 (O/'session.json').write_text(json.dumps(dict(map_sha256=hashlib.sha256(mapfile.read_bytes()).hexdigest(),started_unix=time.time()),indent=2))
source=(R/'tools/review-s0-shallow-rock.py').read_text().replace('ShallowRock_20261019','RockEmbedRetry_20261020')
exec(compile(source,str(R/'tools/review-s0-shallow-rock.py'),'exec'),globals())



if '-Polishfinal' not in u.SystemLibrary.get_command_line():shots=[]
else:shots=[('backwall',(1700,400,300),(5,90)),('concept',(2900,900,700),(-20,-138))]




