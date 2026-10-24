"""Reduce only the front lobe of the upper rear rock; preserve original collision."""
import unreal as u,json,math
E=u.EditorAssetLibrary;Q=u.GeometryScript_MeshQueries;AS=u.GeometryScript_AssetUtils
a=next(a for a in A.get_all_level_actors() if a.get_name()=='StaticMeshActor_795')
assert a.get_actor_label()=='SM_LCave_P_Mesa_22'
c=a.static_mesh_component;source=c.static_mesh;original_materials=list(c.get_materials())
assert source.get_path_name()=='/Game/LuosCaves/Meshes/Props_Mesas/SM_LCave_P_Mesa_10.SM_LCave_P_Mesa_10'
dest='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/SM_S0_RearBulge_V38'
assert not E.does_asset_exist(dest)
d=u.DynamicMesh();result=AS.copy_mesh_from_static_mesh(source,d,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD());assert 'SUCCESS' in str(result[-1])
closed_before=Q.get_is_closed_mesh(d)
_,positions,gaps=Q.get_all_vertex_positions(d,False);assert not gaps
points=positions.convert_vector_list_to_array();transform=c.get_world_transform();changes=[]
for index,p in enumerate(points):
 world=u.MathLibrary.transform_location(transform,p);old=[world.x,world.y,world.z];
 depth=max(0.,2050.-world.y)
 t=min(1.,depth/120.);weight=t*t*(3.-2.*t)
 world.y+=.65*depth*weight
 updated=u.MathLibrary.inverse_transform_location(transform,world)
 assert positions.set_vector_list_item(index,updated)
 changes.append({'vertex':index,'before_world':old,'after_world':[world.x,world.y,world.z]})
assert changes
u.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(d,positions)
u.GeometryScript_Normals.recompute_normals(d,u.GeometryScriptCalculateNormalsOptions())
assert Q.get_is_closed_mesh(d)==closed_before
mesh=E.duplicate_asset(source.get_path_name(),dest);assert mesh
original_flag=source.get_editor_property('body_setup').get_editor_property('collision_trace_flag')
result=AS.copy_mesh_to_static_mesh(d,mesh,u.GeometryScriptCopyMeshToAssetOptions(),u.GeometryScriptMeshWriteLOD());assert 'SUCCESS' in str(result[-1])
# Keep original simple body setup; use original visual mesh for complex collision as well.
mesh.set_editor_property('complex_collision_mesh',source)
assert mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==original_flag
assert E.save_loaded_asset(mesh,False)
material=u.load_asset('/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/M_S0_IrregularRock_V24');assert material
targets=[(a,source,mesh,original_materials)]
(O/'mesh-audit.json').write_text(json.dumps({'actor':a.get_name(),'source':source.get_path_name(),'candidate':dest,'changed_vertices':changes,'source_closed':closed_before,'candidate_closed':Q.get_is_closed_mesh(d),'collision_trace_flag':str(original_flag),'complex_collision_mesh':source.get_path_name(),'actor_transform':str(a.get_actor_transform()),'original_materials':[m.get_path_name() if m else '' for m in original_materials]},indent=2))
