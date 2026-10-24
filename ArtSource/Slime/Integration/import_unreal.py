import unreal as u,json,zipfile
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=Path(u.Paths.project_dir()).resolve()
OLD='/Game/Constellation/Characters/Enemies/Slime_Normal'
NEW='/Game/Constellation/Characters/Enemies/Slime_Liquid'
reg=u.AssetRegistryHelpers.get_asset_registry();reg.search_all_assets(True)
opts=u.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True)
backup=P/'before-integration.zip'
if not backup.exists():
 packages=set(str(x.package_name) for x in reg.get_assets_by_path('/Game/Constellation/Characters/Enemies',recursive=True))
 for p in list(packages):packages.update(str(x) for x in reg.get_referencers(p,opts))
 packages.update(['/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Slime','/Game/Constellation/Characters/NPC/Blueprints/BP_NPC_Slime'])
 with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:
  for package in sorted(packages):
   if not package.startswith('/Game/'):continue
   for ext in ['.uasset','.umap','.uexp','.ubulk']:
    f=ROOT/'Content'/(package[6:]+ext)
    if f.exists():z.write(f,f.relative_to(ROOT))
 (P/'backup-packages.json').write_text(json.dumps(sorted(packages),indent=2))
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
sk=u.load_asset(OLD+'/SK_Slime_Normal')
opt=u.FbxImportUI()
opt.import_mesh=True;opt.import_as_skeletal=True;opt.import_animations=True
opt.mesh_type_to_import=u.FBXImportType.FBXIT_SKELETAL_MESH
opt.automated_import_should_detect_type=False
opt.skeleton=sk;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False
opt.skeletal_mesh_import_data.import_uniform_scale=1
opt.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose',True)
opt.skeletal_mesh_import_data.set_editor_property('use_t0_as_ref_pose',False)
opt.anim_sequence_import_data.import_uniform_scale=1
opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False)
opt.anim_sequence_import_data.set_editor_property('custom_sample_rate',24)
task=u.AssetImportTask();task.filename=str(P/'SKM_Slime_Liquid.fbx');task.destination_path=NEW;task.destination_name='SKM_Slime_Liquid';task.automated=True;task.replace_existing=True;task.save=True;task.options=opt;task.factory=u.FbxFactory()
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
mesh=u.load_asset(NEW+'/SKM_Slime_Liquid');assert mesh
assert mesh.get_editor_property('skeleton')==sk
dest=NEW+'/AS_Slime_Liquid_Idle'
ao=u.FbxImportUI();ao.import_mesh=False;ao.import_as_skeletal=True;ao.import_animations=True;ao.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION;ao.automated_import_should_detect_type=False;ao.skeleton=sk;ao.import_materials=False;ao.import_textures=False
ao.anim_sequence_import_data.import_uniform_scale=1
ao.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False)
ao.anim_sequence_import_data.set_editor_property('custom_sample_rate',24)
ta=u.AssetImportTask();ta.filename=str(P/'SKM_Slime_Liquid.fbx');ta.destination_path=NEW;ta.destination_name='AS_Slime_Liquid_Idle';ta.automated=True;ta.replace_existing=True;ta.save=True;ta.options=ao;ta.factory=u.FbxFactory()
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([ta])
anim=u.load_asset(dest);assert anim
anim.set_preview_skeletal_mesh(mesh)
u.EditorAssetLibrary.save_loaded_asset(anim,False)
assert abs(anim.get_play_length()-4)<.01
opt=u.FbxImportUI();opt.import_mesh=True;opt.import_as_skeletal=False;opt.import_animations=False;opt.import_materials=False;opt.import_textures=False;opt.automated_import_should_detect_type=False;opt.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
opt.static_mesh_import_data.combine_meshes=True;opt.static_mesh_import_data.import_uniform_scale=1
st=u.AssetImportTask();st.filename=str(P/'SM_Slime_Liquid.fbx');st.destination_path=NEW;st.destination_name='SM_Slime_Liquid';st.automated=True;st.replace_existing=True;st.save=True;st.options=opt;st.factory=u.FbxFactory()
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([st])
u.EditorAssetLibrary.save_loaded_asset(sk,False)
rp=sk.get_reference_pose()
assert abs(rp.get_ref_bone_pose('Root').translation.z+84.327904)<.001
assert abs(rp.get_ref_bone_pose('Center').translation.z-47.817761)<.001
assert abs(rp.get_ref_bone_pose('Top').translation.z-153.033815)<.001
assert rp.get_ref_bone_pose('drop').translation.z>100, 'Additional bone reference pose must be in centimeters'
assert abs(u.AnimationLibrary.get_bone_pose_for_time(anim,'Root',0,False).translation.z+84.327904)<.001
report={'imported':list(task.imported_object_paths),'animation':anim.get_path_name(),'duration':anim.get_play_length(),'bounds':str(mesh.get_bounds()),'materials':str(mesh.get_editor_property('materials')),'reference':{str(b):str(rp.get_ref_bone_pose(b)) for b in rp.get_bone_names()},'root_pose':str(u.AnimationLibrary.get_bone_pose_for_time(anim,'Root',0,False))}
(P/'import-report.json').write_text(json.dumps(report,indent=2))
