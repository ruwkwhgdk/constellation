import unreal as u,hashlib,json,time
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/ReflectionDistanceApply_20261020';O.mkdir(parents=True,exist_ok=True)
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
if '-Polishfinal' not in u.SystemLibrary.get_command_line():
 assert not (O/'session.json').exists()
 (O/'session.json').write_text(json.dumps(dict(map_sha256=hashlib.sha256(mapfile.read_bytes()).hexdigest())))
exec(compile((R/'tools/review-s0-shallow-rock.py').read_text().replace('ShallowRock_20261019','ReflectionDistanceApply_20261020'),'distance-review','exec'),globals())
pc=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='S0_WetFloor_PlanarReflection').get_component_by_class(u.PlanarReflectionComponent)
if '-Polishfinal' not in cmd:
 assert pc.get_editor_property('max_view_distance_override')==-1
 pc.set_editor_property('max_view_distance_override',8000.0);tag='candidate'
else:assert pc.get_editor_property('max_view_distance_override')==8000.0
shots=[('floor',(2600,0,180),(-8,180)),('reverse',(3050,-2650,1650),(-25,130)),('upper',(1450,1500,1500),(-30,105))]

if '-Polishfinal' not in cmd:shots=[]
else:shots=[('floor',(2600,0,180),(-8,180)),('concept',(2900,900,700),(-20,-138))]


if '-Polishfinal' in cmd:(O/'final-distance.json').write_text(json.dumps(dict(max_view_distance_override=pc.get_editor_property('max_view_distance_override'),screen_percentage=pc.get_editor_property('screen_percentage'))))
