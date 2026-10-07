import copy
import unittest
from combat_recipe import validate_recipe, load_recipe

def recipe():
    return {"schema_version":1,"id":"SlimeScout_v1",
            "mesh":"/Game/Constellation/Characters/Enemies/Slime_Normal/SKM_Slime_Normal",
            "actions":[{"id":"Light","source":"/Game/Constellation/Review/CombatCore/DA_EnemyStrike","values":{"damage":12}}],
            "patterns":[{"id":"Light","action":"Light","max_consecutive":0}],
            "encounter":{}}

class RecipeTests(unittest.TestCase):
    def rejected(self, data, text):
        with self.assertRaisesRegex(ValueError,text):
            validate_recipe(data)
    def test_defaults(self):
        out=validate_recipe(recipe())
        self.assertEqual(out["encounter"]["move_speed"],220)
        self.assertEqual(out["patterns"][0]["max_distance"],180)
    def test_unknown_fields(self):
        data=recipe(); data["encounter"]["move_speeed"]=200
        self.rejected(data,"move_speeed")
    def test_unsafe_id(self):
        data=recipe(); data["id"]="../Core"
        self.rejected(data,"id")
    def test_case_insensitive_ids(self):
        data=recipe(); data["actions"].append({"id":"light","source":data["actions"][0]["source"]})
        self.rejected(data,"duplicate")
    def test_reserved_asset_names(self):
        for name in ("Patterns","encounter"):
            data=recipe(); data["actions"][0]["id"]=name
            self.rejected(data,"reserved")
    def test_unknown_action(self):
        data=recipe(); data["patterns"][0]["action"]="Missing"
        self.rejected(data,"Missing")
    def test_unreachable_attack_distance(self):
        data=recipe(); data["patterns"][0]["max_distance"]=100
        self.rejected(data,"attack_distance")
    def test_disabled_patterns(self):
        data=recipe(); data["patterns"][0]["weight"]=0
        self.rejected(data,"enabled")
    def test_repeat_dead_end(self):
        data=recipe(); data["patterns"][0]["max_consecutive"]=2
        self.assertTrue(any("repeat" in w for w in validate_recipe(data)["warnings"]))
    def test_nan_and_bool_numbers(self):
        for value in (float("nan"),float("inf"),True):
            data=recipe(); data["actions"][0]["values"]["damage"]=value
            self.rejected(data,"damage")
    def test_bad_ranges(self):
        data=recipe(); data["encounter"]["lose_radius"]=1
        self.rejected(data,"lose_radius")
    def test_unaffordable_cost(self):
        data=recipe(); data["actions"][0]["values"]["stamina_cost"]=101
        self.rejected(data,"stamina_cost")
    def test_does_not_mutate_input(self):
        data=recipe(); before=copy.deepcopy(data); validate_recipe(data)
        self.assertEqual(data,before)

if __name__=="__main__":
    unittest.main()
