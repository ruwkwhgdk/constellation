"""Import the supplied key circle without changing interaction rules or carry data."""
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
task=u.AssetImportTask()
task.filename=str(root/'ArtSource/UI/InteractionPrompt/T_InteractionPrompt_KeyBackground.png')
task.destination_path='/Game/Constellation/UI/Art'
task.destination_name='T_InteractionPrompt_KeyBackground'
task.automated=True
task.replace_existing=True
task.save=False
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
texture=u.load_asset(task.destination_path+'/'+task.destination_name)
assert texture
texture.set_editor_property('lod_group',u.TextureGroup.TEXTUREGROUP_UI)
texture.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_EDITOR_ICON)
texture.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS)
texture.set_editor_property('srgb',True)
assert u.EditorAssetLibrary.save_loaded_asset(texture,False)
hero=u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine')
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn=u.SubobjectDataBlueprintFunctionLibrary
prompts=[]
for handle in sub.k2_gather_subobject_data_for_blueprint(hero):
    obj=fn.get_object_for_blueprint(fn.get_data(handle),hero)
    if isinstance(obj,u.InteractionPromptComponent): prompts.append(obj)
assert len(prompts)==1
prompts[0].set_editor_property('key_background_texture',texture)
u.BlueprintEditorLibrary.compile_blueprint(hero)
assert u.EditorAssetLibrary.save_loaded_asset(hero,False)
assert prompts[0].get_editor_property('key_background_texture')==texture
u.log('INTERACTION_KEY_CIRCLE_SAVED '+texture.get_path_name())
