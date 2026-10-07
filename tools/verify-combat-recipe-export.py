"""Read-only roundtrip and in-memory edit detection regression."""
import hashlib
import json
import runpy
import sys
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
sys.path.insert(0,str(root/"tools"))
from combat_recipe_compare import compare_recipes
module=runpy.run_path(str(root/"tools/export-combat-recipe.py"))
snapshot=module["snapshot"]
first,_,_=snapshot("SlimeScout_v1","SlimeExportProbe")
second,_,_=snapshot("SlimeScout_v2","SlimeExportProbe")
assert compare_recipes(first,second)==[], "Reimport changed tuning"
source=u.load_asset("/Game/Constellation/Review/CombatRecipes/SlimeScout_v1/DA_Light")
previous=source.get_editor_property("damage")
try:
    source.set_editor_property("damage",previous+3)
    changed,_,_=snapshot("SlimeScout_v1","SlimeExportProbe")
    differences=compare_recipes(first,changed)
    assert differences==[{"path":"actions.Light.values.damage","before":previous,"after":previous+3}],differences
finally:
    source.set_editor_property("damage",previous)
# Existing output input is protected even when a generated version is absent.
input_path=root/"CombatRecipes/SlimeScout_v2.json"
before=hashlib.sha256(input_path.read_bytes()).hexdigest()
try:
    module["run"]("SlimeScout_v1","SlimeScout_v2")
    raise AssertionError("Existing version accepted")
except ValueError as error:
    assert "already exists" in str(error),str(error)
assert hashlib.sha256(input_path.read_bytes()).hexdigest()==before
# A snapshot must also satisfy the importer's template compatibility checks.
probe=root/"CombatRecipes/ExportRejectedProbe.json"
assert not probe.exists()
globals_=module["run"].__globals__
real_snapshot=globals_["snapshot"]
bad=dict(first)
bad["id"]="ExportRejectedProbe"
bad["mesh"]="/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview"
globals_["snapshot"]=lambda *args: (bad,[],{})
try:
    try:
        module["run"]("SlimeScout_v1","ExportRejectedProbe")
        raise AssertionError("Exporter skipped importer compatibility checks")
    except ValueError as error:
        assert "skeleton" in str(error) or "template" in str(error),str(error)
    assert not probe.exists()
finally:
    globals_["snapshot"]=real_snapshot
    if probe.exists(): probe.unlink()  # only this newly created test file
report={"import_preflight_enforced":True,"passed":True,"roundtrip_equal":True,"edited_damage_detected":True,"existing_version_preserved":True}
(root/"Saved/CombatAudit/recipe-export-verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
u.log("COMBAT_EXPORT_VERIFIED "+json.dumps(report))
