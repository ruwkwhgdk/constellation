"""Create four reviewable, upper-body hit reactions on the maintained heroine skeleton.
Uses the authored Sword_Damaged local rotation changes, converted through component
space; pelvis, legs, fingers and skirt retain the maintained Relaxed pose. No mesh
replacement, root movement, translation retargeting or unverified bone-name copying.
Run in Unreal Editor Python. The JSON report is technical validation, not visual approval.
"""
import json, math
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
BASE='/Game/Constellation/Characters/Heroine/Refined/Animations/'
neutral=u.load_asset(BASE+'AS_player_heroine_new_PreviewRelaxed')
source=u.load_asset('/Game/Constellation/Characters/Shared/Animations/Sword_Damaged')
assert neutral and source
ext=u.AnimPoseExtensions
options=u.AnimPoseEvaluationOptions()
options.evaluation_type=u.AnimDataEvalType.RAW
np=ext.get_anim_pose_at_time(neutral,0.,options)
sp=ext.get_anim_pose_at_time(source,0.,options)
names=[str(n) for n in ext.get_bone_names(np)]
# Source, target, source parent, target parent, maximum per-joint angle in degrees.
MAPPING=[('spine','spine_01','hips','pelvis',7),('spine1','spine_02','spine','spine_01',8),
 ('spine2','spine_03','spine1','spine_02',9),('neck','neck_01','spine2','spine_03',6),
 ('head','head','neck','neck_02',7),('leftshoulder','clavicle_l','spine2','spine_03',5),
 ('rightshoulder','clavicle_r','spine2','spine_03',5),('leftarm','upperarm_l','leftshoulder','clavicle_l',12),
 ('rightarm','upperarm_r','rightshoulder','clavicle_r',12),('leftforearm','lowerarm_l','leftarm','upperarm_l',10),
 ('rightforearm','lowerarm_r','rightarm','upperarm_r',10)]

def quat(q): return (q.x,q.y,q.z,q.w)
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
def inv(q): return (-q[0],-q[1],-q[2],q[3])
def limit(q,amount,max_degrees):
 length=math.sqrt(sum(v*v for v in q));q=tuple(v/length for v in q)
 if q[3]<0:q=tuple(-v for v in q)
 angle=2*math.acos(max(-1.,min(1.,q[3])));norm=math.sqrt(sum(v*v for v in q[:3]))
 if norm<1e-8:return (0.,0.,0.,1.)
 angle=min(angle*amount,math.radians(max_degrees))
 return tuple(v/norm*math.sin(angle/2) for v in q[:3])+(math.cos(angle/2),)
def rot(p,b,world=False):return quat(ext.get_bone_pose(p,b,u.AnimPoseSpaces.WORLD if world else u.AnimPoseSpaces.LOCAL).rotation)

# Measured with audit-hit-reaction-directions.py on the maintained identity-relative
# Core mesh: unaligned Front head recoil peaked at 140.497054 degrees, chest141.674169.
# Rotate authored deltas by the measured39.502946-degree offset to recoil toward-X.
FACING_ALIGNMENT_DEGREES=180.-140.49705444680015
frames=24
poses=[ext.get_anim_pose_at_time(source,source.sequence_length*i/frames,options) for i in range(frames+1)]
baseposes={b:ext.get_bone_pose(np,b,u.AnimPoseSpaces.LOCAL) for b in names}
report={'source':source.get_path_name(),'neutral':neutral.get_path_name(),'asset_duration':1.0,'runtime_duration':.35,
 'method':'authored upper-body local deltas converted through initial parent component axes; bounded directional variants',
 'facing_alignment_degrees':FACING_ALIGNMENT_DEGREES,
 'preserved':'all neutral translations/scales, pelvis/legs/feet/fingers/garment tracks; no mesh edits',
 'visual_review':'required: opposite angles, foot contact, arm/skirt intersection and transition playback', 'assets':[]}
for direction,yaw in [('Front',0),('Back',180),('Left',-90),('Right',90)]:
 name='AS_player_heroine_new_Hit_'+direction
 path=BASE+name
 sequence=u.load_asset(path)
 if not sequence:
  sequence=u.EditorAssetLibrary.duplicate_asset(neutral.get_path_name().split('.')[0],path)
 assert sequence
 controller=sequence.get_editor_property('controller')
 # Keep the duplicate's verified 24fps compression target. Runtime retimes this
 # 1-second curve to .35s; changing model fps alone leaves stale platform sampling.
 controller.open_bracket("Author directional combat reaction",False)
 controller.set_frame_rate(u.FrameRate(numerator=24,denominator=1),False)
 controller.set_number_of_frames(u.FrameNumber(value=frames),False)
 keys={b:[rot(np,b)]*(frames+1) for b in names}
 half=math.radians(yaw+FACING_ALIGNMENT_DEGREES)/2;turn=(0,0,math.sin(half),math.cos(half))
 peaks={}
 for old,new,oldparent,newparent,maximum in MAPPING:
  reference=rot(sp,old);src_parent=rot(sp,oldparent,True);dst_parent=rot(np,newparent,True)
  values=[]
  for i,pose in enumerate(poses):
   t=i/frames
   # The authored timing is retained inside a short impact/recovery window; endpoints are exact neutral.
   envelope=min(1.,t/.12)*min(1.,(1-t)/.3)
   delta=mul(rot(pose,old),inv(reference))
   world=mul(mul(src_parent,delta),inv(src_parent))
   world=mul(mul(turn,world),inv(turn))
   local=mul(mul(inv(dst_parent),world),dst_parent)
   bounded=limit(local,.8*max(0.,envelope),maximum)
   values.append(mul(bounded,rot(np,new)))
  keys[new]=values
  peaks[new]=max(math.degrees(2*math.acos(min(1.,abs(mul(q,inv(rot(np,new)))[3])))) for q in values)
 for bone in names:
  pose=baseposes[bone]
  assert controller.set_bone_track_keys(bone,[pose.translation]*(frames+1),[u.Quat(*q) for q in keys[bone]],[pose.scale3d]*(frames+1),False),bone
 controller.close_bracket(False)
 assert u.EditorAssetLibrary.save_loaded_asset(sequence,False)
 assert abs(sequence.sequence_length-1.)<.001
 report['assets'].append({'asset':sequence.get_path_name(),'bone_count':len(names),'peaks_degrees':peaks})
out=ROOT/'Saved/VFXImplementation';out.mkdir(parents=True,exist_ok=True)
(out/'hit-reaction-generation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
u.log('COMBAT_HIT_REACTIONS_GENERATED')
