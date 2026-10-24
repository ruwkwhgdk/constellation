"""Candidate: preserve source XY outline; embed asymmetric rim into wall along depth."""
import math
E=u.EditorAssetLibrary;AS=u.GeometryScript_AssetUtils;Q=u.GeometryScript_MeshQueries
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
actors={a.get_name():a for a in A.get_all_level_actors()};changes=[];audit=[]
for index,name in enumerate(['StaticMeshActor_831','StaticMeshActor_833']):
 a=actors[name];c=a.static_mesh_component;source=c.static_mesh
 dest=D+'/SM_S0_EmbeddedRock_V22_'+str(index)
 assert not E.does_asset_exist(dest),'Do not overwrite an existing candidate'
 mesh=E.duplicate_asset(source.get_path_name(),dest);assert mesh
 d=u.DynamicMesh();result=AS.copy_mesh_from_static_mesh(source,d,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD());assert 'SUCCESS' in str(result[-1])
 _,positions,gaps=Q.get_all_vertex_positions(d,False);assert not gaps
 box=source.get_bounding_box();cx=(box.min.x+box.max.x)/2;cy=(box.min.y+box.max.y)/2
 rx=(box.max.x-box.min.x)/2;ry=(box.max.y-box.min.y)/2
 count=0;maximum=0;protected=0
 for i,p in enumerate(positions.convert_vector_list_to_array()):
  x=(p.x-cx)/rx;y=(p.y-cy)/ry;r=math.hypot(x,y);angle=math.atan2(y,x)
  start=.48+.12*math.sin(angle*2+.7+index)+.06*math.cos(angle*3-1.1)
  f=max(0,min(1,(r-start)/.45));f=f*f*(3-2*f)
  depth=f*(85+25*math.sin(angle+index*1.4))
  # Roll90 maps local -Z to world +Y; never extend toward the main aisle.
  if depth<.001:protected+=1;continue
  assert positions.set_vector_list_item(i,u.Vector(p.x,p.y,p.z-depth))
  count+=1;maximum=max(maximum,depth)
 u.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(d,positions)
 normal=u.GeometryScriptSplitNormalsOptions();normal.opening_angle_deg=45;normal.split_by_opening_angle=True
 u.GeometryScript_Normals.compute_split_normals(d,normal,u.GeometryScriptCalculateNormalsOptions())
 opts=u.GeometryScriptCopyMeshToAssetOptions();opts.enable_recompute_normals=False
 result=AS.copy_mesh_to_static_mesh(d,mesh,opts,u.GeometryScriptMeshWriteLOD());assert 'SUCCESS' in str(result[-1])
 collision=source.get_editor_property('complex_collision_mesh') or source
 mesh.set_editor_property('complex_collision_mesh',collision)
 mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 assert E.save_loaded_asset(mesh,False)
 materials=list(c.get_materials());c.set_static_mesh(mesh)
 for slot,m in enumerate(materials):c.set_material(slot,m)
 changes.append(dict(name=name,label=a.get_actor_label(),old=source.get_path_name(),new=mesh.get_path_name()))
 audit.append(dict(mesh=mesh.get_path_name(),source=source.get_path_name(),collision=collision.get_path_name(),changed_vertices=count,protected_vertices=protected,max_depth_cm=maximum,xy_unchanged=True,aisle_extension=False,visual_collision_difference_requires_review=True))
(O/'changes.json').write_text(json.dumps(changes,indent=2));(O/'mesh-audit.json').write_text(json.dumps(audit,indent=2))
tag='art1';shots=[('backwall',(1700,400,300),(5,90)),('concept',(2900,900,700),(-20,-138))];S.update(i=0,sent=False,t=time.monotonic())
