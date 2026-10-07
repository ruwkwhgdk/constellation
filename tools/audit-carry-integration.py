"""Read current carry integration assets without modifying them (Unreal Python)."""
import hashlib
import json
from pathlib import Path
import unreal as u

root = Path(u.Paths.project_dir()).resolve()
out = root / 'Saved/CarryReview'
out.mkdir(parents=True, exist_ok=True)
paths = [
    '/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine',
    '/Game/Constellation/Characters/Heroine/Blueprints/BP_PlayerCharacter',
    '/Game/Constellation/Characters/Heroine/Blueprints/ABP_Player_Heroine',
    '/Game/Constellation/Gameplay/Interaction/Components/Ac_Interact',
    '/Game/Constellation/Gameplay/Interaction/Components/Ac_Ability',
    '/Game/Constellation/UI/Widgets/WBP_PlayerHUD',
    '/Game/Constellation/Input/IAC_Default',
]
rows = []
for path in paths:
    obj = u.load_asset(path)
    assert obj, path
    source = root / 'Content' / (path.removeprefix('/Game/') + '.uasset')
    row = {'path': path, 'class': obj.get_class().get_name(),
           'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    if isinstance(obj, u.Blueprint):
        text = u.ResourceRecoveryLibrary.export_blueprint_graphs(obj)
        graph_file = out / 'graphs' / (obj.get_name() + '.txt')
        graph_file.parent.mkdir(parents=True, exist_ok=True)
        graph_file.write_text(text, encoding='utf-8')
        row['graph_file'] = str(graph_file.relative_to(out))
        cls = obj.generated_class()
        if cls:
            row['is_character'] = isinstance(u.get_default_object(cls), u.Character)
            cdo = u.get_default_object(cls)
            for name in ('mesh', 'player_state', 'current_state'):
                try:
                    row[name] = str(cdo.get_editor_property(name))
                except Exception:
                    pass
            if isinstance(cdo, u.Character):
                mesh = cdo.get_editor_property('mesh')
                row['skeletal_mesh'] = str(mesh.get_editor_property('skeletal_mesh_asset'))
                row['anim_class'] = str(mesh.get_editor_property('anim_class'))
    else:
        try:
            row['mappings'] = str(obj.get_editor_property('mappings'))
        except Exception:
            pass
    rows.append(row)
(out / 'integration.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf-8')
u.log('CARRY_INTEGRATION_AUDIT_COMPLETE')
