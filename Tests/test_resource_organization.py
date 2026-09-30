import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('organization',Path(__file__).resolve().parents[1]/'tools/resource_organization.py')
org=importlib.util.module_from_spec(spec);spec.loader.exec_module(org)

class OrganizationTests(unittest.TestCase):
    def test_vendor_and_engine_managed_paths_stay(self):
        for p in ['/Game/LuosCaves/Textures/T_Rock','/Game/Resources/VFX/FXVarietyPack/Materials/M_Fire','/Game/__ExternalActors__/A/B/C','/Game/Levels/_GENERATED/User/Mesh']:
            self.assertEqual(org.destination(p,[])[0],p)
    def test_quest_is_one_domain_and_map_name_is_preserved(self):
        self.assertEqual(org.destination('/Game/Data/Quests/DA_QuestDatabase',['DataAsset'])[0],'/Game/Constellation/Gameplay/Quests/Data/DA_QuestDatabase')
        self.assertEqual(org.destination('/Game/Levels/L_StartIsland',['World'])[0],'/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland')
    def test_patch_object_suffix_and_longest_boundary(self):
        moves={'/Game/A/B':'/Game/Constellation/C/B','/Game/A':'/Game/Constellation/C'}
        self.assertEqual(org.replace_paths("'/Game/A/B.B_C' '/Game/AB/X'",moves),"'/Game/Constellation/C/B.B_C' '/Game/AB/X'")
    def test_collision_is_fatal(self):
        with self.assertRaises(ValueError):org.check_destinations([{'old':'/Game/A','new':'/Game/Z'},{'old':'/Game/B','new':'/Game/Z'}])
    def test_windows_case_collision_is_fatal(self):
        with self.assertRaises(ValueError):org.check_destinations([{'old':'/Game/A','new':'/Game/X/Test'},{'old':'/Game/B','new':'/Game/X/test'}])
    def test_existing_redirector_chain_resolves_to_moved_target(self):
        rows=[{'old':'/Game/Actual','new':'/Game/Constellation/Actual'}]
        baseline={'/Game/Old':{'classes':['ObjectRedirector'],'dependencies':['/Game/Alias']},'/Game/Alias':{'classes':['ObjectRedirector'],'dependencies':['/Game/Actual']}}
        self.assertEqual(org.resolved_mapping(rows,baseline)['/Game/Old'],'/Game/Constellation/Actual')
    def test_alias_object_and_generated_class_names_follow_target(self):
        mapping={'/Game/BP_Old':'/Game/Constellation/BP_New'}
        self.assertEqual(org.replace_paths("/Game/BP_Old.BP_Old_C /Game/BP_Old.BP_Old",mapping),"/Game/Constellation/BP_New.BP_New_C /Game/Constellation/BP_New.BP_New")

if __name__=='__main__':unittest.main()
