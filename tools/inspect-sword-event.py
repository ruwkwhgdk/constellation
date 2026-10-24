"""Read-only saved-map inventory; no map or asset saves."""
import unreal as u, json, traceback
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/SwordAcquisition/Inspection_20261021'
O.mkdir(parents=True,exist_ok=True)
try:
    u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
    rows=[]
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        meshes=[c.static_mesh.get_path_name() for c in a.get_components_by_class(u.StaticMeshComponent) if c.static_mesh]
        if any(k in (a.get_name()+' '+a.get_actor_label()+' '+str(meshes)).lower() for k in ['sword','star','break_floor','검']):
            rows.append(dict(name=a.get_name(),label=a.get_actor_label(),path=a.get_path_name(),cls=a.get_class().get_path_name(),transform=str(a.get_actor_transform()),meshes=meshes))
    registry=u.AssetRegistryHelpers.get_asset_registry()
    assets=[]
    for a in registry.get_assets_by_path('/Game',recursive=True):
        if any(k in str(a.asset_name).lower() for k in ['sword','rust','getitem','itemget','itemacqui','itemobtain']):
            assets.append(str(a.package_name))
    (O/'inventory.json').write_text(json.dumps(dict(actors=rows,assets=assets,qte_available=hasattr(u,'DirectorQTESettings')),ensure_ascii=False,indent=2),encoding='utf8')
except:
    (O/'error.txt').write_text(traceback.format_exc(),encoding='utf8')
finally:
    u.SystemLibrary.quit_editor()
