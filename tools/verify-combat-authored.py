import unreal as u
import json
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve()
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
results={}
for name,expected_hp,expected_heavy in (("CombatTool_v3",100,28),("CombatTool_Tuned_v1",117,31)):
    assert levels.load_level("/Game/Constellation/Review/CombatRecipes/"+name+"/L_Preview")
    actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    player=next(a for a in actors if isinstance(a,u.CombatLabCharacter) and not a.get_editor_property("training_enemy"))
    enemies=[a for a in actors if isinstance(a,u.CombatLabCharacter) and a.get_editor_property("training_enemy")]
    assert len(enemies)==3
    assert player.get_editor_property("combat").get_editor_property("max_health")==expected_hp
    guard=next(a for a in enemies if "Guard" in a.get_actor_label())
    scout=next(a for a in enemies if "Scout" in a.get_actor_label())
    def heavy(a):
        rows=a.get_editor_property("pattern_profile").get_editor_property("patterns")
        return next(x.get_editor_property("action").get_editor_property("damage") for x in rows if "Heavy" in str(x.get_editor_property("action").get_name()))
    assert heavy(guard)==expected_heavy
    assert heavy(scout)==22
    assert guard.get_editor_property("combat").get_editor_property("max_health")==220
    assert scout.get_editor_property("combat").get_editor_property("max_health")==150
    director=player.get_editor_property("encounter_director")
    assert director and director.get_editor_property("max_attackers")==1
    assert len(director.get_editor_property("enemies"))==3
    for a in enemies:
        errors,warnings=u.CombatLabEditorLibrary.validate_combat_character(a)
        assert not errors,str(errors)
    results[name]={"player_hp":expected_hp,"guard_heavy":expected_heavy,"scout_heavy":22,"enemies":3}
(root/"Saved/CombatAudit/authored-reload.json").write_text(json.dumps(results,indent=2))
u.log("COMBAT_AUTHORED_RELOAD PASS")
