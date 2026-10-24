"""Replace gameplay references without deleting the original model yet."""
import unreal as u,json
from pathlib import Path
P=Path(__file__).resolve().parent
B='/Game/Constellation/Characters/Enemies/Slime_Liquid'
OLD='/Game/Constellation/Characters/Enemies/Slime_Normal'
reg=u.AssetRegistryHelpers.get_asset_registry();reg.search_all_assets(True)
opts=u.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True)
old=u.load_asset(OLD+'/SKM_Slime_Normal');new=u.load_asset(B+'/SKM_Slime_Liquid')
yellow=u.load_asset(B+'/Materials/MI_Slime_Gel_Yellow')
refs=[str(x) for x in reg.get_referencers(OLD+'/SKM_Slime_Normal',opts)]
objects=[];worlds=[];blueprints=[];changes=[]
for path in refs:
 obj=u.load_asset(path)
 if isinstance(obj,u.World):worlds.append(path)
 objects.append(obj)
for data in reg.get_assets_by_path('/Game/Constellation/Characters/Enemies/Blueprints',True):
 obj=data.get_asset()
 if isinstance(obj,u.Blueprint) and not isinstance(obj,u.AnimBlueprint) and ('Slime' in obj.get_name() or obj.get_name()=='BP_Monster_Patrol'):objects.append(obj)
objects.append(u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Slime'))
def replace_components():
 count=0
 for c in u.ObjectIterator(u.SkeletalMeshComponent):
  mesh=c.get_editor_property('skeletal_mesh_asset')
  if mesh!=old and mesh!=new:continue
  path=c.get_path_name()
  is_yellow=any(x and x.get_name()=='MI_Slime_Yellow' for x in c.get_editor_property('override_materials')) or 'Slime_Yellow' in path
  if mesh==old or is_yellow:
   c.modify();c.set_skeletal_mesh_asset(new);c.set_editor_property('override_materials',[])
   if is_yellow:
    for i,s in enumerate(new.get_editor_property('materials')):
     if 'Indigo' in str(s.material_slot_name):c.set_material(i,yellow)
   changes.append(path);count+=1
 return count
replace_components()
for obj in objects:
 if not obj:continue
 if isinstance(obj,u.AnimSequence):obj.set_preview_skeletal_mesh(new)
 elif isinstance(obj,u.Skeleton):obj.set_skeleton_preview_mesh(new)
 elif isinstance(obj,u.Blueprint) and not isinstance(obj,u.AnimBlueprint):
  u.BlueprintEditorLibrary.compile_blueprint(obj);blueprints.append(obj.get_path_name())
 u.EditorAssetLibrary.save_loaded_asset(obj,False)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
# Map packages were loaded, edited and saved with their components above. Do not
# switch active maps while other edited worlds are still dirty (UE rejects that).
# Reimport the existing Idle sequence in place, preserving all Blueprint and
# cinematic bindings. Original gameplay clips and montage notifies are untouched.
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
opt=u.FbxImportUI();opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_animations=True;opt.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION;opt.automated_import_should_detect_type=False;opt.skeleton=new.get_editor_property('skeleton');opt.import_materials=False;opt.import_textures=False
opt.anim_sequence_import_data.import_uniform_scale=1
opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False);opt.anim_sequence_import_data.set_editor_property('custom_sample_rate',24)
t=u.AssetImportTask();t.filename=str(P/'SKM_Slime_Liquid.fbx');t.destination_path=OLD+'/Animation';t.destination_name='AS_Slime_Idle';t.automated=True;t.replace_existing=True;t.save=True;t.options=opt;t.factory=u.FbxFactory()
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
idle=u.load_asset(OLD+'/Animation/AS_Slime_Idle');assert abs(idle.get_play_length()-4)<.001
idle.set_preview_skeletal_mesh(new);u.EditorAssetLibrary.save_loaded_asset(idle,False)
u.EditorLoadingAndSavingUtils.new_blank_map(False)
bp=u.load_asset('/Game/Constellation/Characters/Enemies/Blueprints/BP_Slime_Base')
probe=actors.spawn_actor_from_class(bp.generated_class(),u.Vector(0,0,300))
assert probe.get_component_by_class(u.SkeletalMeshComponent).get_editor_property('skeletal_mesh_asset')==new,'Saved Blueprint still uses old mesh'
actors.destroy_actor(probe)
(P/'replacement-report.json').write_text(json.dumps({'changed_components':sorted(set(changes)),'maps':worlds,'blueprints':blueprints,'idle_duration':idle.get_play_length(),'old_model_retained_until_tests':True},indent=2))
