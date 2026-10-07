"""Import the supplied Figma PNG and install the editable interaction prompt rules."""
import json, shutil
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
out=root/'Saved/InteractionPromptReview'
(out/'backups').mkdir(parents=True,exist_ok=True)
lib=u.EditorAssetLibrary
hero_path='/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine'
source=root/'Content/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine.uasset'
backup=out/'backups/BP_Player_Heroine.before-prompt.uasset'
if not backup.exists(): shutil.copy2(source,backup)

task=u.AssetImportTask()
task.filename=str(root/'ArtSource/UI/InteractionPrompt/T_InteractionPrompt_Background.png')
task.destination_path='/Game/Constellation/UI/Art'
task.destination_name='T_InteractionPrompt_Background'
task.automated=True; task.replace_existing=True; task.save=False
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
texture=u.load_asset(task.destination_path+'/'+task.destination_name)
assert texture
texture.set_editor_property('lod_group',u.TextureGroup.TEXTUREGROUP_UI)
texture.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_EDITOR_ICON)
texture.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS)
texture.set_editor_property('srgb',True)
assert lib.save_loaded_asset(texture,False)

I='/Game/Constellation/Gameplay/Interaction/'
S='/Game/Constellation/Environments/School/Blueprints/'
A=u.InteractionAction
rows=[
 (S+'BP_School_Door',A.OPEN,dict(toggle_property='IsOpen',alternate_action=A.CLOSE)),
 (S+'BP_School_Locker_Open',A.OPEN,dict(completed_property='IsOpened',required_overlap_component='EnableBoxCollision')),
 (S+'BP_School_Gate',A.OPEN,{}),
 (S+'BP_Grand_Piano',A.PLAY,{}),
 (S+'BP_School_Girl_Statue',A.RESTORE,{}),
 (I+'Actors/BP_Chest',A.OPEN,dict(completed_property='IsOpened')),
 (I+'Actors/BP_Book',A.READ,dict(respect_interact_once=True)),
 (I+'Actors/BP_Ladder',A.CLIMB,dict(alternate_component_tag='LadderTop',alternate_action=A.DESCEND)),
 (I+'Actors/BP_Kiosk_Reset',A.RESET,{}),
 (I+'Actors/BP_Switch',A.ACTIVATE,dict(toggle_property='bIsOn',alternate_action=A.DEACTIVATE,enabled_property='bIsActive')),
 (I+'Actors/BP_Sword_Pickup',A.COLLECT,dict(respect_interact_once=True)),
 (I+'Actors/BP_Star_Object_Sequence',A.INSPECT,dict(respect_interact_once=True)),
 (I+'Actors/BP_Star_Object',A.COLLECT,dict(respect_interact_once=True)),
 (I+'BP_Interactable_CheckPosition',A.INTERACT,dict(respect_interact_once=True,required_overlap_component='EnableBoxCollision')),
 (I+'BP_Interactable_Base',A.INTERACT,dict(respect_interact_once=True)),
]
rules=[]
for path,action,props in rows:
    rule=u.InteractionPromptRule()
    cls=lib.load_blueprint_class(path); assert cls,path
    rule.actor_class=cls; rule.action=action
    for k,v in props.items(): rule.set_editor_property(k,v)
    rules.append(rule)
hero=u.load_asset(hero_path)
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn=u.SubobjectDataBlueprintFunctionLibrary
handles=sub.k2_gather_subobject_data_for_blueprint(hero)
prompt=None
for handle in handles:
    obj=fn.get_object_for_blueprint(fn.get_data(handle),hero)
    if isinstance(obj,u.InteractionPromptComponent): prompt=obj; break
if prompt is None:
    params=u.AddNewSubobjectParams(parent_handle=handles[0],new_class=u.InteractionPromptComponent,blueprint_context=hero)
    handle,reason=sub.add_new_subobject(params)
    assert fn.is_handle_valid(handle),str(reason)
    sub.rename_subobject(handle,'InteractionPrompt')
    prompt=fn.get_object_for_blueprint(fn.get_data(handle),hero)
assert prompt
prompt.set_editor_property('rules',rules)
prompt.set_editor_property('background_texture',texture)
prompt.set_editor_property('interact_input_action',u.load_asset('/Game/Constellation/Input/IA_Interact'))
u.BlueprintEditorLibrary.compile_blueprint(hero)
assert lib.save_loaded_asset(hero,False)
(out/'installed.json').write_text(json.dumps({'texture':texture.get_path_name(),'hero':hero_path,'rules':[{'class':p,'action':str(a),'conditions':{k:str(v) for k,v in props.items()}} for p,a,props in rows]},ensure_ascii=False,indent=2),encoding='utf-8')
u.log('INTERACTION_PROMPT_INSTALLED rules='+str(len(rules)))
