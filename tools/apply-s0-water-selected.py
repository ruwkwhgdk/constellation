"""Apply reviewed V7 material slots to the unchanged maintained map and reload."""
import unreal as u,json,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/WaterPass_20261017'
source=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256((O/'AbandonedSchool.before.umap').read_bytes()).digest(),'Source changed externally'
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
actors={a.get_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
changes=json.loads((O/'allowed-material-changes.json').read_text())
assert len(changes)==9
for name,label,component,slot,old,new in changes:
    a=actors[name]
    c=next(c for c in a.get_components_by_class(u.StaticMeshComponent) if c.get_name()==component)
    assert c.get_material(slot).get_path_name()==old
    material=u.EditorAssetLibrary.load_asset(new)
    assert material
    c.set_material(slot,material)
exec((R/'tools/save-s0-water.py').read_text(),globals())
exec((R/'tools/review-s0-water.py').read_text(),globals())
