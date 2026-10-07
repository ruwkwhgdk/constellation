"""Unreal-side authoring for version 2 recipes. Never edits source packages."""
import copy
import json
from pathlib import Path
import unreal as u
from combat_recipe import V2_ACTION_RANGES, ACTION_BOOLEANS, STAT_RANGES, effective_enemy, resolved_vfx, validate_vfx

BASE="/Game/Constellation/Review/CombatRecipes"
TEMPLATE="/Game/Constellation/Review/CombatCore/L_CombatEncounter"
assets=u.EditorAssetLibrary

def package(obj):
    return obj.get_path_name().split(".")[0]

def loaded(path,kind):
    obj=u.load_asset(path)
    if not isinstance(obj,kind):raise ValueError(path+": missing "+kind.__name__)
    return obj

def native(obj):
    reason=u.CombatLabEditorLibrary.get_combat_asset_error(obj)
    if reason:raise ValueError(obj.get_name()+": "+reason)

def resolved(rows,mesh):
    result={}
    for row in rows:
        source=loaded(row["source"],u.CombatActionDefinition)
        montage=loaded(row["montage"],u.AnimMontage) if "montage" in row else source.get_editor_property("montage")
        if not montage or montage.get_editor_property("skeleton")!=mesh.get_editor_property("skeleton"):
            raise ValueError(row["id"]+": incompatible montage skeleton")
        # Transient copies let native validation check fully resolved values without changing source assets.
        obj=u.new_object(u.CombatActionDefinition)
        for key in (*V2_ACTION_RANGES,*ACTION_BOOLEANS):
            obj.set_editor_property(key,row["values"].get(key,source.get_editor_property(key)))
        obj.set_editor_property("montage",montage)
        obj.set_editor_property("next_action",None)
        if "hit_windows" in row:
            length=montage.get_play_length()
            for w in row["hit_windows"]:
                if w["end"]>length:raise ValueError(row["id"]+": hit window exceeds montage duration")
            windows=row["hit_windows"]
            preview=u.CombatLabEditorLibrary.preview_authored_hit_windows(montage,
                [w["id"] for w in windows],[w["start"] for w in windows],[w["end"] for w in windows])
            if not preview:raise ValueError(row["id"]+": invalid authored hit windows")
            obj.set_editor_property("montage",preview)
        result[row["id"]]=obj
    for row in rows:
        obj=result[row["id"]]
        obj.set_editor_property("next_action",result.get(row.get("next_action")))
        native(obj)
    return result

def vfx_settings(actor,settings,apply=False):
    settings=resolved_vfx(settings)
    validate_vfx(settings,"resolved.vfx")
    for slot in ("attack","hit"):
        row=settings[slot]
        system=loaded(row["system"],u.NiagaraSystem) if row.get("system") else None
        if apply:
            cue=u.CombatVFXCue()
            cue.set_editor_property("mode",getattr(u.CombatVFXCueMode,row["mode"].upper()))
            # Unreal's Python enum spelling separates PascalCase words.
            import re
            enum_name=re.sub(r"(?<!^)(?=[A-Z])","_",row["kind"]).upper()
            cue.set_editor_property("kind",getattr(u.ConstellationFXKind,enum_name))
            cue.set_editor_property("system",system);cue.set_editor_property("color",u.LinearColor(*row["color"]))
            cue.set_editor_property("scale",row["scale"]);cue.set_editor_property("duration",row["duration"])
            actor.get_editor_property("combat_vfx").set_editor_property(slot+"_cue",cue)
    if apply:actor.get_editor_property("combat_vfx").set_editor_property("presentation_enabled",settings["enabled"])

def prepare(data):
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if not levels.load_level(TEMPLATE):raise ValueError("Missing encounter template")
    actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    enemies=[a for a in actors if isinstance(a,u.CombatLabCharacter) and a.get_editor_property("training_enemy")]
    players=[a for a in actors if isinstance(a,u.CombatLabCharacter) and not a.get_editor_property("training_enemy")]
    if len(enemies)!=1 or len(players)!=1:raise ValueError("Template requires one player and one monster")
    enemy,player=enemies[0],players[0]
    mesh=loaded(data["mesh"],u.SkeletalMesh)
    if enemy.get_editor_property("mesh").get_editor_property("skeletal_mesh_asset")!=mesh:
        raise ValueError("Current template supports slime mesh; another skeleton needs a matching locomotion template")
    vfx_settings(player,data.get("player",{}).get("vfx",{}))
    for row in data["enemies"]:vfx_settings(enemy,resolved_vfx(data.get("monster_vfx"),row.get("vfx")))
    groups={"enemy":resolved(data["actions"],mesh)}
    if "player" in data:
        groups["player"]=resolved(data["player"]["actions"],player.get_editor_property("mesh").get_editor_property("skeletal_mesh_asset"))
    for actor,stats,actions in ((enemy,data["monster_stats"],groups["enemy"]),
          (player,data.get("player",{}).get("stats",{}),groups.get("player",{}))):
        combat=actor.get_editor_property("combat")
        values={key:stats.get(key,combat.get_editor_property(key)) for key in STAT_RANGES}
        if values["dodge_distance"]<=0 or values["dodge_invulnerable_end"]>values["dodge_duration"] or values["dodge_invulnerable_start"]>=values["dodge_invulnerable_end"]:
            raise ValueError("Resolved dodge interval invalid")
        for action in actions.values():
            if action.get_editor_property("stamina_cost")>values["max_stamina"]:raise ValueError("Action SP cost exceeds configured maximum")
    for row in data["enemies"]:
        if any(k in row for k in ("stats","action_values","pattern_values","encounter_values")):
            effective=effective_enemy(data,row)
            actions=resolved(effective["actions"],mesh)
            combat=enemy.get_editor_property("combat")
            stats={key:effective["monster_stats"].get(key,combat.get_editor_property(key)) for key in STAT_RANGES}
            if stats["dodge_distance"]<=0 or stats["dodge_invulnerable_end"]>stats["dodge_duration"] or stats["dodge_invulnerable_start"]>=stats["dodge_invulnerable_end"]:
                raise ValueError("enemies."+row["id"]+": resolved dodge interval/distance invalid")
            maximum=stats["max_stamina"]
            if any(a.get_editor_property("stamina_cost")>maximum for a in actions.values()):
                raise ValueError(row["id"]+": action SP cost exceeds maximum")
            groups["enemy/"+row["id"]]=actions
    return groups

def create(data,report,apply):
    folder=BASE+"/"+data["id"]
    if assets.does_directory_exist(folder):raise ValueError("Version already exists; choose a new id: "+data["id"])
    recipe_dir=Path(u.Paths.project_dir()).resolve()/"CombatRecipes"
    if any((recipe_dir/(data["id"]+suffix)).exists() for suffix in (".resolved.json",".manifest.json")):
        raise ValueError("Authoring records already exist; choose a new version id")
    groups=prepare(data)
    def target(group):
        return folder+"/Enemies/"+group.split("/",1)[1] if group.startswith("enemy/") else folder
    def name_prefix(group):return "Player_" if group=="player" else ""
    planned=[target(g)+"/DA_"+name_prefix(g)+key for g,actions in groups.items() for key in actions]
    planned += [folder+"/DA_Patterns",folder+"/DA_Encounter",folder+"/L_Preview"]
    for g,rows in (("enemy",data["actions"]),("player",data.get("player",{}).get("actions",[]))):
        for row in rows:
            if "hit_windows" in row:planned.append(folder+"/AM_"+("Player_" if g=="player" else "")+row["id"])
    for row in data["enemies"]:
        g="enemy/"+row["id"]
        if g in groups:
            planned += [target(g)+"/DA_Patterns",target(g)+"/DA_Encounter"]
            planned += [target(g)+"/AM_"+a["id"] for a in data["actions"] if "hit_windows" in a]
    if len(planned)!=len(set(p.lower() for p in planned)):raise ValueError("Generated asset name collision")
    if any(assets.does_asset_exist(p) for p in planned):raise ValueError("Generated package already exists")
    report.update(planned=planned)
    if not apply:return
    def remember(obj):
        if not obj:raise RuntimeError("Asset creation failed")
        report["created"].append(obj.get_path_name());assets.set_metadata_tag(obj,"CombatRecipeId",data["id"])
        return obj
    def new(name,kind,destination=None):
        factory=u.DataAssetFactory();factory.set_editor_property("data_asset_class",kind)
        return remember(u.AssetToolsHelpers.get_asset_tools().create_asset(name,destination or folder,kind,factory))
    generated={}
    row_groups=[("enemy",data["actions"]),("player",data.get("player",{}).get("actions",[]))]
    for enemy_row in data["enemies"]:
        g="enemy/"+enemy_row["id"]
        if g in groups:row_groups.append((g,effective_enemy(data,enemy_row)["actions"]))
    for group,rows in row_groups:
        generated[group]={}
        for row in rows:
            resolved_action=groups[group][row["id"]]
            prefix="Player_" if group=="player" else ""
            obj=new("DA_"+prefix+row["id"],u.CombatActionDefinition,target(group))
            for key in (*V2_ACTION_RANGES,*ACTION_BOOLEANS):obj.set_editor_property(key,resolved_action.get_editor_property(key))
            montage=resolved_action.get_editor_property("montage")
            if "hit_windows" in row:
                source_montage=loaded(row["montage"],u.AnimMontage) if "montage" in row else loaded(row["source"],u.CombatActionDefinition).get_editor_property("montage")
                montage=remember(assets.duplicate_asset(package(source_montage),target(group)+"/AM_"+prefix+row["id"]))
                windows=row["hit_windows"]
                if not u.CombatLabEditorLibrary.configure_authored_hit_windows(montage,
                    [w["id"] for w in windows],[w["start"] for w in windows],[w["end"] for w in windows]):
                    raise RuntimeError("Unable to configure hit windows")
                if not assets.save_loaded_asset(montage):raise RuntimeError("Montage save failed")
            obj.set_editor_property("montage",montage);obj.set_editor_property("display_name",data["id"]+" / "+row["id"])
            assets.set_metadata_tag(obj,"CombatSource",row["source"]);generated[group][row["id"]]=obj
        for row in rows:
            obj=generated[group][row["id"]];obj.set_editor_property("next_action",generated[group].get(row.get("next_action")))
            native(obj)
            if not assets.save_loaded_asset(obj):raise RuntimeError("Action save failed")
    profile=new("DA_Patterns",u.CombatPatternProfile);entries=[]
    for row in data["patterns"]:
        entry=u.CombatPatternEntry()
        for k,v in row.items():entry.set_editor_property(k,generated["enemy"][v] if k=="action" else v)
        entries.append(entry)
    profile.set_editor_property("patterns",entries)
    encounter=new("DA_Encounter",u.CombatEncounterProfile)
    for k,v in data["encounter"].items():encounter.set_editor_property(k,v)
    for obj in (profile,encounter):
        native(obj)
        if not assets.save_loaded_asset(obj):raise RuntimeError("Profile save failed")
    profiles={"enemy":(profile,encounter)}
    for enemy_row in data["enemies"]:
        g="enemy/"+enemy_row["id"]
        if g not in groups:continue
        effective=effective_enemy(data,enemy_row)
        local_profile=new("DA_Patterns",u.CombatPatternProfile,target(g));entries=[]
        for row in effective["patterns"]:
            entry=u.CombatPatternEntry()
            for k,v in row.items():entry.set_editor_property(k,generated[g][v] if k=="action" else v)
            entries.append(entry)
        local_profile.set_editor_property("patterns",entries)
        local_encounter=new("DA_Encounter",u.CombatEncounterProfile,target(g))
        for k,v in effective["encounter"].items():local_encounter.set_editor_property(k,v)
        for obj in (local_profile,local_encounter):
            native(obj)
            if not assets.save_loaded_asset(obj):raise RuntimeError("Instance profile save failed")
        profiles[g]=(local_profile,local_encounter)
    remember(assets.duplicate_asset(TEMPLATE,folder+"/L_Preview"))
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actor_system=u.get_editor_subsystem(u.EditorActorSubsystem)
    if not levels.load_level(folder+"/L_Preview"):raise RuntimeError("Preview load failed")
    actors=actor_system.get_all_level_actors()
    enemy=next(a for a in actors if isinstance(a,u.CombatLabCharacter) and a.get_editor_property("training_enemy"))
    player=next(a for a in actors if isinstance(a,u.CombatLabCharacter) and not a.get_editor_property("training_enemy"))
    # The maintained template contains all mesh, animation, collision and control defaults.
    base=enemy.get_actor_location()
    base_stats={key:data["monster_stats"].get(key,enemy.get_editor_property("combat").get_editor_property(key)) for key in STAT_RANGES}
    enemies=[enemy]
    for row in data["enemies"][1:]:
        clone=u.CombatLabEditorLibrary.duplicate_review_enemy(enemy,u.Vector(0,0,0))
        if not clone:raise RuntimeError("Enemy duplication failed")
        enemies.append(clone)
    for actor,row in zip(enemies,data["enemies"]):
        actor.set_actor_location(base+u.Vector(*row["offset"]),False,False)
        actor.set_actor_label(data["id"]+" / "+row["id"])
        vfx_settings(actor,resolved_vfx(data.get("monster_vfx"),row.get("vfx")),True)
        g="enemy/"+row["id"] if "enemy/"+row["id"] in groups else "enemy"
        actor.set_editor_property("action",next(iter(generated[g].values())))
        actor.set_editor_property("pattern_profile",profiles[g][0]);actor.set_editor_property("encounter_profile",profiles[g][1])
        for key,value in effective_enemy(data,row)["monster_stats"].items():actor.get_editor_property("combat").set_editor_property(key,value)
    vfx_settings(player,data.get("player",{}).get("vfx",{}),True)
    if "player" in data:
        for slot,prop in (("basic","action"),("skill","skill_action"),("ultimate","ultimate_action")):
            player.set_editor_property(prop,generated["player"].get(data["player"]["slots"].get(slot)))
        for key,value in data["player"]["stats"].items():player.get_editor_property("combat").set_editor_property(key,value)
        if "move_speed" in data["player"]:player.get_editor_property("character_movement").set_editor_property("max_walk_speed",data["player"]["move_speed"])
    director=actor_system.spawn_actor_from_class(u.CombatEncounterDirector,u.Vector(0,0,0))
    if not director:raise RuntimeError("Encounter director creation failed")
    director.set_actor_label(data["id"]+" / Encounter")
    director.set_editor_property("max_attackers",data["max_attackers"])
    director.set_editor_property("battle_zone_key",data["battle_key"])
    director.set_editor_property("notify_scene_events",data["notify_scene"])
    director.set_editor_property("enemies",enemies);director.set_editor_property("player",player)
    for actor in [player,*enemies]:actor.set_editor_property("encounter_director",director)
    if not levels.save_current_level():raise RuntimeError("Preview save failed")
    write_provenance(data,generated,player,enemies,report,base_stats)

def write_provenance(data,generated,player,enemies,report,base_stats):
    import hashlib
    root=Path(u.Paths.project_dir()).resolve()
    document=copy.deepcopy(data);document.pop("warnings",None)
    for group,rows in (("enemy",document["actions"]),("player",document.get("player",{}).get("actions",[]))):
        for row in rows:
            obj=generated[group][row["id"]]
            row["source"]=package(obj)
            row["values"]={key:obj.get_editor_property(key) for key in (*V2_ACTION_RANGES,*ACTION_BOOLEANS)}
            row["montage"]=package(obj.get_editor_property("montage"))
    document["monster_stats"]=base_stats
    document["monster_vfx"]=resolved_vfx(data.get("monster_vfx"))
    if "player" in document:
        document["player"]["vfx"]=resolved_vfx(data["player"].get("vfx"))
        document["player"]["stats"]={key:player.get_editor_property("combat").get_editor_property(key) for key in STAT_RANGES}
        document["player"]["move_speed"]=player.get_editor_property("character_movement").get_editor_property("max_walk_speed")
    def actor_manifest(actor,role,identity):
        def path(obj):return obj.get_path_name() if obj else "None"
        action=actor.get_editor_property("action");profile=actor.get_editor_property("pattern_profile")
        encounter=actor.get_editor_property("encounter_profile")
        signature="|".join(path(x) for x in (actor.get_editor_property("mesh").get_editor_property("skeletal_mesh_asset"),action,profile,encounter))
        skill=actor.get_editor_property("skill_action");ultimate=actor.get_editor_property("ultimate_action")
        if skill:signature+="|skill:"+path(skill)
        if ultimate:signature+="|ultimate:"+path(ultimate)
        patterns=profile.get_editor_property("patterns") if profile else []
        for entry in patterns:signature+="|pattern:"+str(entry.get_editor_property("id"))+"="+path(entry.get_editor_property("action"))
        visited={}
        def visit(obj):
            if not obj or path(obj) in visited:return
            key=obj.get_name()[3:]
            if key.startswith("Player_"):key=key[7:]
            visited[path(obj)]=key;visit(obj.get_editor_property("next_action"))
        for obj in (action,skill,ultimate):visit(obj)
        for entry in patterns:visit(entry.get_editor_property("action"))
        signature+="".join("|"+key for key in visited)
        return {"role":role,"id":identity,"signature":signature,"actions":visited,"has_encounter":bool(encounter),
            "patterns":[str(entry.get_editor_property("id")) for entry in patterns]}
    map_path=BASE+"/"+data["id"]+"/L_Preview"
    actors={map_path+"/"+player.get_name():actor_manifest(player,"player","player")}
    for actor,row in zip(enemies,data["enemies"]):
        actors[map_path+"/"+actor.get_name()]=actor_manifest(actor,"monster",row["id"])
    content=json.dumps(document,ensure_ascii=False,indent=2)
    provenance=root/"CombatRecipes"/(data["id"]+".resolved.json")
    with provenance.open("x",encoding="utf-8") as stream:stream.write(content)
    manifest={"schema_version":1,"kind":"ConstellationCombatAuthoringManifest","id":data["id"],"complete":True,
        "recipe_sha256":hashlib.sha256(provenance.read_bytes()).hexdigest(),"actors":actors}
    path=root/"CombatRecipes"/(data["id"]+".manifest.json")
    with path.open("x",encoding="utf-8") as stream:json.dump(manifest,stream,ensure_ascii=False,indent=2)
    report.update(preview_map=map_path,provenance=str(provenance),manifest=str(path))
