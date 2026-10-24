import unreal as u,json
from pathlib import Path
out=Path(u.Paths.project_dir())/'Saved/Minimap'
w=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
rows=[]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 loc=a.get_actor_location();center,ext=a.get_actor_bounds(False)
 row=dict(name=a.get_name(),label=a.get_actor_label(),cls=a.get_class().get_name(),path=a.get_path_name(),location=[loc.x,loc.y,loc.z],bounds=[[center.x,center.y,center.z],[ext.x,ext.y,ext.z]],tags=[str(t) for t in a.tags],meshes=[])
 for c in a.get_components_by_class(u.StaticMeshComponent):
  m=c.get_editor_property('static_mesh')
  if m:
   p=c.get_world_location();rot=c.get_world_rotation();sc=c.get_world_scale()
   row['meshes'].append(dict(name=c.get_name(),mesh=m.get_path_name(),pos=[p.x,p.y,p.z],rot=[rot.pitch,rot.yaw,rot.roll],scale=[sc.x,sc.y,sc.z]))
 rows.append(row)
(out/'school-actors.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
for path in ['/Game/Constellation/Environments/School/Blueprints/BP_School_Door','/Game/Constellation/Environments/School/Blueprints/BP_School_Trapdoor','/Game/Constellation/Gameplay/Interaction/Actors/BP_Ladder']:
 a=u.load_asset(path)
 if a:(out/(path.split('/')[-1]+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(a),encoding='utf8')
u.log('MINIMAP_AUDIT_COMPLETE '+str(len(rows)))
