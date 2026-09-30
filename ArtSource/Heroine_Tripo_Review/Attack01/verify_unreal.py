import unreal,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;B='/Game/Constellation/Characters/Heroine/Refined'
a=unreal.load_asset(B+'/Animations/AS_player_heroine_new_Attack01_Horizontal');m=unreal.load_asset(B+'/Animations/AM_player_heroine_new_Attack01_Horizontal');mesh=unreal.load_asset(B+'/SK_player_heroine_new_RunPreview')
assert a and m and abs(a.sequence_length-1)<.001 and abs(m.sequence_length-1)<.001
assert a.get_editor_property('skeleton')==mesh.skeleton==m.get_editor_property('skeleton')
assert a.get_editor_property('rate_scale')==m.get_editor_property('rate_scale')==1
tracks=m.slot_anim_tracks;assert len(tracks)==1
seg=tracks[0].anim_track.anim_segments[0];assert seg.anim_reference==a and seg.anim_play_rate==1
lib=unreal.AnimationLibrary
ns=[{'name':str(n.notify.get_editor_property('notify_name')),'time':lib.get_anim_notify_event_trigger_time(n)} for n in lib.get_animation_notify_events(m)]
assert len(ns)==5
for name,t in [('Hitbox On',.35),('Hitbox Off',.5),('ComboWindow Open',.5),('ComboWindow Close',.65),('End Attack',.99)]:assert any(n['name']==name and abs(n['time']-t)<.001 for n in ns)
poses={n:[str(lib.get_bone_pose_for_time(a,n,t,False)) for t in [0,.25,.4,.5,.75,1.]] for n in ['root','pelvis','hand_r','foot_l','foot_r']}
assert poses['hand_r'][0]!=poses['hand_r'][2]
reference=unreal.load_asset('/Game/Constellation/Characters/Heroine/Base/Animation/AM_Sword_Attack_Horizontal');assert abs(reference.sequence_length-1.2)<.001 and reference.get_editor_property('rate_scale')==1.25
report={'pass':True,'sequence':a.get_path_name(),'montage':m.get_path_name(),'duration_s':a.sequence_length,'montage_duration_s':m.sequence_length,'notifies':ns,'original_montage_unchanged':True,'source_sha256':hashlib.sha256((P/'AS_player_heroine_new_Attack01_Horizontal.fbx').read_bytes()).hexdigest(),'pose_samples':poses}
(P/'unreal_verification.json').write_text(json.dumps(report,indent=2));print('ATTACK_SAVED_ASSETS_VERIFIED')
