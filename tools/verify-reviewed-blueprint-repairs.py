"""Fresh-process verification and graph evidence for the saved audit repairs."""
import json
from pathlib import Path
import unreal as u

root = Path(u.Paths.project_dir()).resolve()
out = root / 'Saved/ProjectAudit/20261001'
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
    assert result == 'PREVIEW changes=0 errors=0 warnings=0', (path, result)
    graph = u.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
    target = out / 'after' / (path.removeprefix('/Game/') + '.txt')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(graph, encoding='utf-8')
    results.append({'path': path, 'result': result})
path = '/Game/LuosCaves/Maps/LCaves_Will_Chambers_Contribution_Showcase'
world = u.load_asset(path)
graph = u.ResourceRecoveryLibrary.export_level_blueprint_graphs(world)
assert graph.startswith('COMPILE errors=0 warnings=0'), graph[:100]
target = out / 'after' / 'showcase-level.txt'
target.write_text(graph, encoding='utf-8')
results.append({'path': path, 'result': graph.splitlines()[0]})
(out / 'saved-verification.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
u.log('SAVED_REPAIRS_VERIFIED ' + str(len(results)))
