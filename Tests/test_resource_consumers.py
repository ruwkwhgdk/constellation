"""Check real maintained map consumers without executing scene-building recipes."""
import ast
import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / 'docs/ResourceOrganization/move_manifest.csv').open(encoding='utf-8-sig') as stream:
    MAPS = {r['new'].rsplit('/', 1)[-1]: r['new'] for r in csv.DictReader(stream)
            if r['batch'] == 'maps' and 'World' in r['classes'].split(';')}


def strings(path):
    tree = ast.parse((ROOT / path).read_text(encoding='utf-8-sig'))
    names = {}

    def value(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return names[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return value(node.left) + value(node.right)
        raise ValueError('Not a static string')

    for node in tree.body:
        if isinstance(node, ast.Assign):
            try:
                result = value(node.value)
            except (KeyError, ValueError):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names[target.id] = result
    return tree, value


class MaintainedMapConsumers(unittest.TestCase):
    def test_heroine_save_and_report_destinations(self):
        cases = [('RigReferenceFit/preview_unreal.py', 'ReferenceFit'),
                 ('UnrealImport_player_heroine_new/preview.py', 'Preview'),
                 ('WalkTimid/preview_unreal.py', 'Walk_Timid')]
        for recipe, suffix in cases:
            with self.subTest(recipe=recipe):
                tree, value = strings('ArtSource/Heroine_Tripo_Review/' + recipe)
                expected = MAPS['L_player_heroine_new_' + suffix]
                saves = [value(n.args[1]) for n in ast.walk(tree) if isinstance(n, ast.Call)
                         and isinstance(n.func, ast.Attribute) and n.func.attr == 'save_map']
                reports = [value(v) for n in ast.walk(tree) if isinstance(n, ast.Dict)
                           for k, v in zip(n.keys, n.values)
                           if isinstance(k, ast.Constant) and k.value == 'map']
                self.assertEqual(saves, [expected])
                self.assertEqual(reports, [expected])

    def test_stairwell_source_and_playable_maps(self):
        tree, value = strings('Content/Python/open_stairwell_scale2_doorwall.py')
        loads = [value(n.args[0]) for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == 'load_level']
        self.assertEqual(loads, [MAPS['L_Stairwell_Reference'], MAPS['L_Stairwell_PlayScale2']])

    def test_maintained_entrypoint_map_links(self):
        files = ['ArtSource/Stairwell_Modular/Workflow/CURRENT.md',
                 'ArtSource/OvergrownHall/CURRENT.md', 'ArtSource/OvergrownHall/Workflow/README.md',
                 'ArtSource/SubwayEntrance/CURRENT.md',
                 'ArtSource/Stairwell_Modular/Scripts/build_review_index.ps1',
                 'ArtSource/OvergrownHall/Scripts/write_tripo_full_review.py']
        wrong = []
        for path in files:
            for package in re.findall(r'/Game/[A-Za-z0-9_/]+', (ROOT / path).read_text(encoding='utf-8-sig')):
                name = package.rsplit('/', 1)[-1]
                if name in MAPS and package != MAPS[name]:
                    wrong.append((path, package, MAPS[name]))
        self.assertEqual(wrong, [])


if __name__ == '__main__':
    unittest.main()
