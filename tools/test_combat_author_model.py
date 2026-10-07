import tempfile
import unittest
from pathlib import Path
from test_combat_recipe_v2 import extended
from combat_recipe import validate_recipe
from combat_author_model import save_version,read_version,versions,command

class AuthorModelTests(unittest.TestCase):
    def test_roundtrip_and_exclusive_save(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=extended();save_version(data,root)
            self.assertEqual(read_version(data["id"],root)["player"],validate_recipe(data)["player"])
            with self.assertRaises(FileExistsError):save_version(data,root)
            self.assertEqual(len(versions(root)),1)
    def test_invalid_never_creates_file(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=extended();data["id"]="../escape"
            with self.assertRaises(ValueError):save_version(data,root)
            self.assertFalse((root/"CombatRecipes").exists())
    def test_command_is_fixed_argument_vector(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=extended();save_version(data,root)
            args=command("build",data["id"],root)
            self.assertEqual(args[-1],"-Apply")
            with self.assertRaises(ValueError):command("play",data["id"],root)
            with self.assertRaises(ValueError):command("build","x;calc",root)
    def test_partial_map_is_not_playable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=extended();save_version(data,root)
            folder=root/"Content/Constellation/Review/CombatRecipes"/data["id"];folder.mkdir(parents=True)
            (folder/"L_Preview.umap").touch()
            self.assertFalse(versions(root)[0]["playable"])
            with self.assertRaises(ValueError):command("play",data["id"],root)

    def test_incomplete_manifest_pair_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=extended();save_version(data,root)
            (root/"CombatRecipes"/(data["id"]+".manifest.json")).write_text('{"complete":true}')
            with self.assertRaises(ValueError):read_version(data["id"],root)

    def test_generated_version_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=extended();(root/"Content/Constellation/Review/CombatRecipes"/data["id"]).mkdir(parents=True)
            with self.assertRaises(ValueError):save_version(data,root)
if __name__=="__main__":unittest.main()
