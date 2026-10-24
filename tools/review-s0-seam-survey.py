"""Fresh session guard before loading map; use -Polishfinal for reload review."""
import unreal as u,hashlib,json,time
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/SeamSurvey_20261019'
O.mkdir(parents=True,exist_ok=True)
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
if '-Polishfinal' not in u.SystemLibrary.get_command_line():
 assert not (O/'session.json').exists(),'Use a new output directory for another session'
 (O/'session.json').write_text(json.dumps(dict(map_sha256=hashlib.sha256(mapfile.read_bytes()).hexdigest(),started_unix=time.time()),indent=2))
source=(R/'tools/review-s0-shallow-rock.py').read_text().replace('ShallowRock_20261019','SeamSurvey_20261019')
exec(compile(source,str(R/'tools/review-s0-shallow-rock.py'),'exec'),globals())



if '-Polishfinal' not in u.SystemLibrary.get_command_line():shots=[]
else:shots=[('backwall',(1700,400,300),(5,90)),('concept',(2900,900,700),(-20,-138))]


measured=[]
for a in A.get_all_level_actors():
 p=a.get_actor_location()
 if -1000<p.x<3500 and 1500<p.y<2900:
  center,extent=a.get_actor_bounds(False)
  measured.append(dict(name=a.get_name(),label=a.get_actor_label(),center=[center.x,center.y,center.z],extent=[extent.x,extent.y,extent.z]))
(O/'bounds.json').write_text(json.dumps(measured,indent=2))
shots=[('junction',(2600,900,700),(0,110))]

