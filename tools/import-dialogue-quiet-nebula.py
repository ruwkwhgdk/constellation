import unreal as u
from pathlib import Path
import json
root=Path(u.Paths.project_dir());folder='/Game/Constellation/UI/Dialogue'
t=u.AssetImportTask();t.filename=str(root/'ArtSource/UI/Dialogue/QuietNebulaStar/T_Dialogue_QuietNebulaAtlas.png');t.destination_path=folder;t.destination_name='T_Dialogue_QuietNebulaAtlas';t.automated=True;t.replace_existing=True;t.save=False
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);asset=u.load_asset(folder+'/'+t.destination_name);assert asset
for key,value in [('lod_group',u.TextureGroup.TEXTUREGROUP_UI),('compression_settings',u.TextureCompressionSettings.TC_EDITOR_ICON),('mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS),('srgb',True),('never_stream',True)]:asset.set_editor_property(key,value)
assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
refs=u.EditorAssetLibrary.find_package_referencers_for_asset('/Game/Constellation/UI/Widgets/WBP_Dialogue',False)
(root/'Saved/DialogueRestyle/legacy-referencers.json').write_text(json.dumps(list(refs),indent=2),encoding='utf8')
u.log('QUIET_NEBULA_IMPORTED')
