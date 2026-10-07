"""Compile proposed graph repairs on transient duplicates; never save assets."""
import json
from pathlib import Path
import unreal as u

paths = [
    '/Game/Constellation/Gameplay/Interaction/Actors/BP_QuestProgressTrigger',
    '/Game/Constellation/Characters/Enemies/Blueprints/AI/BTT_Attack',
    '/Game/Constellation/Characters/Enemies/Blueprints/AI/BTT_GetNextPatrolPoint',
    '/Game/Constellation/Characters/Enemies/Blueprints/AI/BTS_CheckDistance',
]
results = []
for path in paths:
    bp = u.load_asset(path)
    result = u.ResourceRecoveryLibrary.repair_known_blueprint_logic(bp, False)
    results.append({'path': path, 'result': result})
    u.log('BLUEPRINT_REPAIR ' + path + ' ' + result)
out = Path(u.Paths.project_dir()) / 'Saved/ProjectAudit/20261001/repair-preview.json'
out.write_text(json.dumps(results, indent=2), encoding='utf-8')
assert all('errors=0' in r['result'] and 'warnings=0' in r['result'] for r in results), results
