"""Create carry assets and connect only reviewed character Blueprints; run in Unreal Python."""
import json, hashlib, shutil
from pathlib import Path
import unreal as u

root=Path(u.Paths.project_dir()).resolve(); out=root/'Saved/CarryReview'; out.mkdir(parents=True,exist_ok=True)
art=root/'ArtSource/Heroine_Tripo_Review/Carry'; tools=u.AssetToolsHelpers.get_asset_tools(); lib=u.EditorAssetLibrary
base='/Game/Constellation/Characters/Heroine/Base'; refined='/Game/Constellation/Characters/Heroine/Refined'
folder=base+'/Animation/Carry'; srcfolder=refined+'/Animations/Carry'
hero_path='/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine'
abp_path='/Game/Constellation/Characters/Heroine/Blueprints/ABP_Player_Heroine'
for path in [hero_path,abp_path,base+'/Player_Heroine_Skeleton',refined+'/SKEL_player_heroine_new']:
    relative=path.removeprefix('/Game/')+'.uasset'; src=root/'Content'/relative; backup=out/'backups'/relative
    backup.parent.mkdir(parents=True,exist_ok=True)
    if not backup.exists(): shutil.copy2(src,backup)
rows=json.loads((art/'motion_samples.json').read_text(encoding='utf-8'))
srcskel=u.load_asset(refined+'/SKEL_player_heroine_new'); dstskel=u.load_asset(base+'/Player_Heroine_Skeleton')
preview=u.load_asset(refined+'/SK_player_heroine_new_RunPreview'); oldmesh=u.load_asset(base+'/Player_Heroine')
result={'animations':[],'blueprints':{}}
previous=json.loads((out/'assets.json').read_text(encoding='utf-8')) if (out/'assets.json').exists() else {'animations':[]}
for row in rows:
    name=row['clip']; asset='AS_Heroine_Carry_'+name
    opt=u.FbxImportUI(); opt.import_mesh=False; opt.import_as_skeletal=True; opt.import_animations=True
    opt.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION; opt.automated_import_should_detect_type=False; opt.skeleton=srcskel
    opt.import_materials=False; opt.import_textures=False; opt.create_physics_asset=False
    opt.anim_sequence_import_data.import_uniform_scale=100.; opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False)
    opt.anim_sequence_import_data.set_editor_property('custom_sample_rate',30)
    task=u.AssetImportTask(); task.filename=str(art/(asset+'.fbx')); task.destination_path=srcfolder; task.destination_name=asset
    task.automated=True; task.replace_existing=True; task.save=True; task.options=opt; task.factory=u.FbxFactory()
    digest=hashlib.sha256((art/(asset+'.fbx')).read_bytes()).hexdigest()
    source=u.load_asset(srcfolder+'/'+asset)
    if not source or not any(x['name']==name and x['sha256']==digest for x in previous['animations']):
        tools.import_asset_tasks([task]); source=u.load_asset(srcfolder+'/'+asset)
    assert source,asset
    source.set_preview_skeletal_mesh(preview)
    seq=u.CarryEditorLibrary.retarget_carry_sequence(source,dstskel,folder,'AS_Carry_'+name+'_Game'); assert seq,name
    seq.set_preview_skeletal_mesh(oldmesh); seq.set_editor_property('enable_root_motion',False)
    seq.set_editor_property('force_root_lock',False)
    assert abs(seq.sequence_length-row['duration'])<.04,(name,seq.sequence_length)
    montage=u.load_asset(folder+'/AM_Carry_'+name)
    if not montage:
        factory=u.AnimMontageFactory(); factory.target_skeleton=dstskel; factory.source_animation=seq
        montage=tools.create_asset('AM_Carry_'+name,folder,u.AnimMontage,factory)
    montage.set_preview_skeletal_mesh(oldmesh)
    tracks=montage.get_editor_property('slot_anim_tracks')
    track=tracks[0]; track.set_editor_property('slot_name','CarryUpperBody' if name in ('Hold','Aim') else 'DefaultSlot')
    animtrack=track.get_editor_property('anim_track'); segments=animtrack.get_editor_property('anim_segments')
    segment=segments[0]; segment.set_editor_property('anim_reference',seq); segments[0]=segment
    animtrack.set_editor_property('anim_segments',segments); track.set_editor_property('anim_track',animtrack); tracks[0]=track
    montage.set_editor_property('slot_anim_tracks',tracks)
    for prop,seconds in [('blend_in',.12),('blend_out',.12)]:
        blend=montage.get_editor_property(prop); blend.set_editor_property('blend_time',seconds); montage.set_editor_property(prop,blend)
    if name in ('Hold','Aim'):
        montage.set_editor_property('enable_auto_blend_out',False)
    else:
        al=u.AnimationLibrary
        if not al.is_valid_anim_notify_track_name(montage,'Carry'): al.add_animation_notify_track(montage,'Carry')
        al.remove_animation_notify_events_by_track(montage,'Carry')
        notify=al.add_animation_notify_event(montage,'Carry',row['contact_seconds'],u.CarryAnimNotify)
        notify.set_editor_property('contact',{'Pickup':u.CarryContact.PICKUP,'Place':u.CarryContact.PLACE,'Throw':u.CarryContact.THROW}[name])
    for obj in [source,seq,montage]: assert lib.save_loaded_asset(obj,False)
    result['animations'].append({'name':name,'source':source.get_path_name(),'sequence':seq.get_path_name(),'montage':montage.get_path_name(),
        'duration':seq.sequence_length,'sha256':hashlib.sha256((art/(asset+'.fbx')).read_bytes()).hexdigest()})

matfolder='/Game/Constellation/Gameplay/Interaction/Materials'; mat=u.load_asset(matfolder+'/M_HoldPreview')
if not mat:
    mat=tools.create_asset('M_HoldPreview',matfolder,u.Material,u.MaterialFactoryNew())
    mat.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT); mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided',True)
    color=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionVectorParameter)
    color.set_editor_property('parameter_name','PreviewColor'); color.set_editor_property('default_value',u.LinearColor(0,.8,.65,1))
    opacity=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionScalarParameter)
    opacity.set_editor_property('parameter_name','Opacity'); opacity.set_editor_property('default_value',.3)
    u.MaterialEditingLibrary.connect_material_property(color,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    u.MaterialEditingLibrary.connect_material_property(opacity,'',u.MaterialProperty.MP_OPACITY)
    u.MaterialEditingLibrary.recompile_material(mat)
assert lib.save_loaded_asset(mat,False)

def blueprint(name,path,parent):
    bp=u.load_asset(path+'/'+name)
    if not bp:
        f=u.BlueprintFactory(); f.set_editor_property('parent_class',parent); bp=tools.create_asset(name,path,u.Blueprint,f)
    assert bp,name
    return bp
hold=blueprint('Ac_Holdable','/Game/Constellation/Gameplay/Interaction/Components',u.HoldableComponent)
u.BlueprintEditorLibrary.compile_blueprint(hold); assert lib.save_loaded_asset(hold,False)
box=blueprint('BP_Holdable_TestBox','/Game/Constellation/Gameplay/Interaction/Actors',u.Actor)
report=u.CarryEditorLibrary.configure_test_box(box,hold.generated_class()); assert 'errors=0' in report,report
result['blueprints']['test_box']=report; assert lib.save_loaded_asset(box,False)
hero=u.load_asset(hero_path); abp=u.load_asset(abp_path)
for key,report in [('input',u.CarryEditorLibrary.install_carry_input(hero)),('overlay',u.CarryEditorLibrary.install_carry_overlay(abp)),
                   ('settings',u.CarryEditorLibrary.configure_carry_blueprint(hero,folder,mat))]:
    result['blueprints'][key]=report; assert 'errors=0' in report,report
for obj in [hero,abp,dstskel]: assert lib.save_loaded_asset(obj,False)
(out/'assets.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
u.log('CARRY_ASSETS_SETUP_COMPLETE '+json.dumps(result['blueprints']))
