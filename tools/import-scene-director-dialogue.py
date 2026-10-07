from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
for name in ['T_Dialogue_Background','T_Dialogue_Continue','T_Dialogue_SpeakerBackground','T_Dialogue_ChoiceFocusedBG','T_Dialogue_ChoiceFocusedStroke','T_Dialogue_ChoiceIdleBG','T_Dialogue_ChoiceIdleStroke','T_Dialogue_ChoiceCursor']:
    task=u.AssetImportTask()
    task.filename=str(root/'ArtSource/UI/Dialogue'/f'{name}.png')
    task.destination_path='/Game/Constellation/UI/Dialogue'
    task.destination_name=name
    task.automated=True
    task.replace_existing=True
    task.save=False
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture=u.load_asset(task.destination_path+'/'+name)
    assert texture
    texture.set_editor_property('lod_group',u.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property('srgb',True)
    assert u.EditorAssetLibrary.save_loaded_asset(texture,False)
    u.log('DIALOGUE_TEXTURE_IMPORTED '+texture.get_path_name())
