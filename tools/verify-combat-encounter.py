"""Read saved encounter assets and the unchanged player-control baseline."""
import json
import runpy
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir())
runpy.run_path(str(root/"tools/verify-combat-lab.py"))
base="/Game/Constellation/Review/CombatCore"
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert levels.load_level(base+"/L_CombatEncounter")
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
fighters=[a for a in actors if isinstance(a,u.CombatLabCharacter)]
assert len(fighters)==2
enemy=next(a for a in fighters if a.get_editor_property("training_enemy"))
player=next(a for a in fighters if not a.get_editor_property("training_enemy"))
profile=enemy.get_editor_property("encounter_profile")
assert profile and enemy.get_editor_property("pattern_profile")
assert any(isinstance(a,u.NavMeshBoundsVolume) for a in actors)
assert any(a.get_actor_label()=="Navigation detour obstacle" for a in actors)
assert player.get_editor_property("character_movement").get_editor_property("max_walk_speed")==500
assert player.get_editor_property("arm").get_editor_property("target_arm_length")==450
assert not player.get_editor_property("encounter_profile")
report={"passed":True,"map":base+"/L_CombatEncounter","profile":profile.get_path_name(),
        "player_start":str(player.get_actor_location()),"enemy_start":str(enemy.get_actor_location()),
        "enemy_speed":profile.get_editor_property("move_speed"),"player_speed":500}
(root/"Saved/CombatAudit/20261004/encounter-verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
u.log("COMBAT_ENCOUNTER_VERIFY "+json.dumps(report))
