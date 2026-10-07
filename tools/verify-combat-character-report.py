"""Generate and verify an AI handoff report from the maintained recipe preview."""
import json
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert levels.load_level("/Game/Constellation/Review/CombatRecipes/SlimeScout_v2/L_Preview")
enemy=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
           if isinstance(a,u.CombatLabCharacter) and a.get_editor_property("training_enemy"))
result=u.CombatLabEditorLibrary.save_combat_character_report(enemy)
assert result is not None, "Native report save failed"
path,error=result
assert path and not error,error
report=json.loads(Path(path).read_text(encoding="utf-8-sig"))
assert report["valid"] is True,report["errors"]
assert report["encounter"]["move_speed"]==220
assert len(report["patterns"])==2
assert all(row["action"]["path"].startswith("/Game/Constellation/Review/CombatRecipes/SlimeScout_v2/") for row in report["patterns"])
summary={"passed":True,"report":path,"valid":report["valid"],"patterns":len(report["patterns"])}
(root/"Saved/CombatAudit/character-report-verification.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
u.log("COMBAT_CHARACTER_REPORT_VERIFIED "+json.dumps(summary))
