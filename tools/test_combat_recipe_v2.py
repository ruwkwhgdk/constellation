import copy
import unittest
from combat_recipe import validate_recipe
from test_combat_recipe import recipe

def extended():
    d=recipe();d["schema_version"]=2
    source="/Game/Constellation/Review/CombatCore/DA_PlayerStrike"
    d["player"]={"actions":[
        {"id":"Basic","source":source,"next_action":"Finish","values":{"input_window_start":.3,"input_window_end":.6}},
        {"id":"Finish","source":source},
        {"id":"Dash","source":source,"values":{"dash_distance":300,"dash_duration":.25,"ultimate_gain":15}},
        {"id":"Burst","source":source,"values":{"radial_hit":True,"radius":350,"ultimate_cost":100,"ultimate_gain":0}}
    ],"slots":{"basic":"Basic","skill":"Dash","ultimate":"Burst"},"stats":{"max_health":120,"max_stamina":100}}
    d["monster_stats"]={"max_health":180}
    d["enemies"]=[{"id":"Left","offset":[0,-180,0]},{"id":"Right","offset":[0,180,0]}]
    d["max_attackers"]=1
    return d

class RecipeV2Tests(unittest.TestCase):
    def test_scene_key_and_monster_chain(self):
        d=extended();d.update(battle_key="Trial",notify_scene=True)
        self.assertTrue(validate_recipe(d)["notify_scene"])
        d["battle_key"]=""
        with self.assertRaises(ValueError):validate_recipe(d)
        d=extended();extra=copy.deepcopy(d["actions"][0]);extra["id"]="Second";d["actions"].append(extra);d["actions"][0]["next_action"]="Second"
        with self.assertRaisesRegex(ValueError,"monster"):validate_recipe(d)

    def test_zero_dodge_distance_rejected(self):
        d=extended();d["player"]["stats"]["dodge_distance"]=0
        with self.assertRaisesRegex(ValueError,"dodge_distance"):validate_recipe(d)

    def test_complete_loadout(self):
        d=extended();before=copy.deepcopy(d);out=validate_recipe(d)
        self.assertEqual(out["player"]["slots"]["ultimate"],"Burst");self.assertEqual(d,before)
    def test_bad_slot_and_chain(self):
        for key in ("slot","chain"):
            d=extended()
            if key=="slot":d["player"]["slots"]["skill"]="Missing"
            else:d["player"]["actions"][0]["next_action"]="Missing"
            with self.assertRaisesRegex(ValueError,"Missing"):validate_recipe(d)
    def test_cycle_rejected(self):
        d=extended();d["player"]["actions"][1]["next_action"]="Basic"
        with self.assertRaisesRegex(ValueError,"cycle"):validate_recipe(d)
    def test_unknown_value(self):
        d=extended();d["player"]["actions"][0]["values"]["damag"]=30
        with self.assertRaisesRegex(ValueError,"damag"):validate_recipe(d)
    def test_strict_boolean(self):
        d=extended();d["player"]["actions"][3]["values"]["radial_hit"]=1
        with self.assertRaisesRegex(ValueError,"boolean"):validate_recipe(d)
    def test_motion_and_windows(self):
        d=extended();d["player"]["actions"][2]["montage"]="/Game/Motion/Dash"
        d["player"]["actions"][2]["hit_windows"]=[{"id":"Impact","start":.2,"end":.4}]
        self.assertTrue(validate_recipe(d))
        d["player"]["actions"][2]["hit_windows"][0]["end"]=.1
        with self.assertRaisesRegex(ValueError,"end"):validate_recipe(d)
    def test_enemy_positions(self):
        for value in ([0,float("nan"),0],[0,0],["0",0,0]):
            d=extended();d["enemies"][0]["offset"]=value
            with self.assertRaises(ValueError):validate_recipe(d)
    def test_limits(self):
        for k,v in (("max_attackers",0),("max_attackers",True),("max_attackers",17)):
            d=extended();d[k]=v
            with self.assertRaises(ValueError):validate_recipe(d)
    def test_per_enemy_overrides(self):
        d=extended();d["enemies"][0]["stats"]={"max_health":250}
        d["enemies"][0]["action_values"]={"Light":{"damage":44}}
        self.assertEqual(validate_recipe(d)["monster_stats"]["max_health"],180)
        d["enemies"][0]["action_values"]["Missing"]={"damage":1}
        with self.assertRaisesRegex(ValueError,"Missing"):validate_recipe(d)
    def test_new_fields_rejected_in_v1(self):
        d=extended();d["schema_version"]=1
        with self.assertRaises(ValueError):validate_recipe(d)
if __name__=="__main__":unittest.main()
