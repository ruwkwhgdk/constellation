import hashlib,re
E=u.EditorAssetLibrary
baseline=json.loads((O/'baseline-actors.json').read_text())
changes=json.loads((O/'changes.json').read_text());allowed={r['name']:r for r in changes}
actors={a.get_name():a for a in A.get_all_level_actors()}
def norm(s):return re.sub(r'0x[0-9A-Fa-f]+','PTR',s).replace('-0.000000','0.000000')
for row in baseline:
 a=actors[row['name']]
 assert norm(str(a.get_actor_transform()))==norm(row['transform']),row['label']
 assert a.get_actor_enable_collision()==row['collision']
 cs={c.get_name():c for c in a.get_components_by_class(u.StaticMeshComponent)}
 for item in row['meshes']:
  c=cs[item['name']]
  expected=allowed[row['name']]['new'] if row['name'] in allowed else item['mesh']
  assert (c.static_mesh.get_path_name() if c.static_mesh else '')==expected,row['label']
  assert [m.get_path_name() if m else '' for m in c.get_materials()]==item['materials']
audit=[]
for variant in json.loads((O/'variants.json').read_text()):
 old=E.load_asset(variant['source']);new=E.load_asset(variant['mesh'])
 assert old.get_editor_property('complex_collision_mesh')==new.get_editor_property('complex_collision_mesh')
 assert new.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
 arrays=[]
 for mesh in [old,new]:
  d=u.DynamicMesh();u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(mesh,d,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD())
  _,p,gaps=u.GeometryScript_MeshQueries.get_all_vertex_positions(d,False);assert not gaps
  arrays.append(p.convert_vector_list_to_array())
 assert len(arrays[0])==len(arrays[1])
 top=old.get_bounding_box().max.z-60;protected=0
 for a,b in zip(*arrays):
  assert abs(a.z-b.z)<.001
  if a.z>=top:
   assert (a-b).length()<.001
   protected+=1
 audit.append(dict(mesh=new.get_path_name(),vertices=len(arrays[0]),protected_top_vertices=protected,collision_unchanged=True))
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
assert hashlib.sha256(mapfile.read_bytes()).hexdigest()=='729a6ed8174381a2479e68052ce9c69bfc29bd8642d3ffb85227f7710351a587'
(O/'mesh-audit.json').write_text(json.dumps(audit,indent=2))
assert u.EditorLoadingAndSavingUtils.save_map(u.EditorLevelLibrary.get_editor_world(),'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
(O/'saved.json').write_text(json.dumps(dict(changed_mesh_actors=len(allowed),unchanged_actors=len(baseline)-len(allowed),sha256=hashlib.sha256(mapfile.read_bytes()).hexdigest()),indent=2))
u.SystemLibrary.quit_editor()
