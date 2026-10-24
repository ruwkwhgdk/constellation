import unreal as u
from pathlib import Path
r=Path(u.Paths.project_dir());folder='/Game/Constellation/UI/RegionTitle'
for file,name in [('Resources/T_RegionNebula.png','T_RegionNebula')]:
 t=u.AssetImportTask();t.filename=str(r/'ArtSource/UI/RegionTitle'/file);t.destination_path=folder;t.destination_name=name;t.automated=True;t.replace_existing=True;t.save=True
 u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);u.log('REGION_IMPORTED '+str(t.imported_object_paths))
 a=u.load_asset(folder+'/'+name)
 if isinstance(a,u.Texture2D):
  for k,v in [('lod_group',u.TextureGroup.TEXTUREGROUP_UI),('compression_settings',u.TextureCompressionSettings.TC_EDITOR_ICON),('mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS),('srgb',True),('never_stream',True)]:a.set_editor_property(k,v)
  u.EditorAssetLibrary.save_loaded_asset(a,False)
