import unreal as u
from pathlib import Path
import json,traceback
out=Path(u.Paths.project_dir())/'Saved/JumpAcquisition';out.mkdir(parents=True,exist_ok=True)
try:
 a=u.load_asset('/Game/SceneDirector/School/DA_JumpAcquisition')
 assert a,'Jump acquisition director is not installed'
 assert not a.get_editor_property('needs_compile'),'Director needs compile'
 steps=list(a.get_editor_property('steps'))
 shot=next(s for s in steps if s.get_editor_property('type')==u.DirectorNodeType.CAMERA_SWITCH)
 import math
 timed={u.DirectorNodeType.WAIT,u.DirectorNodeType.CAMERA_MOVE,u.DirectorNodeType.DIALOGUE}
 frames=sum(max(1,math.floor(s.get_editor_property('duration')*30+.50001)) for s in steps if s.get_editor_property('type') in timed)
 assert abs(shot.get_editor_property('duration')-frames/30.)<.001,'Camera must hold across waits, UI and narration'
 assert not any(s.get_editor_property('activate_camera') for s in steps if s.get_editor_property('type')==u.DirectorNodeType.CAMERA_MOVE),'Motion must not interrupt continuous shot'
 cues=[str(s.get_editor_property('action_parameters').get_editor_property('identifier')) for s in steps if s.get_editor_property('type')==u.DirectorNodeType.GAME_ACTION]
 for cue in ['Begin','Inspect','Reach','Contact','Surprise','Absorb','AbilityUI','Chest','Palm','Release','Commit']:
  assert cue in cues,cue
 assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
 star=next(x for x in actors if x.get_actor_label()=='star_object_jump')
 assert star.get_component_by_class(u.SceneDirectorInteractionComponent),'Interaction component missing'
 bindings=[x for x in actors if isinstance(x,u.SceneEventBinding) and x.get_editor_property('source')==star]
 assert len(bindings)==1,'Expected one interaction binding'
 assert bindings[0].get_editor_property('director')==a
 assert bindings[0].get_editor_property('trigger')==u.SceneEventTrigger.INTERACTION
 assert bindings[0].get_editor_property('repeat')==u.SceneEventRepeat.ONCE_PER_VISIT
 bp=u.load_asset('/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object')
 text=u.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
 assert text.count('NodeComment="JumpAcquisition.Route"')==1,'Binding-first interaction route missing/duplicated'
 (out/'asset-verification.json').write_text(json.dumps({'ok':True,'steps':len(steps),'cues':cues},indent=2),encoding='utf8')
except:
 (out/'asset-verification.json').write_text(json.dumps({'ok':False,'error':traceback.format_exc()},indent=2),encoding='utf8')
finally:
 if 'Automation RunTests' not in u.SystemLibrary.get_command_line():u.SystemLibrary.quit_editor()
