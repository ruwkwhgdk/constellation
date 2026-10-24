"""Dedicated rock variants: planar side fractures, unchanged upper vertices.
Original meshes remain the explicit complex-collision source.
Run inside the held S0 shape review session.
"""
import math,re
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
AS=u.GeometryScript_AssetUtils;Q=u.GeometryScript_MeshQueries
variants={};reports=[]
for index in [7,9,14]:
 source=E.load_asset('/Game/LuosCaves/Meshes/Props_Mesas/SM_LCave_P_Mesa_%02d'%index)
 dest=D+'/SM_S0_FracturedMesa_%02d_V10'%index
 mesh=E.load_asset(dest) if E.does_asset_exist(dest) else E.duplicate_asset(source.get_path_name(),dest)
 assert mesh
 prior=mesh.get_editor_property('complex_collision_mesh')
 assert prior is None or prior==source
 dynamic=u.DynamicMesh()
 result=AS.copy_mesh_from_static_mesh(source,dynamic,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD())
 assert 'SUCCESS' in str(result[-1]),str(result)
 _,positions,gaps=Q.get_all_vertex_positions(dynamic,False);assert not gaps
 box=source.get_bounding_box();cx=(box.min.x+box.max.x)/2;cy=(box.min.y+box.max.y)/2
 rx=(box.max.x-box.min.x)/2;ry=(box.max.y-box.min.y)/2
 protected=0;changed=0;max_delta=0
 for vertex,p in enumerate(positions.convert_vector_list_to_array()):
  # The flat top and its shoulder are exactly preserved; alter only deeper sides.
  fade=max(0.,min(1.,(box.max.z-45-p.z)/100.))
  if fade==0:protected+=1;continue
  x=(p.x-cx)/rx;y=(p.y-cy)/ry
  angle=math.atan2(y,x)-index*.17
  fold=(angle+math.pi/7)%(math.tau/7)-math.pi/7
  # Circumscribed facets only expand the side silhouette, avoiding seams between rocks.
  factor=1/max(.85,math.cos(fold))
  dx=(p.x-cx)*(factor-1)*fade;dy=(p.y-cy)*(factor-1)*fade
  distance=math.hypot(dx,dy)
  if distance>48:dx*=48/distance;dy*=48/distance
  delta=math.hypot(dx,dy);max_delta=max(max_delta,delta)
  if delta>.0001:changed+=1
  assert positions.set_vector_list_item(vertex,u.Vector(p.x+dx,p.y+dy,p.z))
 assert protected and changed
 u.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(dynamic,positions)
 normals=u.GeometryScriptSplitNormalsOptions();normals.set_editor_property('opening_angle_deg',32.);normals.set_editor_property('split_by_opening_angle',True)
 u.GeometryScript_Normals.compute_split_normals(dynamic,normals,u.GeometryScriptCalculateNormalsOptions())
 options=u.GeometryScriptCopyMeshToAssetOptions();options.set_editor_property('enable_recompute_normals',False)
 result=AS.copy_mesh_to_static_mesh(dynamic,mesh,options,u.GeometryScriptMeshWriteLOD())
 assert 'SUCCESS' in str(result[-1]),str(result)
 mesh.set_editor_property('complex_collision_mesh',source)
 mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 assert E.save_loaded_asset(mesh,False)
 assert mesh.get_editor_property('complex_collision_mesh')==source
 variants[source.get_path_name()]=mesh
 reports.append(dict(mesh=mesh.get_path_name(),collision_source=source.get_path_name(),protected_upper_vertices=protected,changed_side_vertices=changed,max_local_displacement_cm=max_delta))
changes=[]
for a in A.get_all_level_actors():
 c=a.get_component_by_class(u.StaticMeshComponent)
 if not c or not c.static_mesh:continue
 old=c.static_mesh.get_path_name();center,extent=a.get_actor_bounds(False)
 if old not in variants or not (0<center.x<3400 and -2900<center.y<-1100 and center.z<1100):continue
 materials=list(c.get_materials());c.set_static_mesh(variants[old])
 for i,m in enumerate(materials):c.set_material(i,m)
 changes.append(dict(name=a.get_name(),label=a.get_actor_label(),component=c.get_name(),old=old,new=c.static_mesh.get_path_name()))
assert changes
(O/'mesh-variants.json').write_text(json.dumps(reports,indent=2));(O/'allowed-mesh-changes.json').write_text(json.dumps(changes,indent=2))
tag='shape2';S.update(i=0,sent=False,t=time.monotonic())
