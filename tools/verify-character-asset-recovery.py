"""Read-only load verification of recovered GamePilot packages, in a fresh commandlet."""
import json
from pathlib import Path
import unreal as u

root = Path(u.Paths.project_dir())
out = root / 'Saved/CharacterAssetRecovery/20261012'
manifest = json.loads((out / 'recovery.json').read_text(encoding='utf8'))
assets = {}
for item in manifest['assets']:
    path = '/Game/' + item['asset'].removesuffix('.uasset')
    asset = u.load_asset(path)
    assert asset is not None, path
    assets[asset.get_name()] = asset
mesh = assets['SK_Heroine_GamePilot']
skeleton = assets['SKEL_player_heroine_new_RebuildReview']
assert mesh.skeleton == skeleton
physics = mesh.get_editor_property('physics_asset')
assert all(slot.material_interface is not None for slot in mesh.materials)
animations = {}
for name in ('GP_Climbing_Ladder', 'GP_Climbing_To_Top'):
    animation = assets[name]
    assert animation.get_editor_property('skeleton') == skeleton
    duration = animation.get_editor_property('sequence_length')
    assert duration > 0
    animations[name] = duration
abp = u.load_asset('/Game/Constellation/Characters/Heroine/GamePilot/AnimationBlueprint/GP_ABP_Player_Heroine')
assert abp is not None
assert abp.get_editor_property('target_skeleton') == skeleton
result = dict(loaded_assets=list(assets), skeleton=skeleton.get_path_name(),
              physics_asset=physics.get_path_name() if physics else None,
              material_slots=len(mesh.materials),
              morphs=[m.get_name() for m in mesh.get_editor_property('morph_targets')],
              animation_durations=animations, animation_blueprint_skeleton_matches=True)
(out / 'verified.json').write_text(json.dumps(result, indent=2), encoding='utf8')
u.log('CHARACTER_RECOVERY_VERIFIED')
