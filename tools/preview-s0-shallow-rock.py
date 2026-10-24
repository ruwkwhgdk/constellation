import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/ShallowRock_20261019'
E=u.EditorAssetLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem)
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/ShallowRock'
u.SystemLibrary.execute_console_command(u.EditorLevelLibrary.get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
s=opts.static_mesh_import_data;s.combine_meshes=True;s.auto_generate_collision=False;s.convert_scene_unit=True;s.transform_vertex_to_absolute=False;s.generate_lightmap_u_vs=True;s.import_uniform_scale=100.
records=[]
for index,(actorname,x) in enumerate([('StaticMeshActor_831',2674.35),('StaticMeshActor_833',1264.88)]):
 name='SM_S0_ShallowRock_'+str(index)
 task=u.AssetImportTask();task.filename=str(R/'ArtSource/SchoolOpening/WetFloor/ShallowRock'/(name+'.fbx'));task.destination_path=D;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=False;task.options=opts
 u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);mesh=E.load_asset(D+'/'+name);assert mesh
 box=mesh.get_bounding_box();size=box.max-box.min
 if size.x<20:
  dynamic=u.DynamicMesh();result=u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(mesh,dynamic,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD());assert 'SUCCESS' in str(result[-1])
  _,positions,gaps=u.GeometryScript_MeshQueries.get_all_vertex_positions(dynamic,False);assert not gaps
  for vertex,p in enumerate(positions.convert_vector_list_to_array()):assert positions.set_vector_list_item(vertex,u.Vector(p.x*100,p.y*100,p.z*100))
  u.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(dynamic,positions)
  result=u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dynamic,mesh,u.GeometryScriptCopyMeshToAssetOptions(),u.GeometryScriptMeshWriteLOD());assert 'SUCCESS' in str(result[-1])
 box=mesh.get_bounding_box();size=box.max-box.min;assert 1300<size.x<1600 and 100<size.y<150,(name,str(size))
 mesh.set_editor_property('complex_collision_mesh',None);mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);assert E.save_loaded_asset(mesh,False)
 a=next(a for a in A.get_all_level_actors() if a.get_name()==actorname);c=a.static_mesh_component
 row=dict(name=actorname,old_mesh=c.static_mesh.get_path_name(),old_transform=str(a.get_actor_transform()))
 material=c.get_material(0);c.set_static_mesh(mesh);c.set_material(0,material)
 a.set_actor_rotation(u.Rotator(yaw=180),False);a.set_actor_scale3d(u.Vector([1478.25,1330.6875][index]/size.x,1,1));a.set_actor_location(u.Vector(x,2000,-10),False,True)
 row.update(new_mesh=mesh.get_path_name(),new_transform=str(a.get_actor_transform()),bounds=str(a.get_actor_bounds(False)));records.append(row)
(O/'changes.json').write_text(json.dumps(records,indent=2))
tag='art1';shots=[('backwall',(1700,400,300),(5,90)),('reverse',(3050,-2650,1650),(-25,130)),('concept',(2900,900,700),(-20,-138))];S.update(i=0,sent=False,t=time.monotonic())



