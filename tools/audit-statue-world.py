import unreal as u
from pathlib import Path
world=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
out=Path(u.Paths.project_saved_dir())/'StatueDirector'; lines=[]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 if any(s in a.get_class().get_name() for s in ['Statue','NPC_Player','SequenceManager']) or isinstance(a,u.CineCameraActor):
  lines.append(str(a)+' '+a.get_actor_label()+' '+str(a.get_actor_transform()))
  if isinstance(a,u.CineCameraActor): lines.append(str(a.get_cine_camera_component().get_editor_property('filmback')))
(out/'actors.txt').write_text('\n'.join(lines),encoding='utf-8')
