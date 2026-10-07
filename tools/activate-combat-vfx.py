"""Enable the shared gallery presentation on maintained combat maps; preserve all combat data."""
import unreal as u
import json,shutil,datetime
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve()
folder=root/'Saved/CombatAudit/VFXActivation'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S');folder.mkdir(parents=True)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
report=[]
for name in ('CombatTool_v3','CombatTool_Tuned_v1'):
 path='/Game/Constellation/Review/CombatRecipes/'+name+'/L_Preview'
 file=root/('Content/'+path.removeprefix('/Game/')+'.umap');shutil.copy2(file,folder/(name+'.umap'))
 assert levels.load_level(path)
 rows=[]
 for actor in actors.get_all_level_actors():
  if not isinstance(actor,u.CombatLabCharacter):continue
  fx=actor.get_editor_property('combat_vfx');before=fx.get_editor_property('presentation_enabled')
  fx.set_editor_property('presentation_enabled',True)
  rows.append({'actor':actor.get_name(),'previously_enabled':before})
 assert len(rows)==4 and levels.save_current_level()
 assert levels.load_level(path)
 assert all(a.get_editor_property('combat_vfx').get_editor_property('presentation_enabled') for a in actors.get_all_level_actors() if isinstance(a,u.CombatLabCharacter))
 report.append({'map':path,'actors':rows})
(folder/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
u.log('COMBAT_VFX_ACTIVATION PASS '+str(folder))
