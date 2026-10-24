import unreal as u
from pathlib import Path
import json,traceback
out=Path(u.Paths.project_dir())/'Saved/JumpAcquisition';out.mkdir(parents=True,exist_ok=True)
try:
 w=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 rows=[]
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  if any(s in (a.get_class().get_name()+a.get_actor_label()).lower() for s in ['star','별','sceneevent']):
   r={'name':a.get_name(),'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'transform':str(a.get_actor_transform()),'properties':{}}
   for p in ['target_level_sequence','unlock_ability','is_hidden_at_sequence_start','director','source','original_sequence','trigger']:
    try:r['properties'][p]=str(a.get_editor_property(p))
    except:pass
   r['components']=[{'name':c.get_name(),'class':c.get_class().get_name(),'transform':str(c.get_world_transform()) if isinstance(c,u.SceneComponent) else ''} for c in a.get_components_by_class(u.ActorComponent)]
   rows.append(r)
 (out/'audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
 for n in ['BP_Star_Object','BP_Star_Object_Sequence']:
  b=u.load_asset('/Game/Constellation/Gameplay/Interaction/Actors/'+n)
  (out/(n+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(b),encoding='utf8')
 u.log('JUMP_AUDIT_OK')
except: (out/'audit-error.txt').write_text(traceback.format_exc(),encoding='utf8')
finally:u.SystemLibrary.quit_editor()
