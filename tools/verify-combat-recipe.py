"""Integration regression: saved recipe assets, rejected inputs, original hashes."""
import copy
import hashlib
import json
import runpy
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
module=runpy.run_path(str(root/"tools/import-combat-recipe.py"))
run=module["run"]
base="/Game/Constellation/Review/CombatRecipes/SlimeScout_v1"
original=json.loads((root/"CombatRecipes/SlimeScout_v1.json").read_text(encoding="utf-8-sig"))
# The standard successful apply report is preserved while rejection cases run.
report_file=root/"Saved/CombatAudit/recipe-result.json"
saved_report=report_file.read_bytes()
checks=[]
try:
    for case in ("MissingSource","WrongSkeleton","ExistingVersion"):
        data=copy.deepcopy(original)
        if case!="ExistingVersion": data["id"]="Reject"+case
        if case=="MissingSource": data["actions"][0]["source"]="/Game/Constellation/Review/DoesNotExist"
        if case=="WrongSkeleton": data["actions"][0]["source"]="/Game/Constellation/Review/CombatCore/DA_PlayerFollowUp03"
        path=root/"Saved/CombatAudit"/(case+".json")
        path.write_text(json.dumps(data),encoding="utf-8")
        expected={"MissingSource":"missing asset","WrongSkeleton":"skeleton","ExistingVersion":"already exists"}[case]
        try:
            run(path,True)
            raise AssertionError(case+" unexpectedly accepted")
        except ValueError as error:
            assert expected in str(error), str(error)
        if case!="ExistingVersion":
            assert not u.EditorAssetLibrary.does_directory_exist(module["BASE"]+"/"+data["id"])
        checks.append(case)
finally:
    report_file.write_bytes(saved_report)
for row in original["actions"]:
    obj=u.load_asset(base+"/DA_"+row["id"])
    assert obj
    for key,value in row["values"].items():
        assert abs(obj.get_editor_property(key)-value)<.0001,(key,value)
    assert not u.CombatLabEditorLibrary.get_combat_asset_error(obj)
profile=u.load_asset(base+"/DA_Patterns")
encounter=u.load_asset(base+"/DA_Encounter")
assert not u.CombatLabEditorLibrary.get_combat_asset_error(profile)
assert not u.CombatLabEditorLibrary.get_combat_asset_error(encounter)
for entry in profile.get_editor_property("patterns"):
    assert entry.get_editor_property("action").get_path_name().startswith(base+"/")
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert levels.load_level(base+"/L_Preview")
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
enemy=next(a for a in actors if isinstance(a,u.CombatLabCharacter) and a.get_editor_property("training_enemy"))
player=next(a for a in actors if isinstance(a,u.CombatLabCharacter) and not a.get_editor_property("training_enemy"))
assert enemy.get_editor_property("pattern_profile")==profile
assert enemy.get_editor_property("encounter_profile")==encounter
assert player.get_editor_property("character_movement").get_editor_property("max_walk_speed")==500
assert player.get_editor_property("arm").get_editor_property("target_arm_length")==450
checks.append("SavedAssetsAndPreviewBindings")
for row in json.loads((root/"Saved/CombatAudit/recipe-original-hashes.json").read_text(encoding="utf-8-sig")):
    assert hashlib.sha256(Path(row["Path"]).read_bytes()).hexdigest().upper()==row["Hash"]
checks.append("OriginalHashesUnchanged")
report={"passed":True,"checks":checks}
(root/"Saved/CombatAudit/recipe-verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
u.log("COMBAT_RECIPE_VERIFIED "+json.dumps(report))
