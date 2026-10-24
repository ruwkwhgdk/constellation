import unreal as u,json
from pathlib import Path
P=lambda o,k:o.get_editor_property(k)
O=Path(u.Paths.project_dir())/'Saved/S0CinematicPolish';O.mkdir(exist_ok=True)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem);actors=A.get_all_level_actors();by={x.get_actor_label():x for x in actors}
g=by['S0_LittleGirl_Blocking'];comps=g.get_components_by_class(u.SkeletalMeshComponent);c=comps[0] if comps else None;mesh=c.get_skeletal_mesh_asset() if c else None
data=dict(girl_mesh=mesh.get_path_name() if mesh else None,bones=[str(c.get_bone_name(i)) for i in range(c.get_num_bones())] if c else [],components=[str(x) for x in g.get_components_by_class(u.ActorComponent)],girl_rotation=str(g.get_actor_rotation()),girl_bounds=str(g.get_actor_bounds(False)),locker_bounds=str(by['S0_LockerDoor'].get_actor_bounds(False)),stage_region=str(P(by['S0_OpeningStage'],'region_title_class')))
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');s=list(P(a,'steps'));gid=lambda g:tuple(P(g,k) for k in ('a','b','c','d'));ids={gid(P(x,'id')):i for i,x in enumerate(s)}
data['steps']=[dict(i=i,type=str(P(x,'type')),next=[ids[gid(g)] for g in P(x,'next_nodes')],row=str(P(P(x,'dialogue_row'),'row_name')),choices=len(P(x,'choices')),duration=P(x,'duration'),pos=str(P(P(x,'destination'),'value')),rot=str(P(P(x,'rotation'),'value')),action=str(P(P(x,'action_parameters'),'identifier'))) for i,x in enumerate(s)]
data['widgets']=[x for x in u.EditorAssetLibrary.list_assets('/Game/Constellation',recursive=True) if any(k in x.lower() for k in ('regiontitle','tutorial','toast')) and ('/W' in x or '/WB' in x)]
(O/'audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');u.log('S0_POLISH_AUDIT_DONE')
