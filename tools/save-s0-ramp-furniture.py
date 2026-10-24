import unreal as u,json,hashlib,shutil
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/RampFurniture_20261018';O.mkdir(exist_ok=True)
f=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
expected=json.loads((R/'Saved/S0WetFloor/ClosedLedge_20261018/saved.json').read_text())['sha256']
assert hashlib.sha256(f.read_bytes()).hexdigest()==expected,'Reload latest map and reconcile changes before saving.'
shutil.copy2(f,O/'AbandonedSchool.before.umap')
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
exec((R/'tools/clear-s0-ramp-furniture.py').read_text(),globals())
assert u.EditorLoadingAndSavingUtils.save_map(u.EditorLevelLibrary.get_editor_world(),'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
actors={a.get_name():a for a in A.get_all_level_actors()}
for name,xyz in placements.items():
 p=actors[name].get_actor_location();assert all(abs(a-b)<.01 for a,b in zip([p.x,p.y,p.z],xyz))
(O/'saved.json').write_text(json.dumps({'actors':list(placements),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'reload_positions_verified':True},indent=2))
