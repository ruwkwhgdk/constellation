"""Plane-fractured derivatives of source rocks; no original asset edits."""
import unreal as u,math,json
E=u.EditorAssetLibrary;AS=u.GeometryScript_AssetUtils;Q=u.GeometryScript_MeshQueries
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
actors={a.get_name():a for a in A.get_all_level_actors()};targets=[];audit=[]
for idx,name in enumerate(['StaticMeshActor_831','StaticMeshActor_833']):
 a=actors[name];source=a.static_mesh_component.static_mesh
 assert source.get_name() in ['SM_LCave_P_Mesa_12','SM_LCave_P_Mesa_11']
 dest=D+'/SM_S0_FracturedSource_V25_'+str(idx);assert not E.does_asset_exist(dest)
 mesh=E.duplicate_asset(source.get_path_name(),dest);assert mesh
 d=u.DynamicMesh();result=AS.copy_mesh_from_static_mesh(source,d,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD());assert 'SUCCESS' in str(result[-1])
 b=source.get_bounding_box();cx=(b.min.x+b.max.x)/2;cy=(b.min.y+b.max.y)/2;rx=(b.max.x-b.min.x)/2;ry=(b.max.y-b.min.y)/2
 original_closed=Q.get_is_closed_mesh(d)
 # Irregularly spaced fracture directions, never a radial rescaling.
 cuts=([(1,-.23,.81),(-1,.35,.83),(.54,1,.79),(-.62,1,.76)] if idx==0 else [(1,.17,.84),(-1,-.31,.85),(.75,1,.78),(-.39,1,.81)])
 for nx,ny,offset in cuts:
  n=u.Vector(nx/rx,ny/ry,0);length=math.sqrt(n.x*n.x+n.y*n.y);n=n/length
  distance=offset/length
  origin=u.Vector(cx+n.x*distance,cy+n.y*distance,0)
  rot=u.MathLibrary.make_rot_from_z(n)
  opts=u.GeometryScriptMeshPlaneCutOptions();opts.fill_holes=True;opts.fill_spans=True;opts.hole_fill_material_id=0
  u.GeometryScript_MeshBooleans.apply_mesh_plane_cut(d,u.Transform(location=origin,rotation=rot,scale=u.Vector(1,1,1)),opts)
 assert Q.get_is_closed_mesh(d),'Cut mesh has open edges'
 _,positions,gaps=Q.get_all_vertex_positions(d,True)
 pp=positions.convert_vector_list_to_array();assert len(pp)>100
 assert all(math.isfinite(v) for p in pp for v in [p.x,p.y,p.z])
 assert all(b.min.x-.1<=p.x<=b.max.x+.1 and b.min.y-.1<=p.y<=b.max.y+.1 and b.min.z-.1<=p.z<=b.max.z+.1 for p in pp),'Cut expanded source bounds'
 mins=[min(getattr(p,k) for p in pp) for k in ['x','y','z']];maxs=[max(getattr(p,k) for p in pp) for k in ['x','y','z']]
 assert maxs[0]-mins[0]>rx and maxs[1]-mins[1]>ry,'Cut removed too much'
 normals=u.GeometryScriptSplitNormalsOptions();normals.opening_angle_deg=48;normals.split_by_opening_angle=True
 u.GeometryScript_Normals.compute_split_normals(d,normals,u.GeometryScriptCalculateNormalsOptions())
 opts=u.GeometryScriptCopyMeshToAssetOptions();opts.enable_recompute_normals=False
 result=AS.copy_mesh_to_static_mesh(d,mesh,opts,u.GeometryScriptMeshWriteLOD());assert 'SUCCESS' in str(result[-1])
 mesh.set_editor_property('complex_collision_mesh',None)
 mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 assert E.save_loaded_asset(mesh,False)
 targets.append((a,source,mesh))
 audit.append({'actor':name,'source':source.get_path_name(),'candidate':mesh.get_path_name(),'source_closed':original_closed,'candidate_closed':True,'vertices':len(pp),'bounds_min':mins,'bounds_max':maxs,'no_source_bounds_expansion':True,'collision':'candidate complex-as-simple; intentionally matches cut surface','cuts':cuts})
(O/'mesh-audit.json').write_text(json.dumps(audit,indent=2))
