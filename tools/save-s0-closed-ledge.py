"""Save reviewed seven-actor replacement only after full baseline comparison."""
import hashlib,re
baseline=json.loads((O/'baseline-actors.json').read_text())
allowed={r['name'] for r in json.loads((O/'changes.json').read_text())}
current={a.get_name():a for a in A.get_all_level_actors()}
def normal(s):
 return re.sub(r'0x[0-9A-Fa-f]+','PTR',s).replace('-0.000000','0.000000')
for row in baseline:
 a=current[row['name']]
 assert a.get_actor_label()==row['label']
 assert a.get_actor_enable_collision()==row['collision']
 cs={c.get_name():c for c in a.get_components_by_class(u.StaticMeshComponent)}
 if row['name'] not in allowed:
  assert normal(str(a.get_actor_transform()))==normal(row['transform']),row['label']
 for item in row['meshes']:
  c=cs[item['name']]
  assert [m.get_path_name() if m else '' for m in c.get_materials()]==item['materials'],row['label']
  if row['name'] not in allowed:assert (c.static_mesh.get_path_name() if c.static_mesh else '')==item['mesh'],row['label']
map_file=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
expected=json.loads((O/'before-hash.json').read_text(encoding='utf-8-sig'))['Hash']
assert hashlib.sha256(map_file.read_bytes()).hexdigest().upper()==expected,'Map changed on disk; reload latest rather than overwrite.'
assert u.EditorLoadingAndSavingUtils.save_map(u.EditorLevelLibrary.get_editor_world(),'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
(O/'saved.json').write_text(json.dumps(dict(changed_actor_count=len(allowed),unchanged_actor_count=len(baseline)-len(allowed),sha256=hashlib.sha256(map_file.read_bytes()).hexdigest()),indent=2))
u.SystemLibrary.quit_editor()
