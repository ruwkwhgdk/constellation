"""Read-only interaction inventory, including inherited interfaces and graph evidence."""
import json
from pathlib import Path
import unreal as u
root = Path(u.Paths.project_dir()).resolve()
out = root / 'Saved/InteractionPromptReview'
(out / 'graphs').mkdir(parents=True, exist_ok=True)
registry = u.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(True)
interface = u.load_class(None, '/Game/Constellation/Gameplay/Interaction/Interfaces/BPI_Interact.BPI_Interact_C')
rows = []
for asset in registry.get_assets_by_path('/Game/Constellation', recursive=True):
    if str(asset.asset_class_path.asset_name) != 'Blueprint':
        continue
    bp = asset.get_asset()
    cls = bp.generated_class() if bp else None
    if not cls:
        continue
    cdo = u.get_default_object(cls)
    if not u.SystemLibrary.does_implement_interface(cdo, interface):
        continue
    text = u.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
    (out / 'graphs' / (bp.get_name() + '.txt')).write_text(text, encoding='utf-8')
    rows.append({'path': str(asset.package_name), 'class': cls.get_path_name()})
for path in ('/Game/Constellation/Gameplay/Interaction/Components/Ac_Interact', '/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine'):
    bp = u.load_asset(path)
    (out / 'graphs' / (bp.get_name() + '.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(bp), encoding='utf-8')
(out / 'inventory.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
u.log('INTERACTION_INVENTORY_COMPLETE ' + str(len(rows)))
