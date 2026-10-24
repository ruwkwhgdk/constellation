import hashlib,re,shutil
baseline=json.loads((O/'baseline-actors.json').read_text());changes=json.loads((O/'changes.json').read_text());lcdata=json.loads((O/'light-change.json').read_text())
allowed={r['name']:r for r in changes};actors={a.get_name():a for a in A.get_all_level_actors()}
def norm(s):return re.sub(r'0x[0-9A-Fa-f]+','PTR',s).replace('-0.000000','0.000000')
for row in baseline:
 a=actors[row['name']]
 assert a.get_actor_label()==row['label'] and a.get_actor_enable_collision()==row['collision']
 if row['name']!=lcdata['name']:assert norm(str(a.get_actor_transform()))==norm(row['transform']),row['label']
 cs={c.get_name():c for c in a.get_components_by_class(u.StaticMeshComponent)}
 for item in row['meshes']:
  c=cs[item['name']];expected=list(item['materials'])
  if row['name'] in allowed:expected[0]=allowed[row['name']]['new']
  assert [m.get_path_name() if m else '' for m in c.get_materials()]==expected
  assert (c.static_mesh.get_path_name() if c.static_mesh else '')==item['mesh']
light=actors[lcdata['name']];lc=light.get_component_by_class(u.LightComponent)
assert not lc.cast_shadows and lc.intensity==40
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
assert hashlib.sha256(mapfile.read_bytes()).hexdigest()=='33fddf6aedd7a81656ad5969dbe3f1bb2497d59852c1dbe355d72bed6ab2c22a'
shutil.copy2(mapfile,O/'AbandonedSchool.before.umap')
assert u.EditorLoadingAndSavingUtils.save_map(u.EditorLevelLibrary.get_editor_world(),'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
(O/'saved.json').write_text(json.dumps(dict(material_actors=2,light_actors=1,sha256=hashlib.sha256(mapfile.read_bytes()).hexdigest()),indent=2))
u.SystemLibrary.quit_editor()
