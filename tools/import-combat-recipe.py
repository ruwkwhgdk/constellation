"""Unreal commandlet entry point. Preview by default; creates a new version only."""
import json
import os
import sys
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
sys.path.insert(0,str(ROOT/"tools"))
from combat_recipe import load_recipe, ACTION_RANGES, number

BASE="/Game/Constellation/Review/CombatRecipes"
TEMPLATE="/Game/Constellation/Review/CombatCore/L_CombatEncounter"
assets=u.EditorAssetLibrary

def native_check(obj):
    reason=u.CombatLabEditorLibrary.get_combat_asset_error(obj)
    if reason:
        raise ValueError(obj.get_path_name()+": "+reason)

def loaded(path,kind):
    obj=u.load_asset(path)
    if not isinstance(obj,kind):
        raise ValueError(path+": missing asset or wrong type; expected "+kind.__name__)
    return obj

def preflight(data):
    mesh=loaded(data["mesh"],u.SkeletalMesh)
    sources={}
    for row in data["actions"]:
        obj=loaded(row["source"],u.CombatActionDefinition)
        native_check(obj)
        if obj.get_editor_property("next_action"):
            raise ValueError(row["id"]+": monster recipe sources must not contain a player follow-up chain")
        montage=obj.get_editor_property("montage")
        if montage.get_editor_property("skeleton")!=mesh.get_editor_property("skeleton"):
            raise ValueError(row["id"]+": montage skeleton does not match recipe mesh")
        for key,bounds in ACTION_RANGES.items():
            number(row["values"].get(key,obj.get_editor_property(key)),*bounds,row["id"]+"."+key)
        sources[row["id"]]=obj
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if not levels.load_level(TEMPLATE):
        raise ValueError("Missing encounter template; run setup-combat-encounter.py first")
    enemies=[a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
             if isinstance(a,u.CombatLabCharacter) and a.get_editor_property("training_enemy")]
    if len(enemies)!=1:
        raise ValueError("Encounter template must contain exactly one enemy")
    if enemies[0].get_editor_property("mesh").get_editor_property("skeletal_mesh_asset")!=mesh:
        raise ValueError("Recipe mesh must match the current encounter template (slime only in version 1)")
    for key in ("idle_animation","move_animation"):
        animation=enemies[0].get_editor_property(key)
        if not animation or animation.get_editor_property("skeleton")!=mesh.get_editor_property("skeleton"):
            raise ValueError("Template "+key+" is missing or incompatible")
    return sources

def run(path,apply=False):
    report={"passed":False,"mode":"apply" if apply else "preview","recipe":str(path),"created":[]}
    report_path=Path(os.environ.get("COMBAT_RECIPE_RESULT",str(ROOT/"Saved/CombatAudit/recipe-result.json")))
    report_path.parent.mkdir(parents=True,exist_ok=True)
    try:
        data=load_recipe(path)
        if data["schema_version"]==2:
            from combat_recipe_unreal import create
            report.update(id=data["id"],normalized=data,warnings=data["warnings"])
            create(data,report,apply)
            report["passed"]=True
            return report
        folder=BASE+"/"+data["id"]
        planned=[folder+"/DA_"+a["id"] for a in data["actions"]]+[folder+"/DA_Patterns",folder+"/DA_Encounter",folder+"/L_Preview"]
        report.update({"id":data["id"],"planned":planned,"warnings":data["warnings"],"normalized":data})
        if assets.does_directory_exist(folder) or any(assets.does_asset_exist(p) for p in planned):
            raise ValueError(folder+": version already exists; choose a new recipe id (no overwrite)")
        sources=preflight(data)
        if apply:
            def remember(obj):
                if not obj: raise RuntimeError("Asset creation failed")
                report["created"].append(obj.get_path_name())
                assets.set_metadata_tag(obj,"CombatRecipeId",data["id"])
                return obj
            def create(name,kind):
                factory=u.DataAssetFactory()
                factory.set_editor_property("data_asset_class",kind)
                return remember(u.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,kind,factory))
            generated={}
            for row in data["actions"]:
                obj=remember(assets.duplicate_asset(row["source"],folder+"/DA_"+row["id"]))
                for key,value in row["values"].items():
                    obj.set_editor_property(key,value)
                obj.set_editor_property("display_name",data["id"]+" / "+row["id"])
                native_check(obj)
                generated[row["id"]]=obj
            profile=create("DA_Patterns",u.CombatPatternProfile)
            entries=[]
            for row in data["patterns"]:
                entry=u.CombatPatternEntry()
                for key,value in row.items():
                    entry.set_editor_property(key,generated[value] if key=="action" else value)
                entries.append(entry)
            profile.set_editor_property("patterns",entries)
            encounter=create("DA_Encounter",u.CombatEncounterProfile)
            for key,value in data["encounter"].items():
                encounter.set_editor_property(key,value)
            native_check(profile); native_check(encounter)
            for obj in [*generated.values(),profile,encounter]:
                if not assets.save_loaded_asset(obj):
                    raise RuntimeError("Save failed: "+obj.get_path_name())
            preview=remember(assets.duplicate_asset(TEMPLATE,folder+"/L_Preview"))
            levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
            if not levels.load_level(folder+"/L_Preview"):
                raise RuntimeError("Could not load generated preview map")
            enemies=[a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
                     if isinstance(a,u.CombatLabCharacter) and a.get_editor_property("training_enemy")]
            if len(enemies)!=1: raise RuntimeError("Generated preview enemy missing")
            enemy=enemies[0]
            enemy.set_editor_property("action",next(iter(generated.values())))
            enemy.set_editor_property("pattern_profile",profile)
            enemy.set_editor_property("encounter_profile",encounter)
            enemy.set_actor_label(data["id"]+" recipe enemy")
            if not levels.save_current_level(): raise RuntimeError("Preview map save failed")
            report["preview_map"]=folder+"/L_Preview"
        report["passed"]=True
        return report
    except Exception as error:
        report["error"]=str(error)
        raise
    finally:
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        u.log("COMBAT_RECIPE_RESULT "+json.dumps({k:v for k,v in report.items() if k!="normalized"},ensure_ascii=False))

if __name__=="__main__":
    run(os.environ.get("COMBAT_RECIPE_INPUT",str(ROOT/"CombatRecipes/SlimeScout_v1.json")),
        os.environ.get("COMBAT_RECIPE_APPLY")=="1")
