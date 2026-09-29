import unreal,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;B='/Game/Resources/Characters/PC/player_heroine_new';A=B+'/Animations'
a=unreal.load_asset(A+'/AS_player_heroine_new_Attack01_Horizontal');mesh=unreal.load_asset(B+'/SK_player_heroine_new_RunPreview')
mn='AM_player_heroine_new_Attack01_Horizontal';old=unreal.load_asset(A+'/'+mn)
assert abs(a.sequence_length-1)<.001
if old and abs(old.sequence_length-1)>.001:
 refs=unreal.AssetRegistryHelpers.get_asset_registry().get_referencers(A+'/'+mn,unreal.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True)) or []
 assert not refs,list(refs)
 assert unreal.EditorAssetLibrary.delete_asset(A+'/'+mn)
 old=None
m=old
if not m:
 factory=unreal.AnimMontageFactory();factory.set_editor_property('target_skeleton',a.get_editor_property('skeleton'));factory.set_editor_property('source_animation',a)
 m=unreal.AssetToolsHelpers.get_asset_tools().create_asset(mn,A,unreal.AnimMontage,factory)
assert m
m.set_preview_skeletal_mesh(mesh);m.set_editor_property('rate_scale',1.)
for k,v in [('blend_in',.08),('blend_out',.12)]:
 b=m.get_editor_property(k);b.set_editor_property('blend_time',v);m.set_editor_property(k,b)
lib=unreal.AnimationLibrary
if not lib.is_valid_anim_notify_track_name(m,'Combat'):lib.add_animation_notify_track(m,'Combat')
lib.remove_animation_notify_events_by_track(m,'Combat')
events=[('Hitbox On',.35),('Hitbox Off',.50),('ComboWindow Open',.50),('ComboWindow Close',.65),('End Attack',.99)]
for name,t in events:
 notify=lib.add_animation_notify_event(m,'Combat',t,unreal.AnimNotify_PlayMontageNotify)
 assert notify;notify.set_editor_property('notify_name',name)
unreal.EditorAssetLibrary.set_metadata_tag(m,'ComboWindowSeconds','0.50-0.65');unreal.EditorAssetLibrary.set_metadata_tag(m,'NextAttackBlendSeconds','0.08')
assert unreal.EditorAssetLibrary.save_loaded_asset(m,only_if_is_dirty=False)
notifies=[{'name':str(n.notify.get_editor_property('notify_name')),'time':lib.get_anim_notify_event_trigger_time(n)} for n in lib.get_animation_notify_events(m)]
report={'pass':True,'sequence':a.get_path_name(),'montage':m.get_path_name(),'duration_s':a.sequence_length,'montage_duration_s':m.sequence_length,'notifies':notifies,'source_sha256':hashlib.sha256((P/'AS_player_heroine_new_Attack01_Horizontal.fbx').read_bytes()).hexdigest()}
assert abs(a.sequence_length-1)<.001 and abs(m.sequence_length-1)<.001 and len(notifies)==5
(P/'unreal_import.json').write_text(json.dumps(report,indent=2));print('ATTACK_MONTAGE_READY',json.dumps(report))
