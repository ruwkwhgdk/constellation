import hashlib,re,shutil
baseline=json.loads((O/'baseline-actors.json').read_text());changes={r['name']:r for r in json.loads((O/'changes.json').read_text())};actors={a.get_name():a for a in A.get_all_level_actors()}
def norm(s):return re.sub(r'0x[0-9A-Fa-f]+','PTR',s).replace('-0.000000','0.000000')
for row in baseline:
 a=actors[row['name']];expected_transform=changes[row['name']]['new_transform'] if row['name'] in changes else row['transform'];assert norm(str(a.get_actor_transform()))==norm(expected_transform)
 assert a.get_actor_enable_collision()==row['collision']
 cs={c.get_name():c for c in a.get_components_by_class(u.StaticMeshComponent)}
 for item in row['meshes']:
  c=cs[item['name']];expected=list(item['materials'])
  assert [m.get_path_name() if m else '' for m in c.get_materials()]==expected
  assert (c.static_mesh.get_path_name() if c.static_mesh else '')==item['mesh']
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==json.loads((O/'session.json').read_text())['map_sha256']
shutil.copy2(mapfile,O/'AbandonedSchool.before.umap')
assert u.EditorLoadingAndSavingUtils.save_map(u.EditorLevelLibrary.get_editor_world(),'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
(O/'saved.json').write_text(json.dumps(dict(infill_transform_actors=len(changes),sha256=hashlib.sha256(mapfile.read_bytes()).hexdigest()),indent=2))
u.SystemLibrary.quit_editor()


