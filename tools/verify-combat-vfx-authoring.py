import unreal as u
import json,sys
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve();sys.path.insert(0,str(root/'tools'))
from combat_recipe import load_recipe
from combat_recipe_unreal import prepare
levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
report={}
for name in ('CombatTool_v3','CombatTool_Tuned_v1','CombatTool_VFX_v1'):
 assert levels.load_level('/Game/Constellation/Review/CombatRecipes/'+name+'/L_Preview')
 chars=[a for a in actors.get_all_level_actors() if isinstance(a,u.CombatLabCharacter)]
 assert len(chars)==4 and all(a.get_editor_property('combat_vfx').get_editor_property('presentation_enabled') for a in chars)
 guard=next(a for a in chars if 'Guard' in a.get_actor_label());player=next(a for a in chars if not a.get_editor_property('training_enemy'))
 assert guard.get_editor_property('combat').get_editor_property('max_health')==220
 assert player.get_editor_property('combat').get_editor_property('max_health')==(117 if name=='CombatTool_Tuned_v1' else 100)
 if name=='CombatTool_VFX_v1':
  cue=guard.get_editor_property('combat_vfx').get_editor_property('hit_cue')
  assert cue.get_editor_property('mode')==u.CombatVFXCueMode.BUILTIN
  assert cue.get_editor_property('kind')==u.ConstellationFXKind.SLIME_HIT
  assert abs(cue.get_editor_property('scale')-1.3)<.001
  for a in chars:
   if a!=guard:assert a.get_editor_property('combat_vfx').get_editor_property('hit_cue').get_editor_property('mode')==u.CombatVFXCueMode.DEFAULT
 report[name]={'enabled':len(chars),'hp_preserved':True,'individual_override':name=='CombatTool_VFX_v1'}
d=load_recipe(root/'CombatRecipes/CombatTool_VFX_v1.json');d.pop('warnings',None)
d['player']['vfx']={'attack':{'mode':'Niagara','system':'/Game/Constellation/VFX/NS_SwordTrail'}}
prepare(d)
d['player']['vfx']['attack']['system']=d['actions'][0]['source']
try:prepare(d)
except ValueError as e:assert 'NiagaraSystem' in str(e)
else:raise AssertionError('Non-Niagara asset accepted')
(root/'Saved/CombatAudit/vfx-authored-reload.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
u.log('COMBAT_VFX_AUTHORED_RELOAD PASS')
