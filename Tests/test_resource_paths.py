import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Content/Python'))
import resource_paths as p

class ResourcePathTests(unittest.TestCase):
    def test_historical_report_nested_object_paths(self):
        pth='/Game/Levels/L_StartIsland'
        expected='/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland'
        self.assertEqual(p.remap_data({'map':pth,'objects':[pth+'.L_StartIsland:PersistentLevel.Actor']}),{'map':expected,'objects':[expected+'.L_StartIsland:PersistentLevel.Actor']})
    def test_unknown_source_and_substring_are_preserved(self):
        for value in ['ArtSource/Example/file.blend','/Game/Levels/L_StartIslandExtra','/Game/LuosCaves/SM_Cave']:
            self.assertEqual(p.resolve(value),value)
    def test_json_input_remapped_without_modifying_original(self):
        source='{"map":"/Game/Levels/L_StartIsland"}'
        self.assertIn('/Constellation/',p.loads(source)['map'])
        self.assertNotIn('/Constellation/',source)
    def test_historical_blueprint_alias_class_name(self):
        self.assertEqual(p.resolve('/Game/Blueprints/Character/PC/BP_Player.BP_Player_C'),'/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine.BP_Player_Heroine_C')

if __name__=='__main__':unittest.main()
