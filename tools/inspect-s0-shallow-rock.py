import re
records=[]
world=u.EditorLevelLibrary.get_editor_world()
for a in A.get_all_level_actors():
 if a.get_actor_label()=='classroom_start_floor_22' or a.get_name() in ['StaticMeshActor_831','StaticMeshActor_833']:
  center,extent=a.get_actor_bounds(False)
  c=a.get_component_by_class(u.StaticMeshComponent)
  records.append(dict(name=a.get_name(),label=a.get_actor_label(),center=[center.x,center.y,center.z],extent=[extent.x,extent.y,extent.z],transform=str(a.get_actor_transform()),collision=str(c.get_collision_enabled())))
hits=[]
for x in [1000,1300,1600,2200,2600,3000]:
 for z in [100,300,600]:
  hit=u.SystemLibrary.line_trace_single(world,u.Vector(x,1500,z),u.Vector(x,2100,z),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],u.DrawDebugTrace.NONE,True)
  hits.append(dict(x=x,z=z,result=hit.export_text() if hit else None))
(O/'junction-inspection.json').write_text(json.dumps(dict(actors=records,traces=hits),indent=2))


