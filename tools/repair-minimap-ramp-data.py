"""Regenerate only minimap data; preserve the level and designer overrides."""
import unreal as u,json,shutil,hashlib
from pathlib import Path
from datetime import datetime
root=Path(u.Paths.project_dir());out=root/'Saved/Minimap'
asset='/Game/Constellation/UI/Minimap/DA_AbandonedSchool'
mapfile=root/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
before=hashlib.sha256(mapfile.read_bytes()).hexdigest()
data=u.load_asset(asset)
backup=out/('ramp-data-before-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.uasset')
shutil.copy2(root/'Content/Constellation/UI/Minimap/DA_AbandonedSchool.uasset',backup)
w=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
preserved={k:str(data.get_editor_property(k)) for k in ('marker_overrides','manual_markers')}
report=u.MinimapEditorLibrary.build_school_map(w,data)
assert report.startswith('OK '),report
assert preserved=={k:str(data.get_editor_property(k)) for k in preserved}
assert u.EditorAssetLibrary.save_loaded_asset(data,only_if_is_dirty=False)
assert before==hashlib.sha256(mapfile.read_bytes()).hexdigest(),'Level changed'
(out/'ramp-generation.json').write_text(json.dumps(dict(report=report,backup=str(backup),level_unchanged=True),indent=2))
u.log('RAMP_DATA_REPAIRED '+report)
if '-SlopeReview' in u.SystemLibrary.get_command_line():
 exec(compile((root/'tools/verify-minimap-slope.py').read_text(encoding='utf8'),str(root/'tools/verify-minimap-slope.py'),'exec'))
else:
 u.SystemLibrary.quit_editor()
