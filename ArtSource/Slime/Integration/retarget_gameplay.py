"""Preserve root/Center motion and timing; remove old Top compression folding.
The old independently scaled Top was authored for different skinning. New Top
follows the Center deformation field so the continuous gel cannot invert.
"""
import unreal as u,json
from pathlib import Path
P=Path(__file__).resolve().parent
B='/Game/Constellation/Characters/Enemies/Slime_Normal/Animation'
report=[]
for name in ['Move','Attack','Damaged','Dead','Jump']:
 a=u.load_asset(B+'/AS_Slime_'+name)
 model=a.get_editor_property('data_model_interface')
 controller=a.get_editor_property('controller')
 if not controller:
  controller=u.AnimationSequencerController();controller.set_model(model)
 frames=u.AnimationLibrary.get_num_frames(a)
 duration=a.get_play_length()
 positions=[];rotations=[];scales=[]
 offset=u.Vector(0,0,153.033815-47.817761)
 for i in range(frames+1):
  center=u.AnimationLibrary.get_bone_pose_for_time(a,'Center',duration*i/frames,False)
  positions.append(center.transform_location(offset))
  rotations.append(center.rotation);scales.append(center.scale3d)
 controller.open_bracket('Adapt slime Top to the new continuous gel skin')
 assert controller.set_bone_track_keys('Top',positions,rotations,scales)
 controller.close_bracket()
 assert abs(a.get_play_length()-duration)<1e-6
 u.EditorAssetLibrary.set_metadata_tag(a,'LiquidSlimeRetarget','Top follows Center deformation; root, Center, duration and notifies retained')
 u.EditorAssetLibrary.save_loaded_asset(a,False)
 report.append({'clip':name,'duration':duration,'frames':frames,'keys':len(positions)})
(P/'retarget-report.json').write_text(json.dumps(report,indent=2))
