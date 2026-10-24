"""Import closed underside variants and preview seven fascia replacements; no map save."""
import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/ClosedLedge_20261018'
E=u.EditorAssetLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem)
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/ClosedLedge'
world=u.EditorLevelLibrary.get_editor_world()
u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
s=opts.static_mesh_import_data;s.combine_meshes=True;s.auto_generate_collision=False;s.convert_scene_unit=True;s.transform_vertex_to_absolute=False;s.generate_lightmap_u_vs=True;s.import_uniform_scale=100.0
meshes=[]
for letter in 'ABC':
 name='SM_S0_ClosedLedge_'+letter;dest=D+'/'+name
 if True:
  task=u.AssetImportTask();task.filename=str(R/'ArtSource/SchoolOpening/WetFloor/ClosedLedge'/(name+'.fbx'));task.destination_path=D;task.destination_name=name;task.automated=True;task.save=True;task.replace_existing=True;task.replace_existing_settings=True;task.options=opts
  u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
 mesh=E.load_asset(dest);assert mesh
 box=mesh.get_bounding_box();size=box.max-box.min
 if abs(size.x-12)<.01:
  dynamic=u.DynamicMesh()
  result=u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(mesh,dynamic,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD())
  assert 'SUCCESS' in str(result[-1])
  _,positions,gaps=u.GeometryScript_MeshQueries.get_all_vertex_positions(dynamic,False);assert not gaps
  for vertex,p in enumerate(positions.convert_vector_list_to_array()):
   assert positions.set_vector_list_item(vertex,u.Vector(p.x*100,p.y*100,p.z*100))
  u.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(dynamic,positions)
  result=u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dynamic,mesh,u.GeometryScriptCopyMeshToAssetOptions(),u.GeometryScriptMeshWriteLOD())
  assert 'SUCCESS' in str(result[-1]);assert E.save_loaded_asset(mesh,False)
  box=mesh.get_bounding_box();size=box.max-box.min
 assert abs(size.x-1200)<1 and 75<size.y<90 and 100<size.z<140,(name,str(box))
 meshes.append(mesh)
labels=['S0_Edge_Upper_%02d'%i for i in range(4)]+['S0_Edge_Lower_%02d'%i for i in range(3)]
targets={a.get_actor_label():a for a in A.get_all_level_actors() if a.get_actor_label() in labels}
assert len(targets)==7
records=[]
for i,label in enumerate(labels):
 a=targets[label];assert not a.get_actor_enable_collision()
 c=a.static_mesh_component;center,extent=a.get_actor_bounds(False)
 old=dict(label=label,name=a.get_name(),mesh=c.static_mesh.get_path_name(),location=str(a.get_actor_location()),scale=str(a.get_actor_scale3d()),bounds=str((center,extent)))
 materials=list(c.get_materials());mesh=meshes[i%3];box=mesh.get_bounding_box();size=box.max-box.min
 top=center.z+extent.z;height=[115,105,120,110,165,175,160][i]
 upper=i<4
 c.set_static_mesh(mesh)
 a.set_actor_scale3d(u.Vector((extent.y if upper else extent.x)*2/size.x,(extent.x if upper else extent.y)*2/size.y,height/size.z))
 for j,m in enumerate(materials):c.set_material(j,m)
 nc,ne=a.get_actor_bounds(False);p=a.get_actor_location()
 a.set_actor_location(u.Vector(p.x+center.x-nc.x,p.y+center.y-nc.y,p.z+top-(nc.z+ne.z)),False,True)
 nc,ne=a.get_actor_bounds(False)
 assert abs(nc.z+ne.z-top)<.01 and abs(nc.x-center.x)<.01 and abs(nc.y-center.y)<.01
 assert abs(ne.x-extent.x)<.01 and abs(ne.y-extent.y)<.01
 old.update(new_mesh=mesh.get_path_name(),new_location=str(a.get_actor_location()),new_scale=str(a.get_actor_scale3d()),new_bounds=str((nc,ne)))
 records.append(old)
(O/'changes.json').write_text(json.dumps(records,indent=2))
tag='art1';S.update(i=0,sent=False,t=time.monotonic())

