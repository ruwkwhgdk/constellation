import unreal,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;B='/Game/Resources/Characters/PC/player_heroine_new';A=B+'/Animations'
skel=unreal.load_asset(B+'/SKEL_player_heroine_new');mesh=unreal.load_asset(B+'/SK_player_heroine_new_RunPreview')
opt=unreal.FbxImportUI();opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_animations=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;opt.automated_import_should_detect_type=False;opt.skeleton=skel;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False
opt.anim_sequence_import_data.import_uniform_scale=100.;opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate',False);opt.anim_sequence_import_data.set_editor_property('custom_sample_rate',60)
name='AS_player_heroine_new_Attack01_Horizontal';task=unreal.AssetImportTask();task.filename=str(P/(name+'.fbx'));task.destination_path=A;task.destination_name=name;task.automated=True;task.replace_existing=True;task.save=True;task.options=opt;task.factory=unreal.FbxFactory()
tools=unreal.AssetToolsHelpers.get_asset_tools();tools.import_asset_tasks([task]);a=unreal.load_asset(A+'/'+name);assert a
a.set_preview_skeletal_mesh(mesh);a.set_editor_property('enable_root_motion',False);a.set_editor_property('rate_scale',1.)
lib=unreal.AnimationLibrary
if not lib.is_valid_anim_notify_track_name(a,'Combat'):lib.add_animation_notify_track(a,'Combat')
lib.remove_all_animation_sync_markers(a)
timing=json.loads((P/'attack01_timing.json').read_text())
events=[('Hitbox On',.35),('Hitbox Off',.50),('ComboWindow Open',.50),('ComboWindow Close',.65),('End Attack',.99)]
for name,t in events:lib.add_animation_sync_marker(a,name.replace(' ','_'),t,'Combat')
assert unreal.EditorAssetLibrary.save_loaded_asset(a,only_if_is_dirty=False)
assert abs(a.sequence_length-1)<.001
unreal.EditorAssetLibrary.set_metadata_tag(a,'ComboWindowSeconds','0.50-0.65')
assert unreal.EditorAssetLibrary.save_loaded_asset(a,only_if_is_dirty=False)
montage_script=P/'fix_montage.py'
exec(compile(montage_script.read_text(),str(montage_script),'exec'),{'__file__':str(montage_script),'__name__':'__main__'})
