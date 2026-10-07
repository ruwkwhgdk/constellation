import unittest
from combat_recipe_compare import compare_recipes
class ComparisonTests(unittest.TestCase):
    def data(self):
        return {"id":"Old","mesh":"/Game/Mesh","actions":[{"id":"Light","source":"/Game/Old","values":{"damage":12,"play_rate":.7}}],"patterns":[{"id":"Light","weight":1}],"encounter":{"move_speed":220}}
    def test_version_and_source_are_not_tuning_changes(self):
        a=self.data(); b=self.data(); b["id"]="New"; b["actions"][0]["source"]="/Game/New"
        self.assertEqual(compare_recipes(a,b),[])
    def test_changed_value_has_location(self):
        a=self.data(); b=self.data(); b["actions"][0]["values"]["damage"]=15
        self.assertEqual(compare_recipes(a,b),[{"path":"actions.Light.values.damage","before":12,"after":15}])
    def test_float_serialization_noise(self):
        a=self.data(); b=self.data(); b["actions"][0]["values"]["play_rate"]=.699999988
        self.assertEqual(compare_recipes(a,b),[])
    def test_representable_float_change_is_not_hidden(self):
        a=self.data(); b=self.data(); a["actions"][0]["values"]["damage"]=1000000; b["actions"][0]["values"]["damage"]=1000000.0625
        self.assertEqual(len(compare_recipes(a,b)),1)
    def test_removed_pattern(self):
        a=self.data(); b=self.data(); b["patterns"]=[]
        self.assertEqual(compare_recipes(a,b)[0]["path"],"patterns.Light")
    def test_boolean_not_numeric(self):
        a=self.data(); b=self.data(); a["encounter"]["flag"]=True; b["encounter"]["flag"]=1
        self.assertEqual(len(compare_recipes(a,b)),1)
if __name__=="__main__": unittest.main()
