import unreal as u
from pathlib import Path
out=Path(u.Paths.project_dir()).resolve()/'Saved/CarryReview'
rows=[]
assets=u.EditorAssetLibrary.list_assets('/Game/Constellation/Characters/Heroine/Base/Animation',True,False)
assets.append('/Game/Constellation/Characters/Shared/Animations/Idle')
for path in assets:
    if 'Idle' not in path and 'Carry_Hold' not in path and 'Carry_Pickup' not in path and 'Carry_Place' not in path: continue
    seq=u.load_asset(path)
    if not isinstance(seq,u.AnimSequence): continue
    rows.append(str(path)+' settings '+str({p:str(seq.get_editor_property(p)) for p in ('force_root_lock','enable_root_motion','root_motion_root_lock','retarget_source','retarget_source_asset','additive_anim_type')}))
    for t in (0.,min(.55,seq.sequence_length),min(.85,seq.sequence_length)):
        for bone in ('Hips','LeftFoot','LeftHand'):
            pose=u.AnimationLibrary.get_bone_pose_for_time(seq,bone,t,False)
            rows.append(f'{path} {t} {bone} {pose}')
(out/'animation-pose-inspection.txt').write_text('\n'.join(rows),encoding='utf-8')
for name in ('Pickup','Place','Throw','Hold','Aim'):
    am=u.load_asset('/Game/Constellation/Characters/Heroine/Base/Animation/Carry/AM_Carry_'+name)
    u.log('CARRY_SLOTS '+name+' '+str(am.get_editor_property('slot_anim_tracks')))
bp=u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/ABP_Player_Heroine')
(out/'graphs/ABP_Carry_After.txt').write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(bp),encoding='utf-8')
u.log('CARRY_POSE_INSPECTION_COMPLETE')
