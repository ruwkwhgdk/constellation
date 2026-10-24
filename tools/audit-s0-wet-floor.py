import unreal as u, json
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/20261017';O.mkdir(parents=True,exist_ok=True)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
rows=[]
def v(p):return [p.x,p.y,p.z]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 p=a.get_actor_location();folder=str(a.get_folder_path());label=a.get_actor_label()
 if 'start' not in (folder+' '+label).lower() and not (-1500<p.x<4500 and -4500<p.y<4500 and -1000<p.z<3000):continue
 c,e=a.get_actor_bounds(False);comps=[]
 for s in a.get_components_by_class(u.StaticMeshComponent):
  comps.append(dict(name=s.get_name(),mesh=s.static_mesh.get_path_name() if s.static_mesh else '',materials=[m.get_path_name() if m else '' for m in s.get_materials()]))
 rows.append(dict(name=a.get_name(),label=label,folder=folder,cls=a.get_class().get_name(),pos=v(p),scale=v(a.get_actor_scale3d()),center=v(c),extent=v(e),meshes=comps))
(O/'actors.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
u.log('S0_WET_AUDIT_COMPLETE')
