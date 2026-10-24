import unreal as u,json,math,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/JumpAcquisition/AnimationIntegration_20261019_004921_228317'
try:
 rows=json.loads((O/'recording.json').read_text());names={'Inspect':'Star_Inspect','Reach':'ReachTouch_Right','Contact':'ReachTouch_Right','Surprise':'Star_Surprise','Absorb':'Star_Absorb','Chest':'Star_RecoverChest','Palm':'Star_PalmConfused'}
 assets={k:u.load_asset('/Game/Constellation/Characters/Heroine/GamePilot/Interaction/AS_'+v) for k,v in names.items()};cache={};results={}
 for i,row in enumerate(rows):
  key=row['phase'];pos=row.get('position')
  if key not in assets or pos is None or pos<.2 or i%5:continue
  asset=assets[key];last=round(asset.get_play_length()*30);errors=[]
  for frame in sorted(set(max(0,min(last,round(pos*30)+n)) for n in [-1,0,1])):
   pair=(key,frame)
   if pair not in cache:cache[pair]=u.AnimPoseExtensions.get_anim_pose_at_frame(asset,frame,u.AnimPoseEvaluationOptions(should_retarget=False))
   worst=angle=0
   for bone,actual in row['bones'].items():
    expected=u.AnimPoseExtensions.get_bone_pose(cache[pair],bone,u.AnimPoseSpaces.WORLD);t=expected.translation;q=expected.rotation
    worst=max(worst,math.dist(actual['t'],[t.x,t.y,t.z]));av=actual['q'];bv=[q.x,q.y,q.z,q.w];dot=abs(sum(a*b for a,b in zip(av,bv)))/math.sqrt(sum(a*a for a in av)*sum(b*b for b in bv));angle=max(angle,math.degrees(2*math.acos(min(1.,dot))))
   errors.append((worst,angle,frame))
  best=min(errors);entry=results.setdefault(key,{'max_position_cm':0,'max_rotation_deg':0,'samples':0})
  entry['max_position_cm']=max(entry['max_position_cm'],best[0]);entry['max_rotation_deg']=max(entry['max_rotation_deg'],best[1]);entry['samples']+=1
 (O/'runtime-pose-comparison.json').write_text(json.dumps(results,indent=2))
except:(O/'pose-check-error.txt').write_text(traceback.format_exc());u.log_error(traceback.format_exc())
