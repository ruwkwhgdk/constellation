import unreal as u,json
from pathlib import Path
P=lambda o,k:o.get_editor_property(k)
R=Path(u.Paths.project_dir())/'Saved/S0ExitRevision';R.mkdir(exist_ok=True)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');steps=[]
guid=lambda g:','.join(str(P(g,k)) for k in ['a','b','c','d'])
vec=lambda v:[v.x,v.y,v.z]
for s in P(a,'steps'):
 d={k:str(P(s,k)) for k in ['id','type','role','duration','wait_for_completion','next_nodes','destination','motion_points','action_parameters','animation']}
 d.update(id=guid(P(s,'id')),next=[guid(g) for g in P(s,'next_nodes')],dest=vec(P(P(s,'destination'),'value')),points=[dict(t=P(pt,'time'),pos=vec(P(pt,'position'))) for pt in P(s,'motion_points')]);steps.append(d)
actors=[]
for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 p=actor.get_actor_location();label=actor.get_actor_label()
 if (300<p.x<600) or label.startswith('S0_'):
  actors.append(dict(label=label,path=actor.get_path_name(),class_name=actor.get_class().get_name(),position=str(p),bounds=str(actor.get_actor_bounds(False)),meshes=[c.static_mesh.get_path_name() for c in actor.get_components_by_class(u.StaticMeshComponent) if c.static_mesh]))
(R/'audit.json').write_text(json.dumps(dict(steps=steps,actors=actors,compile=str(u.SceneDirectorLibrary.compile_director(a))),ensure_ascii=False,indent=2),encoding='utf8')
