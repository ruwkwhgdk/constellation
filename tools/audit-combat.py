"""Read-only combat snapshot. Does not compile, mutate, or save game assets."""
import hashlib
import json
from pathlib import Path
import unreal as u

root = Path(u.Paths.project_dir()).resolve()
out = root / "Saved/CombatAudit/20261004"
out.mkdir(parents=True, exist_ok=True)
registry = u.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(True)
prefixes = (
    "/Game/Constellation/Gameplay/Combat",
    "/Game/Constellation/Characters/Enemies/Blueprints",
    "/Game/Constellation/Characters/Heroine/Blueprints",
)
extra = ("BP_BattleZone", "BP_BattleGate", "BP_MonsterTriggerArea")
rows = []
for a in registry.get_assets_by_path("/Game/Constellation", recursive=True):
    path = str(a.package_name)
    if not path.startswith(prefixes) and not any(x in path for x in extra):
        continue
    cls = str(a.asset_class_path.asset_name)
    file = root / ("Content/" + path.removeprefix("/Game/") + ".uasset")
    row = {"path": path, "class": cls}
    if file.exists():
        row["sha256"] = hashlib.sha256(file.read_bytes()).hexdigest()
    obj = a.get_asset()
    row["loaded"] = obj is not None
    if obj and "Blueprint" in cls:
        graph = u.ResourceRecoveryLibrary.export_blueprint_graphs(obj)
        relative = Path("graphs") / (path.removeprefix("/Game/") + ".txt")
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(graph, encoding="utf-8")
        row["graph_file"] = str(relative)
        row["nodes"] = graph.count("Begin Object Class=")
        if hasattr(obj, "generated_class") and obj.generated_class():
            cdo = u.get_default_object(obj.generated_class())
            row["defaults"] = {}
            for key in ("attack_delay", "attack_distance", "cooldown", "max_hp", "current_hp",
                        "attack_point", "max_stamina", "current_stamina", "is_attacking",
                        "is_invincible", "dodge_power"):
                try:
                    row["defaults"][key] = str(cdo.get_editor_property(key))
                except Exception:
                    pass
    rows.append(row)
(out / "inventory.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
u.log("COMBAT_AUDIT_COMPLETE assets=" + str(len(rows)))
