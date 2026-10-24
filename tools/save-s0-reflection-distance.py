"""Save one reviewed planar-reflection property, with baseline/hash guards."""
import hashlib,re,shutil
assert pc.get_editor_property('max_view_distance_override')==8000.0
actors={a.get_name():a for a in A.get_all_level_actors()}
def norm(v):return re.sub(r'0x[0-9A-Fa-f]+','PTR',str(v)).replace('-0.000000','0.000000')
baseline=json.loads((O/'baseline-actors.json').read_text())
for row in baseline:
 a=actors[row['name']];assert norm(a.get_actor_transform())==norm(row['transform']),row['name']
 assert a.get_actor_enable_collision()==row['collision']
 meshes=[dict(name=c.get_name(),mesh=c.static_mesh.get_path_name() if c.static_mesh else '',materials=[m.get_path_name() if m else '' for m in c.get_materials()]) for c in a.get_components_by_class(u.StaticMeshComponent)]
 assert meshes==row['meshes'],row['name']
assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==json.loads((O/'session.json').read_text())['map_sha256']
shutil.copy2(mapfile,O/'AbandonedSchool.before.umap')
A.destroy_actor(cam)
assert u.EditorLoadingAndSavingUtils.save_map(u.EditorLevelLibrary.get_editor_world(),'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
(O/'saved.json').write_text(json.dumps(dict(property='max_view_distance_override',old=-1,new=8000,baseline_actors_preserved=len(baseline),sha256=hashlib.sha256(mapfile.read_bytes()).hexdigest()),indent=2))
u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
