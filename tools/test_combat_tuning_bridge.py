import copy
import unittest
from test_combat_recipe_v2 import extended
from combat_recipe import validate_recipe,V2_ACTION_RANGES,ACTION_BOOLEANS,STAT_RANGES
from combat_tuning_bridge import convert_report,expected_fields

def fixture():
    data=extended()
    defaults={k:v[0] for k,v in V2_ACTION_RANGES.items()}
    defaults.update(damage=20,stamina_cost=10,cooldown=.4,play_rate=1,reach=140,radius=30,
        input_window_start=.3,input_window_end=.6,dodge_cancel_start=.5,dodge_cancel_end=.7,dash_duration=.25)
    defaults.update({k:False for k in ACTION_BOOLEANS})
    stats={k:v[0] for k,v in STAT_RANGES.items()}
    stats.update(max_health=100,max_stamina=100,dodge_duration=.6,dodge_invulnerable_start=.1,dodge_invulnerable_end=.3)
    for rows in (data["actions"],data["player"]["actions"]):
        for row in rows:row["values"]={**defaults,**row.get("values",{})}
    data["monster_stats"]={**stats,**data["monster_stats"]}
    data["player"]["stats"]={**stats,**data["player"]["stats"]}
    data=validate_recipe(data);data.pop("warnings")
    actors={}
    for role,identity in (("player","player"),("monster","Left"),("monster","Right")):
        rows=data["player"]["actions"] if role=="player" else data["actions"]
        actors["/Game/Test/"+identity]={"id":identity,"role":role,"signature":"signature-"+identity,
            "actions":{"/Game/"+identity+"/"+a["id"]:a["id"] for a in rows},
            "patterns":[] if role=="player" else ["Light"],"has_encounter":role=="monster"}
    manifest={"kind":"ConstellationCombatAuthoringManifest","schema_version":1,"complete":True,"id":data["id"],"actors":actors}
    values={}
    for key,(meta,category,prop,entry) in expected_fields(manifest,data).items():
        scope=data["player"] if meta["role"]=="player" else data
        if category=="stats":value=(scope["stats"] if meta["role"]=="player" else data["monster_stats"])[prop]
        elif category=="movement":value=500
        elif category=="actions":value=next(a for a in scope["actions"] if a["id"]==entry)["values"][prop]
        elif category=="encounter":value=data["encounter"][prop]
        else:value=data["patterns"][0][prop]
        values[key]=int(value) if type(value) is bool else value
    report={"kind":"ConstellationCombatTuningReport","schema_version":1,"preset":{"schema_version":4,
        "sources":{k:v["signature"] for k,v in actors.items()},"values":values},"fields":[{"proposed":999999}]}
    return data,manifest,report

class TuningBridgeTests(unittest.TestCase):
    def test_individual_enemy_and_player_preserved(self):
        data,manifest,report=fixture();before=copy.deepcopy(data)
        report["preset"]["values"]["/Game/Test/Left/Action//Game/Left/Light/Damage"]=55
        report["preset"]["values"]["/Game/Test/player/Combat/MaxHealth"]=130
        out,changes=convert_report(data,manifest,report,"NewVersion")
        self.assertEqual(out["enemies"][0]["action_values"]["Light"]["damage"],55)
        self.assertNotIn("damage",out["enemies"][1].get("action_values",{}).get("Light",{}))
        self.assertEqual(out["player"]["stats"]["max_health"],130)
        self.assertEqual(data,before);self.assertEqual(len(changes),2)
    def test_source_mismatch(self):
        data,m,r=fixture();r["preset"]["sources"]["/Game/Test/player"]="wrong"
        with self.assertRaisesRegex(ValueError,"원본"):convert_report(data,m,r,"Next")
    def test_missing_unknown_and_nonfinite(self):
        for mode in ("missing","unknown","nan","bool"):
            d,m,r=fixture();v=r["preset"]["values"];key=next(iter(v))
            if mode=="missing":v.pop(key)
            elif mode=="unknown":v["unexpected"]=1
            else:v[key]=float("nan") if mode=="nan" else True
            with self.assertRaises(ValueError):convert_report(d,m,r,"Next")
    def test_current_version_cannot_be_overwritten(self):
        d,m,r=fixture()
        with self.assertRaises(ValueError):convert_report(d,m,r,d["id"])
    def test_invalid_proposed_combination_rejected(self):
        d,m,r=fixture();r["preset"]["values"]["/Game/Test/Left/Encounter/LoseRadius"]=1
        with self.assertRaisesRegex(ValueError,"lose_radius"):convert_report(d,m,r,"Next")
if __name__=="__main__":unittest.main()
