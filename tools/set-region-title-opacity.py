"""Adjust only the saved region title background opacity, without rebuilding modules."""
import unreal as u
import json, shutil
from pathlib import Path
from datetime import datetime

root=Path(u.Paths.project_dir()).resolve()
out=root/'Saved/RegionTitle';out.mkdir(parents=True,exist_ok=True)
path='/Game/Constellation/UI/Widgets/WBP_RegionTitle'
asset=u.load_asset(path);assert asset
cls=u.load_class(None,path+'.WBP_RegionTitle_C');assert cls
cdo=u.get_default_object(cls)
before=float(cdo.get_editor_property('nebula_opacity'))
if '-VerifyRegionOpacity' not in u.SystemLibrary.get_command_line():
 source=root/'Content/Constellation/UI/Widgets/WBP_RegionTitle.uasset'
 shutil.copy2(source,out/('WBP_RegionTitle-opacity-before-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.uasset'))
 cdo.set_editor_property('nebula_opacity',0.65)
 u.BlueprintEditorLibrary.compile_blueprint(asset)
 cdo=u.get_default_object(u.load_class(None,path+'.WBP_RegionTitle_C'))
 assert abs(cdo.get_editor_property('nebula_opacity')-0.65)<0.0001
 assert u.EditorAssetLibrary.save_loaded_asset(asset,only_if_is_dirty=False)
else:
 assert abs(before-0.65)<0.0001,'Saved opacity did not persist'
result=dict(asset=path,previous=before,opacity=float(cdo.get_editor_property('nebula_opacity')),verified_reload='-VerifyRegionOpacity' in u.SystemLibrary.get_command_line())
(out/('opacity-verified.json' if result['verified_reload'] else 'opacity-change.json')).write_text(json.dumps(result,indent=2),encoding='utf8')
u.log('REGION_OPACITY_SUCCESS '+str(result))
u.SystemLibrary.quit_editor()
