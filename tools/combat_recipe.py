"""Strict, engine-independent input validation for monster combat recipes."""
import copy
import json
import math
import re
from pathlib import Path

ACTION_RANGES={"damage":(0,1e6),"stamina_cost":(0,100),"cooldown":(0,1e6),
               "play_rate":(.01,100),"reach":(.01,1e6),"radius":(.01,1e6)}
V2_ACTION_RANGES={**ACTION_RANGES,"stamina_cost":(0,1e6),"ultimate_cost":(0,100),"ultimate_gain":(0,100),
    "dash_distance":(0,3000),"dash_duration":(.01,10),"input_window_start":(0,120),"input_window_end":(0,120),
    "dodge_cancel_start":(0,120),"dodge_cancel_end":(0,120)}
ACTION_BOOLEANS=("radial_hit","allow_dodge_cancel")
STAT_RANGES={"max_health":(1,1e6),"max_stamina":(1,1e6),"stamina_recovery_per_second":(0,1e6),
    "stamina_recovery_delay":(0,120),"hit_reaction_duration":(0,10),"dodge_duration":(.01,10),
    "dodge_distance":(.01,3000),"dodge_stamina_cost":(0,1e6),"dodge_invulnerable_start":(0,10),"dodge_invulnerable_end":(0,10)}

PATTERN_DEFAULTS={"min_distance":0,"max_distance":180,"max_angle":80,"require_sight":True,"weight":1,"max_consecutive":1}
ENCOUNTER_DEFAULTS={"detect_radius":800,"lose_radius":1100,"leash_radius":700,"attack_distance":140,
                    "move_speed":220,"think_interval":.2,"lost_sight_time":3,"home_tolerance":50,
                    "retry_delay":1,"retry_cooldown":3,"stuck_timeout":2,"max_move_failures":3,"restore_on_return":True}

def fail(where,message):
    raise ValueError(f"{where}: {message}")

def fields(value,allowed,where,required=()):
    if not isinstance(value,dict):
        fail(where,"expected object")
    unknown=set(value)-set(allowed)
    if unknown:
        fail(where,"unknown fields "+", ".join(sorted(unknown)))
    for key in required:
        if key not in value:
            fail(where,f"missing {key}")

def identifier(value,where):
    if not isinstance(value,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,47}",value) or value.lower()=="none":
        fail(where,"use 1-48 ASCII letters/digits/underscores, starting with a letter")
    return value

def asset_path(value,where):
    if not isinstance(value,str) or not re.fullmatch(r"/Game/(?:[A-Za-z0-9_]+/)*[A-Za-z0-9_]+",value):
        fail(where,"expected /Game/... asset package path")
    return value

def number(value,low,high,where,integer=False):
    if type(value) not in (int,float) or not math.isfinite(value) or not low<=value<=high or (integer and type(value) is not int):
        fail(where,f"expected finite {'integer' if integer else 'number'} in [{low}, {high}]")

def boolean(value,where):
    if type(value) is not bool:
        fail(where,"expected boolean")

def unique(rows,where):
    if not isinstance(rows,list) or not 1<=len(rows)<=32:
        fail(where,"expected 1-32 entries")
    seen=set()
    for i,row in enumerate(rows):
        if not isinstance(row,dict):
            fail(f"{where}[{i}]","expected object")
        key=identifier(row.get("id"),f"{where}[{i}].id").lower()
        if key in seen:
            fail(where,"duplicate ID (case insensitive)")
        seen.add(key)

VFX_KINDS=("SwordHit","SwordBlock","SwordParry","SlimeAttack","SlimeHit","RunDust","GlassBreak","CaveDust","CaveMist","WaterDrop","WaterRipple","CaveSpore","PlayerHit")
VFX_DEFAULT_CUE={"mode":"Default","kind":"SwordHit","system":None,"color":[1,1,1,1],"scale":1,"duration":2}
def validate_vfx(value,where,partial=False):
    fields(value,("enabled","attack","hit"),where)
    if "enabled" in value:boolean(value["enabled"],where+".enabled")
    for slot in ("attack","hit"):
        if slot not in value:continue
        cue=value[slot];path=where+"."+slot;fields(cue,VFX_DEFAULT_CUE,path)
        mode=cue.get("mode","Default")
        if mode not in ("Default","Disabled","Builtin","Niagara"):fail(path+".mode","unknown effect mode")
        if cue.get("kind","SwordHit") not in VFX_KINDS:fail(path+".kind","unknown built-in effect")
        if not partial and mode=="Niagara" and not cue.get("system"):fail(path+".system","Niagara asset required")
        if cue.get("system") is not None:asset_path(cue["system"],path+".system")
        number(cue.get("scale",1),.01,10,path+".scale");number(cue.get("duration",2),.05,10,path+".duration")
        color=cue.get("color",[1,1,1,1])
        if not isinstance(color,list) or len(color)!=4:fail(path+".color","expected RGBA array")
        for i,v in enumerate(color):number(v,0,1 if i==3 else 20,path+".color")

def resolved_vfx(common=None,individual=None):
    result={"enabled":True,"attack":copy.deepcopy(VFX_DEFAULT_CUE),"hit":copy.deepcopy(VFX_DEFAULT_CUE)}
    for source in (common or {},individual or {}):
        if "enabled" in source:result["enabled"]=source["enabled"]
        for slot in ("attack","hit"):result[slot].update(source.get(slot,{}))
    return result

def validate_stats(stats,where):
    fields(stats,STAT_RANGES,where)
    for k,v in stats.items():number(v,*STAT_RANGES[k],where+"."+k)
    if "dodge_invulnerable_start" in stats and "dodge_invulnerable_end" in stats:
        if stats["dodge_invulnerable_start"]>=stats["dodge_invulnerable_end"]:fail(where,"invalid dodge invulnerability interval")
    if "dodge_duration" in stats and stats.get("dodge_invulnerable_end",0)>stats["dodge_duration"]:
        fail(where,"invulnerability exceeds dodge duration")

def validate_actions(rows,version,where):
    unique(rows,where);actions={}
    ranges=V2_ACTION_RANGES if version==2 else ACTION_RANGES
    for a in rows:
        path=where+"."+a["id"]
        if a["id"].lower() in ("patterns","encounter") or a["id"].lower().startswith("player_"):
            fail(path,"reserved generated asset name")
        fields(a,("id","source","values")+(("montage","hit_windows","next_action") if version==2 else ()),path,("source",))
        asset_path(a["source"],path+".source")
        a.setdefault("values",{})
        fields(a["values"],(*ranges,*(ACTION_BOOLEANS if version==2 else ())),path+".values")
        for key,value in a["values"].items():
            if key in ACTION_BOOLEANS:boolean(value,path+"."+key)
            else:number(value,*ranges[key],path+"."+key)
        if "montage" in a:asset_path(a["montage"],path+".montage")
        if "hit_windows" in a:
            unique(a["hit_windows"],path+".hit_windows")
            for w in a["hit_windows"]:
                fields(w,("id","start","end"),path+".hit_windows",("start","end"))
                number(w["start"],0,120,path+".hit_windows.start");number(w["end"],0,120,path+".hit_windows.end")
                if w["end"]<=w["start"]:fail(path+".hit_windows.end","must exceed start")
        actions[a["id"]]=a
    for key,a in actions.items():
        seen={key};following=a.get("next_action")
        while following is not None:
            if not isinstance(following,str) or following not in actions:fail(where+"."+key,"unknown next action "+str(following))
            if following in seen:fail(where+"."+key,"follow-up cycle")
            seen.add(following);following=actions[following].get("next_action")
    return actions

def validate_recipe(raw):
    if not isinstance(raw,dict) or type(raw.get("schema_version")) is not int or raw["schema_version"] not in (1,2):
        fail("schema_version","only version 1 or 2 is supported")
    version=raw["schema_version"]
    base=("schema_version","id","mesh","actions","patterns","encounter")
    fields(raw,base+(("player","monster_stats","enemies","max_attackers","battle_key","notify_scene","monster_vfx") if version==2 else ()),"recipe",base)
    data=copy.deepcopy(raw)
    identifier(data["id"],"id"); asset_path(data["mesh"],"mesh")
    unique(data["patterns"],"patterns")
    actions=validate_actions(data["actions"],version,"actions")
    if version==2:
        data.setdefault("battle_key","");data.setdefault("notify_scene",False)
        boolean(data["notify_scene"],"notify_scene")
        if not isinstance(data["battle_key"],str):fail("battle_key","expected string")
        if data["battle_key"]:identifier(data["battle_key"],"battle_key")
        if data["notify_scene"] and not data["battle_key"]:fail("battle_key","required when notify_scene is enabled")
        for action in data["actions"]:
            if action.get("next_action"):fail("actions."+action["id"],"monster follow-up chains are not supported; use AI patterns")
        if "monster_vfx" in data:validate_vfx(data["monster_vfx"],"monster_vfx")
        data.setdefault("monster_stats",{});validate_stats(data["monster_stats"],"monster_stats")
        data.setdefault("enemies",[{"id":"Enemy1","offset":[0,0,0]}])
        unique(data["enemies"],"enemies")
        if len(data["enemies"])>16: fail("enemies","maximum 16 enemies")
        for row in data["enemies"]:
            fields(row,("id","offset","stats","action_values","pattern_values","encounter_values","vfx"),"enemies."+row["id"],("offset",))
            if "vfx" in row:validate_vfx(row["vfx"],"enemies."+row["id"]+".vfx",partial=True)
            validate_vfx(resolved_vfx(data.get("monster_vfx"),row.get("vfx")),"enemies."+row["id"]+".vfx")
            if not isinstance(row["offset"],list) or len(row["offset"])!=3:fail("enemies.offset","expected three numbers")
            for v in row["offset"]:number(v,-10000,10000,"enemies.offset")
        data.setdefault("max_attackers",1)
        number(data["max_attackers"],1,16,"max_attackers",integer=True)
        if "player" in data:
            player=data["player"];fields(player,("actions","slots","stats","move_speed","vfx"),"player",("actions","slots"))
            if "vfx" in player:validate_vfx(player["vfx"],"player.vfx")
            if "move_speed" in player:number(player["move_speed"],1,3000,"player.move_speed")
            player_actions=validate_actions(player["actions"],2,"player.actions")
            fields(player["slots"],("basic","skill","ultimate"),"player.slots",("basic",))
            for key,value in player["slots"].items():
                if value is not None and (not isinstance(value,str) or value not in player_actions):
                    fail("player.slots."+key,"unknown action "+str(value))
            if player["slots"]["basic"] is None:fail("player.slots.basic","basic action required")
            player.setdefault("stats",{});validate_stats(player["stats"],"player.stats")
    fields(data["encounter"],ENCOUNTER_DEFAULTS,"encounter")
    enc={**ENCOUNTER_DEFAULTS,**data["encounter"]}
    for key,value in enc.items():
        if key=="restore_on_return":
            boolean(value,"encounter."+key)
        else:
            low=0 if key=="lost_sight_time" else .01
            if key=="think_interval": low=.05
            if key=="max_move_failures": low=1
            number(value,low,1e6,"encounter."+key,integer=key=="max_move_failures")
    if enc["lose_radius"]<enc["detect_radius"]:
        fail("encounter.lose_radius","must be >= detect_radius")
    if enc["attack_distance"]>=enc["detect_radius"]:
        fail("encounter.attack_distance","must be < detect_radius")
    if enc["home_tolerance"]>=enc["leash_radius"]:
        fail("encounter.home_tolerance","must be < leash_radius")
    data["encounter"]=enc
    patterns=[]
    for p in data["patterns"]:
        where="patterns."+p["id"]
        fields(p,("id","action",*PATTERN_DEFAULTS),where,("action",))
        if not isinstance(p["action"],str) or p["action"] not in actions:
            fail(where+".action",f"unknown action {p['action']}")
        p={**PATTERN_DEFAULTS,**p}
        for key in ("min_distance","max_distance","max_angle","weight","max_consecutive"):
            number(p[key],0,180 if key=="max_angle" else 1e6,where+"."+key,integer=key=="max_consecutive")
        boolean(p["require_sight"],where+".require_sight")
        if p["min_distance"]>p["max_distance"]:
            fail(where,"min_distance exceeds max_distance")
        patterns.append(p)
    enabled=[p for p in patterns if p["weight"]>0]
    if not enabled:
        fail("patterns","at least one enabled pattern is required")
    # Approach requests stop at AttackDistance-20; status can enter Fighting anywhere
    # up to AttackDistance. Require one continuous viable range over that stop band.
    low=max(0,enc["attack_distance"]-20)
    usable=[p for p in enabled if p["min_distance"]<=low and p["max_distance"]>=enc["attack_distance"]]
    if not usable:
        fail("encounter.attack_distance","no enabled pattern covers the approach stop range")
    warnings=[]
    if len(enabled)==1 and enabled[0]["max_consecutive"]>0:
        warnings.append("Single enabled pattern has a repeat limit: the enemy will eventually wait indefinitely.")
    for p in enabled:
        if p not in usable:
            warnings.append(f"{p['id']}: not available throughout the approach stop range; situational only.")
    data["patterns"]=patterns
    if version==2:
        for row in data["enemies"]:
            if any(k in row for k in ("stats","action_values","pattern_values","encounter_values")):
                validate_recipe(effective_enemy(data,row))
    data["warnings"]=warnings
    return data

def effective_enemy(data,row):
    """Resolve an actor's explicit tuning without mutating shared monster defaults."""
    out=copy.deepcopy(data);out.pop("warnings",None);out.pop("player",None)
    out["enemies"]=[{"id":row["id"],"offset":row["offset"]}]
    for key,base in (("stats","monster_stats"),("encounter_values","encounter")):
        if key in row:
            if not isinstance(row[key],dict):fail("enemies."+row["id"]+"."+key,"expected object")
            out[base]={**out.get(base,{}),**row[key]}
    for key,base in (("action_values","actions"),("pattern_values","patterns")):
        overrides=row.get(key,{})
        if not isinstance(overrides,dict):fail("enemies."+row["id"]+"."+key,"expected object")
        known={r["id"]:r for r in out[base]}
        for name,values in overrides.items():
            if name not in known:fail("enemies."+row["id"]+"."+key,"unknown entry "+name)
            if not isinstance(values,dict):fail(key+"."+name,"expected object")
            if base=="actions":known[name]["values"].update(values)
            else:
                fields(values,PATTERN_DEFAULTS,key+"."+name)
                known[name].update(values)
    return out

def load_recipe(path):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:
                fail(key,"duplicate JSON key")
            result[key]=value
        return result
    return validate_recipe(json.loads(Path(path).read_text(encoding="utf-8-sig"),object_pairs_hook=pairs))
