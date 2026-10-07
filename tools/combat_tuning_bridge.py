"""Convert the authoritative preset values of a play report into a new authored recipe."""
import copy
import hashlib
import json
import math
import re
from pathlib import Path
from combat_recipe import validate_recipe,identifier,effective_enemy

COMBAT={"MaxHealth":"max_health","MaxStamina":"max_stamina","StaminaRecoveryPerSecond":"stamina_recovery_per_second",
        "StaminaRecoveryDelay":"stamina_recovery_delay","HitReactionDuration":"hit_reaction_duration"}
DODGE={"DodgeDuration":"dodge_duration","DodgeDistance":"dodge_distance","DodgeStaminaCost":"dodge_stamina_cost",
       "DodgeInvulnerableStart":"dodge_invulnerable_start","DodgeInvulnerableEnd":"dodge_invulnerable_end"}
ACTIONS={"Damage":"damage","StaminaCost":"stamina_cost","bRadialHit":"radial_hit","DashDistance":"dash_distance",
         "DashDuration":"dash_duration","UltimateCost":"ultimate_cost","UltimateGain":"ultimate_gain","Cooldown":"cooldown",
         "PlayRate":"play_rate","Reach":"reach","Radius":"radius","bAllowDodgeCancel":"allow_dodge_cancel",
         "DodgeCancelStart":"dodge_cancel_start","DodgeCancelEnd":"dodge_cancel_end"}
ENCOUNTER={"MoveSpeed":"move_speed","DetectRadius":"detect_radius","LoseRadius":"lose_radius","LeashRadius":"leash_radius",
           "AttackDistance":"attack_distance","LostSightTime":"lost_sight_time","HomeTolerance":"home_tolerance","bRestoreOnReturn":"restore_on_return"}
PATTERN={"MinDistance":"min_distance","MaxDistance":"max_distance","MaxAngle":"max_angle","Weight":"weight",
         "MaxConsecutive":"max_consecutive","bRequireSight":"require_sight"}
BOOLS={"radial_hit","allow_dodge_cancel","restore_on_return","require_sight"}

def expected_fields(manifest,recipe):
    out={}
    for actor,meta in manifest["actors"].items():
        player=meta["role"]=="player";rows=recipe["player"]["actions"] if player else recipe["actions"]
        by_id={r["id"]:r for r in rows}
        def add(suffix,category,key,entry=None):
            out[actor+"/"+suffix]=(meta,category,key,entry)
        for prop,key in {**COMBAT,**(DODGE if player else {})}.items():add("Combat/"+prop,"stats",key)
        if player:add("Movement/MaxWalkSpeed","movement","move_speed")
        if meta.get("has_encounter",not player):
            for prop,key in ENCOUNTER.items():add("Encounter/"+prop,"encounter",key)
        for path,name in meta["actions"].items():
            props=dict(ACTIONS)
            if by_id[name].get("next_action"):props.update(InputWindowStart="input_window_start",InputWindowEnd="input_window_end")
            for prop,key in props.items():add("Action/"+path+"/"+prop,"actions",key,name)
        for index,name in enumerate(meta["patterns"]):
            for prop,key in PATTERN.items():add("Pattern/"+str(index)+"/"+prop,"patterns",key,name)
    return out

def convert_report(recipe,manifest,report,new_id):
    identifier(new_id,"new_id")
    if new_id.lower()==recipe["id"].lower():raise ValueError("새 버전 이름이 필요합니다.")
    if manifest.get("kind")!="ConstellationCombatAuthoringManifest" or manifest.get("schema_version")!=1 or not manifest.get("complete") or manifest.get("id")!=recipe["id"]:
        raise ValueError("제작 원본 기록이 일치하지 않습니다.")
    if report.get("kind")!="ConstellationCombatTuningReport" or report.get("schema_version")!=1:raise ValueError("지원하지 않는 플레이 보고서입니다.")
    preset=report.get("preset",{})
    if preset.get("schema_version")!=4:raise ValueError("현재 전투 도구에서 내보낸 schema4 보고서가 필요합니다.")
    sources={key:meta["signature"] for key,meta in manifest["actors"].items()}
    if preset.get("sources")!=sources:raise ValueError("보고서의 맵·슬롯·액션 원본이 선택한 버전과 다릅니다.")
    mapping=expected_fields(manifest,recipe);values=preset.get("values")
    if not isinstance(values,dict) or values.keys()!=mapping.keys():raise ValueError("누락되거나 알 수 없는 조정 항목이 있습니다.")
    out=copy.deepcopy(recipe);out.pop("warnings",None);out["id"]=new_id
    enemies={e["id"]:e for e in out["enemies"]}
    changed=[]
    for field,(meta,category,key,entry) in mapping.items():
        value=values[field]
        if type(value) not in (int,float) or not math.isfinite(value):raise ValueError(field+": 유한한 숫자가 필요합니다.")
        if key in BOOLS:
            if value not in (0,1):raise ValueError(field+": 0 또는 1이어야 합니다.")
            value=bool(value)
        if key=="max_consecutive":
            if int(value)!=value:raise ValueError(field+": 정수가 필요합니다.")
            value=int(value)
        player=meta["role"]=="player"
        effective=recipe if player else effective_enemy(recipe,next(e for e in recipe["enemies"] if e["id"]==meta["id"]))
        if player:
            target=out["player"]
            if category=="stats":destination=target["stats"];before=recipe["player"]["stats"].get(key)
            elif category=="movement":destination=target;before=recipe["player"].get(key,500)
            elif category=="actions":
                destination=next(a["values"] for a in target["actions"] if a["id"]==entry)
                before=next(a["values"].get(key) for a in recipe["player"]["actions"] if a["id"]==entry)
            else:raise ValueError("Unsupported player tuning category")
        else:
            row=enemies[meta["id"]]
            if category=="stats":destination=row.setdefault("stats",{});before=effective["monster_stats"].get(key)
            elif category=="encounter":destination=row.setdefault("encounter_values",{});before=effective["encounter"].get(key)
            elif category=="actions":
                destination=row.setdefault("action_values",{}).setdefault(entry,{})
                before=next(a["values"].get(key) for a in effective["actions"] if a["id"]==entry)
            elif category=="patterns":
                destination=row.setdefault("pattern_values",{}).setdefault(entry,{})
                before=next(a.get(key) for a in effective["patterns"] if a["id"]==entry)
            else:raise ValueError("Unsupported monster tuning category")
        if before is None or type(before) is bool and before!=value or type(before) is not bool and not math.isclose(before,value,rel_tol=1e-7,abs_tol=1e-6):
            destination[key]=value;changed.append({"field":field,"before":before,"after":value})
    for row in out["enemies"]:
        for field in ("action_values","pattern_values"):
            if field in row:
                row[field]={k:v for k,v in row[field].items() if v}
                if not row[field]:row.pop(field)
        for field in ("stats","encounter_values"):
            if field in row and not row[field]:row.pop(field)
    checked=validate_recipe(out);checked.pop("warnings",None)
    return checked,changed

def load_bridge(root,base_id,report_name,new_id):
    identifier(base_id,"base_id")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}",report_name):raise ValueError("Invalid report name")
    directory=Path(root)/"CombatRecipes"
    content=(directory/(base_id+".resolved.json")).read_bytes()
    manifest=json.loads((directory/(base_id+".manifest.json")).read_text(encoding="utf-8"))
    if hashlib.sha256(content).hexdigest()!=manifest["recipe_sha256"]:raise ValueError("제작 스냅샷이 변경되어 원본을 확인할 수 없습니다.")
    recipe=json.loads(content)
    report=json.loads((Path(root)/"Saved/CombatTuningReports"/(report_name+".json")).read_text(encoding="utf-8-sig"))
    return convert_report(recipe,manifest,report,new_id)
