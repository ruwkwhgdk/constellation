"""Side-only broad facets; upper shoulder vertices, UVs and collision retained."""
import math
E=u.EditorAssetLibrary
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
AS=u.GeometryScript_AssetUtils;Q=u.GeometryScript_MeshQueries
mapping={};reports=[]
for index in [7,9,14]:
 source=E.load_asset(D+'/SM_S0_FracturedMesa_%02d_V10'%index);assert source
 dest=D+'/SM_S0_SideFacets_%02d_V14'%index
 assert not E.does_asset_exist(dest),'Inspect existing candidate rather than overwrite.'
 mesh=E.duplicate_asset(source.get_path_name(),dest);assert mesh
 dynamic=u.DynamicMesh();result=AS.copy_mesh_from_static_mesh(source,dynamic,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD());assert 'SUCCESS' in str(result[-1])
 _,positions,gaps=Q.get_all_vertex_positions(dynamic,False);assert not gaps
 box=source.get_bounding_box();cx=(box.min.x+box.max.x)/2;cy=(box.min.y+box.max.y)/2;rx=(box.max.x-box.min.x)/2;ry=(box.max.y-box.min.y)/2
 count=protected=0;maximum=0
 for vertex,p in enumerate(positions.convert_vector_list_to_array()):
  fade=max(0,min(1,(box.max.z-60-p.z)/140))
  if fade==0:protected+=1;continue
  x=(p.x-cx)/rx;y=(p.y-cy)/ry;r=math.hypot(x,y)
  if r<.65:continue
  angle=math.atan2(y,x);fold=(angle-index*.19+math.pi/5)%(math.tau/5)-math.pi/5
  target=.97/math.cos(fold)
  amount=max(0,target-r)*fade*min(1,(r-.65)/.2)
  dx=x/r*rx*amount;dy=y/r*ry*amount;distance=math.hypot(dx,dy)
  if distance>45:dx*=45/distance;dy*=45/distance
  maximum=max(maximum,math.hypot(dx,dy))
  if abs(dx)+abs(dy)>.0001:count+=1
  assert positions.set_vector_list_item(vertex,u.Vector(p.x+dx,p.y+dy,p.z))
 assert count>0 and protected>0
 u.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(dynamic,positions)
 normals=u.GeometryScriptSplitNormalsOptions();normals.opening_angle_deg=35;normals.split_by_opening_angle=True
 u.GeometryScript_Normals.compute_split_normals(dynamic,normals,u.GeometryScriptCalculateNormalsOptions())
 options=u.GeometryScriptCopyMeshToAssetOptions();options.enable_recompute_normals=False
 result=AS.copy_mesh_to_static_mesh(dynamic,mesh,options,u.GeometryScriptMeshWriteLOD());assert 'SUCCESS' in str(result[-1])
 collision=source.get_editor_property('complex_collision_mesh');assert collision
 mesh.set_editor_property('complex_collision_mesh',collision)
 mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 assert E.save_loaded_asset(mesh,False)
 mapping[source.get_path_name()]=mesh
 reports.append(dict(mesh=mesh.get_path_name(),source=source.get_path_name(),collision=collision.get_path_name(),protected_upper_vertices=protected,changed_side_vertices=count,max_displacement_cm=maximum))
names={r['name'] for r in json.loads((R/'Saved/S0WetFloor/ShapePass_20261017/allowed-mesh-changes.json').read_text())}
changes=[]
for a in A.get_all_level_actors():
 if a.get_name() not in names:continue
 c=a.static_mesh_component;old=c.static_mesh.get_path_name();assert old in mapping
 materials=list(c.get_materials());c.set_static_mesh(mapping[old])
 for i,m in enumerate(materials):c.set_material(i,m)
 changes.append(dict(name=a.get_name(),label=a.get_actor_label(),old=old,new=c.static_mesh.get_path_name()))
assert len(changes)==len(names)
(O/'variants.json').write_text(json.dumps(reports,indent=2));(O/'changes.json').write_text(json.dumps(changes,indent=2))
tag='art1';S.update(i=0,sent=False,t=time.monotonic())
