"""Read-only verification of saved heroine defaults in a fresh Unreal process."""
import unreal as u,json
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'Saved/FallSystem'
bp=u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine')
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
a=actors.spawn_actor_from_class(bp.generated_class(),u.Vector(0,0,2000))
fall=a.get_component_by_class(u.PlayerFallComponent);assert fall
assert isinstance(a.get_editor_property('character_movement'),u.SteepSlopeMovementComponent)
assert fall.get_editor_property('reference_height')==160
assert fall.get_editor_property('maximum_damage_height_multiplier')==24
for height,tier,ratio in [(319,0,0),(320,1,0),(959,1,0),(960,2,.05),(1440,2,.075),(1920,3,.1),(2880,3,.55),(3840,3,1)]:
    r=fall.evaluate_landing(height)
    assert r.tier==[u.PlayerLandingTier.NONE,u.PlayerLandingTier.NORMAL,u.PlayerLandingTier.WEAK,u.PlayerLandingTier.STRONG][tier] and abs(r.damage_ratio-ratio)<1e-6,(height,r)
report={'passed':True,'actor':a.get_class().get_path_name(),'component':fall.get_path_name(),'reference_height':160,'maximum_multiplier':24}
actors.destroy_actor(a)
(out/'asset-verified.json').write_text(json.dumps(report,indent=2),encoding='utf8')
u.log('FALL_ASSET_VERIFIED')
