"""Measure generated hit directions without editing any assets. Run in Unreal Python."""
import json, math
from pathlib import Path
import unreal as u
base='/Game/Constellation/Characters/Heroine/Refined/Animations/'
neutral=u.load_asset(base+'AS_player_heroine_new_PreviewRelaxed')
assert neutral
ext=u.AnimPoseExtensions
options=u.AnimPoseEvaluationOptions(); options.evaluation_type=u.AnimDataEvalType.RAW
zero=ext.get_anim_pose_at_time(neutral,0.,options)
bones=['spine_03','head']
origin={b:ext.get_bone_pose(zero,b,u.AnimPoseSpaces.WORLD).translation for b in bones}
# Maintained Core setup uses identity mesh-relative rotation; world-facing gallery
# actor yaw does not change actor-local combat direction.
def actor_delta(v):return [v.x,v.y,v.z]
expected={'Front':[-1,0],'Back':[1,0],'Left':[0,1],'Right':[0,-1]}
report={'space':'actor coordinates with maintained Core identity mesh-relative rotation; gallery world yaw excluded',
        'expected_recoil_xy':expected,'directions':{}}
for direction in expected:
 seq=u.load_asset(base+'AS_player_heroine_new_Hit_'+direction);assert seq
 samples=[]
 for frame in range(25):
  fraction=frame/24
  pose=ext.get_anim_pose_at_time(seq,seq.sequence_length*fraction,options)
  values={b:actor_delta(ext.get_bone_pose(pose,b,u.AnimPoseSpaces.WORLD).translation-origin[b]) for b in bones}
  samples.append({'fraction':fraction,'actor_delta':values})
 peaks={}
 for bone in bones:
  peak=max(samples,key=lambda v:sum(x*x for x in v['actor_delta'][bone][:2]))
  delta=peak['actor_delta'][bone];length=math.hypot(*delta[:2]);target=expected[direction]
  peaks[bone]={'fraction':peak['fraction'],'delta_actor':delta,'horizontal_length':length,
               'alignment_with_expected':sum(delta[i]*target[i] for i in (0,1))/max(length,1e-8),
               'heading_degrees':math.degrees(math.atan2(delta[1],delta[0]))}
 report['directions'][direction]={'peaks':peaks,'samples':samples}
out=Path(u.Paths.project_dir()).resolve()/'Saved/VFXImplementation/hit-direction-audit.json'
out.write_text(json.dumps(report,indent=2),encoding='utf8')
u.log('HIT_DIRECTION_AUDIT '+json.dumps({k:v['peaks'] for k,v in report['directions'].items()}))
