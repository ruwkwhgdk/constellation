"""Run only after image review; scope and concurrent-map guards before save."""
import hashlib,re,shutil
baseline=json.loads((O/'baseline-actors.json').read_text());changes=json.loads((O/'changes.json').read_text())
allowed={r['name']:r for r in changes};actors={a.get_name():a for a in A.get_all_level_actors()}
assert set(allowed)=={'StaticMeshActor_831','StaticMeshActor_833'}
def norm(s):return re.sub(r'0x[0-9A-Fa-f]+','PTR',s).replace('-0.000000','0.000000')
for row in baseline:
 a=actors[row['name']]
 assert a.get_actor_label()==row['label'] and a.get_actor_enable_collision()==row['collision']
 if row['name'] not in allowed:assert norm(str(a.get_actor_transform()))==norm(row['transform']),row['label']
 cs={c.get_name():c for c in a.get_components_by_class(u.StaticMeshComponent)}
 for item in row['meshes']:
  c=cs[item['name']]
  expected_materials=list(item['materials'])
  if row['name'] in allowed and (O/'normal-preview.json').exists():
   expected_materials[0]=json.loads((O/'normal-preview.json').read_text())['material']
  assert [m.get_path_name() if m else '' for m in c.get_materials()]==expected_materials
  expected=allowed[row['name']]['new_mesh'] if row['name'] in allowed else item['mesh']
  assert (c.static_mesh.get_path_name() if c.static_mesh else '')==expected
 for name in allowed:
  p=actors[name].get_actor_location();assert p.y>1800 # Both ramps are negative Y.
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
session=json.loads((O/'session.json').read_text())
assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==session['map_sha256'],'Map changed since this review started; reload and revalidate'
assert not (O/'AbandonedSchool.before.umap').exists(),'Do not overwrite a previous review backup'
shutil.copy2(mapfile,O/'AbandonedSchool.before.umap')
assert u.EditorLoadingAndSavingUtils.save_map(u.EditorLevelLibrary.get_editor_world(),'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
(O/'saved.json').write_text(json.dumps(dict(mesh_actors=2,sha256=hashlib.sha256(mapfile.read_bytes()).hexdigest()),indent=2))
u.SystemLibrary.quit_editor()
