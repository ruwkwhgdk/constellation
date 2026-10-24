import math
E=u.EditorAssetLibrary;AS=u.GeometryScript_AssetUtils;Q=u.GeometryScript_MeshQueries
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
original={r['name']:r for r in json.loads((O/'changes.json').read_text())};actors={a.get_name():a for a in A.get_all_level_actors()};changes=[];audit=[]
for number,actorname in enumerate(['StaticMeshActor_831','StaticMeshActor_833']):
 a=actors[actorname];c=a.static_mesh_component;source=E.load_asset(original[actorname]['old'])
 path=D+'/SM_S0_BackRock_V17_'+str(number)
 mesh=E.load_asset(path);assert mesh
 d=u.DynamicMesh();result=AS.copy_mesh_from_static_mesh(source,d,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD());assert 'SUCCESS' in str(result[-1])
 _,positions,gaps=Q.get_all_vertex_positions(d,False);assert not gaps
 box=source.get_bounding_box();cx=(box.min.x+box.max.x)/2;cy=(box.min.y+box.max.y)/2;rx=(box.max.x-box.min.x)/2;ry=(box.max.y-box.min.y)/2
 changed=0;maximum=0
 for i,p in enumerate(positions.convert_vector_list_to_array()):
  x=(p.x-cx)/rx;y=(p.y-cy)/ry;r=math.hypot(x,y)
  if r<.45:continue
  angle=math.atan2(y,x);fold=(angle-.19-number*.23+math.pi/5)%(math.tau/5)-math.pi/5
  target=.94+.055*math.sin(angle*3+number)+.035*math.cos(angle*5+.8);blend=min(1,(r-.45)/.4)
  delta=(target-r)*blend
  dx=x/r*rx*delta;dy=y/r*ry*delta;length=math.hypot(dx,dy)
  if length>45:dx*=45/length;dy*=45/length
  # Local Z becomes wall-normal world Y: retain it, so no projection into the central aisle.
  if math.hypot(dx,dy)>.001:changed+=1
  maximum=max(maximum,math.hypot(dx,dy))
  assert positions.set_vector_list_item(i,u.Vector(p.x+dx,p.y+dy,p.z))
 u.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(d,positions)
 normal=u.GeometryScriptSplitNormalsOptions();normal.opening_angle_deg=45;normal.split_by_opening_angle=True
 u.GeometryScript_Normals.compute_split_normals(d,normal,u.GeometryScriptCalculateNormalsOptions())
 options=u.GeometryScriptCopyMeshToAssetOptions();options.enable_recompute_normals=False
 result=AS.copy_mesh_to_static_mesh(d,mesh,options,u.GeometryScriptMeshWriteLOD());assert 'SUCCESS' in str(result[-1])
 mesh.set_editor_property('complex_collision_mesh',None)
 mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 assert E.save_loaded_asset(mesh,False)
 materials=list(c.get_materials());c.set_static_mesh(mesh)
 for slot,m in enumerate(materials):c.set_material(slot,m)
 changes.append(dict(name=actorname,label=a.get_actor_label(),old=source.get_path_name(),new=mesh.get_path_name()))
 audit.append(dict(mesh=mesh.get_path_name(),vertices=len(positions.convert_vector_list_to_array()),changed_vertices=changed,max_displacement_cm=maximum,wall_normal_depth_unchanged=True,collision_uses_render_mesh=True))
(O/'changes.json').write_text(json.dumps(changes,indent=2));(O/'mesh-audit.json').write_text(json.dumps(audit,indent=2))
tag='art2';shots=[('reverse',(3050,-2650,1650),(-25,130)),('backwall',(1700,400,300),(5,90)),('concept',(2900,900,700),(-20,-138))];S.update(i=0,sent=False,t=time.monotonic())
