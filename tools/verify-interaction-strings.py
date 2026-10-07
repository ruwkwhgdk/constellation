"""Read saved String Table through the saved player's component."""
import csv,json,re
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
table=u.load_asset('/Game/Constellation/Gameplay/Interaction/Data/ST_InteractionActions')
hero=u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine')
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem); fn=u.SubobjectDataBlueprintFunctionLibrary
components=[fn.get_object_for_blueprint(fn.get_data(h),hero) for h in sub.k2_gather_subobject_data_for_blueprint(hero)]
prompt=next(c for c in components if isinstance(c,u.InteractionPromptComponent))
assert prompt.action_strings==table
checks=[]
with (root/'ArtSource/Gameplay/Interaction/initial-action-strings.csv').open(encoding='utf-8-sig') as f:
 for row in csv.DictReader(f):
  action=getattr(u.InteractionAction,re.sub(r'(?<!^)(?=[A-Z])','_',row['Key']).upper())
  actual=str(prompt.get_action_text(action))
  assert actual==row['SourceString'],(row,actual)
  checks.append({'key':row['Key'],'text':actual})
assert len(checks)==16
assert prompt.background_texture and prompt.key_background_texture and len(prompt.rules)==15
out=root/'Saved/InteractionPromptReview/strings-reload.json'
out.write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
u.log('INTERACTION_STRINGS_RELOAD_VERIFIED count=16')
