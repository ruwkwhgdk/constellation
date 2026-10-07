"""Read saved generated assets, export a reimportable recipe and compare tuning."""
import copy
import json
import os
import runpy
import sys
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.project_dir()).resolve()
sys.path.insert(0,str(ROOT/"tools"))
from combat_recipe import ACTION_RANGES,PATTERN_DEFAULTS,ENCOUNTER_DEFAULTS,identifier,validate_recipe,load_recipe
from combat_recipe_compare import compare_recipes
BASE="/Game/Constellation/Review/CombatRecipes"

def package(obj):
    return obj.get_path_name().split(".")[0]

def read_asset(path,kind):
    obj=u.load_asset(path)
    if not isinstance(obj,kind): raise ValueError(path+": missing or wrong asset type")
    if kind in (u.CombatActionDefinition,u.CombatPatternProfile,u.CombatEncounterProfile):
        reason=u.CombatLabEditorLibrary.get_combat_asset_error(obj)
        if reason: raise ValueError(path+": "+reason)
    return obj

def snapshot(bundle_id,new_id):
    identifier(bundle_id,"bundle_id"); identifier(new_id,"new_id")
    if bundle_id.lower()==new_id.lower(): raise ValueError("Use a new id for reimport")
    folder=BASE+"/"+bundle_id
    if u.EditorAssetLibrary.does_directory_exist(BASE+"/"+new_id):
        raise ValueError("New version already exists: "+new_id)
    profile=read_asset(folder+"/DA_Patterns",u.CombatPatternProfile)
    encounter=read_asset(folder+"/DA_Encounter",u.CombatEncounterProfile)
    actions=[]; ids={}; montages={}
    for path in sorted(u.EditorAssetLibrary.list_assets(folder,recursive=False,include_folder=False)):
        obj=u.load_asset(path)
        if not isinstance(obj,u.CombatActionDefinition): continue
        native=u.CombatLabEditorLibrary.get_combat_asset_error(obj)
        if native: raise ValueError(path+": "+native)
        name=obj.get_name()
        if not name.startswith("DA_"): raise ValueError("Unsupported action asset name: "+name)
        key=name[3:]
        if obj.get_editor_property("next_action"): raise ValueError(key+": follow-up chains cannot be exported")
        actions.append({"id":key,"source":package(obj),"values":{k:obj.get_editor_property(k) for k in ACTION_RANGES}})
        ids[package(obj)]=key
        montages[key]=package(obj.get_editor_property("montage"))
    patterns=[]
    for entry in profile.get_editor_property("patterns"):
        source=package(entry.get_editor_property("action"))
        if source not in ids: raise ValueError("Pattern references an action outside the bundle: "+source)
        row={k:entry.get_editor_property(k) for k in PATTERN_DEFAULTS}
        row.update(id=str(entry.get_editor_property("id")),action=ids[source])
        patterns.append(row)
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if not levels.load_level(folder+"/L_Preview"): raise ValueError("Missing preview map")
    enemies=[a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
             if isinstance(a,u.CombatLabCharacter) and a.get_editor_property("training_enemy")]
    if len(enemies)!=1: raise ValueError("Expected one preview enemy")
    enemy=enemies[0]
    if enemy.get_editor_property("pattern_profile")!=profile or enemy.get_editor_property("encounter_profile")!=encounter:
        raise ValueError("Preview enemy is bound to different profiles")
    mesh=enemy.get_editor_property("mesh").get_editor_property("skeletal_mesh_asset")
    if not mesh: raise ValueError("Preview enemy has no mesh")
    for row in actions:
        montage=u.load_asset(row["source"]).get_editor_property("montage")
        if montage.get_editor_property("skeleton")!=mesh.get_editor_property("skeleton"):
            raise ValueError(row["id"]+": incompatible skeleton")
    data={"schema_version":1,"id":new_id,"mesh":package(mesh),"actions":actions,"patterns":patterns,
          "encounter":{k:encounter.get_editor_property(k) for k in ENCOUNTER_DEFAULTS}}
    checked=validate_recipe(data)
    warnings=checked.pop("warnings")
    return checked,warnings,montages

def run(bundle_id,new_id,baseline_path=None):
    report={"passed":False,"bundle":bundle_id,"new_id":new_id}
    audit=ROOT/"Saved/CombatAudit"
    audit.mkdir(parents=True,exist_ok=True)
    try:
        data,warnings,montages=snapshot(bundle_id,new_id)
        # Reuse the exact import contract, including template mesh/locomotion checks.
        runpy.run_path(str(ROOT/"tools/import-combat-recipe.py"))["preflight"](data)
        report.update(warnings=warnings,changes=[],animation_reference_changes=[])
        if baseline_path:
            baseline=load_recipe(baseline_path)
            if baseline["id"].lower()!=bundle_id.lower():
                raise ValueError("Baseline id must match exported bundle")
            baseline=copy.deepcopy(baseline)
            for row in baseline["actions"]:
                source=read_asset(row["source"],u.CombatActionDefinition)
                row["values"]={k:row["values"].get(k,source.get_editor_property(k)) for k in ACTION_RANGES}
                previous=package(source.get_editor_property("montage"))
                if row["id"] in montages and previous!=montages[row["id"]]:
                    report["animation_reference_changes"].append({"id":row["id"],"before":previous,"after":montages[row["id"]]})
            report["changes"]=compare_recipes(baseline,data)
            report["baseline"]=str(baseline_path)
            report["comparison_basis"]="Explicit JSON values; omitted action values resolve from source assets saved now, not historical defaults."
        destination=ROOT/"CombatRecipes"/(new_id+".json")
        destination.parent.mkdir(parents=True,exist_ok=True)
        # Exclusive create prevents overwriting an existing designer input.
        with destination.open("x",encoding="utf-8") as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2)
        report.update(passed=True,export=str(destination))
        return report
    except Exception as error:
        report["error"]=str(error)
        raise
    finally:
        (audit/"recipe-export-result.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        u.log("COMBAT_RECIPE_EXPORT "+json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    run(os.environ.get("COMBAT_EXPORT_ID","SlimeScout_v1"),os.environ.get("COMBAT_EXPORT_NEW_ID","SlimeScout_v2"),
        os.environ.get("COMBAT_EXPORT_BASELINE") or None)
