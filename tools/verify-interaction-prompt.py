"""Reload saved prompt component and verify coverage plus the hard texture dependency."""
import json
from pathlib import Path
import unreal as u
out=Path(u.Paths.project_dir()).resolve()/'Saved/InteractionPromptReview'
path='/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine'
bp=u.load_asset(path)
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn=u.SubobjectDataBlueprintFunctionLibrary
prompts=[fn.get_object_for_blueprint(fn.get_data(h),bp) for h in sub.k2_gather_subobject_data_for_blueprint(bp)]
prompts=[p for p in prompts if isinstance(p,u.InteractionPromptComponent)]
assert len(prompts)==1,len(prompts)
p=prompts[0]
texture=u.load_asset('/Game/Constellation/UI/Art/T_InteractionPrompt_Background')
assert p.background_texture==texture
assert len(p.rules)==15
options=u.AssetRegistryDependencyOptions(include_soft_package_references=False,include_hard_package_references=True)
deps=u.AssetRegistryHelpers.get_asset_registry().get_dependencies(path,options)
assert '/Game/Constellation/UI/Art/T_InteractionPrompt_Background' in [str(d) for d in deps],str(deps)
covered=[]
for row in json.loads((out/'inventory.json').read_text(encoding='utf-8')):
    cls=u.EditorAssetLibrary.load_blueprint_class(row['path'])
    cdo=u.get_default_object(cls)
    assert any(u.MathLibrary.class_is_child_of(cls,r.actor_class) for r in p.rules),row['path']
    covered.append(row['path'])
(out/'reload.json').write_text(json.dumps({'one_component':True,'hard_texture_dependency':True,'covered_interactable_blueprints':covered,'rule_count':len(p.rules)},indent=2),encoding='utf-8')
u.log('INTERACTION_PROMPT_RELOAD_VERIFIED')
