import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir());D='/Game/SceneDirector/School/S0';E=u.EditorAssetLibrary
task=u.AssetImportTask();task.filename=str(R/'ArtSource/SchoolOpening/Photo_Memory_Draft.png');task.destination_path=D;task.destination_name='Photo_Memory_Draft';task.automated=True;task.replace_existing=True;task.replace_existing_settings=False;task.save=True
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths
tex=E.load_asset(D+'/Photo_Memory_Draft');assert tex
mat=E.load_asset(D+'/M_MemoryPhoto_Draft');assert mat
samples=[x for x in u.ObjectIterator(u.MaterialExpressionTextureSample) if x.get_outer()==mat]
assert any(x.get_editor_property('texture')==tex for x in samples),'Photo material lost texture reference'
assert E.save_loaded_asset(tex,False)
(R/'Saved/LockerPhotoUpdate/import.json').write_text(json.dumps(dict(texture=tex.get_path_name(),material=mat.get_path_name(),source=str(R/'ArtSource/SchoolOpening/Photo_Memory_Draft.png'),linked=True),indent=2))
u.log('LOCKER_PHOTO_UPDATED')
