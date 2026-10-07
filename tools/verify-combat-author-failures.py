import unreal as u
import sys,json,copy,hashlib
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve();sys.path.insert(0,str(root/"tools"))
from combat_recipe import load_recipe
from combat_recipe_unreal import prepare
source=root/"Content/Constellation/Review/CombatRecipes/CombatTool_v3"
def hashes():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob("*") if p.is_file()}
before=hashes();base=load_recipe(root/"CombatRecipes/CombatTool_v3.resolved.json")
for kind in ("interval","skeleton","cost"):
 d=copy.deepcopy(base);d.pop("warnings",None)
 if kind=="interval":d["enemies"][0]["stats"]={"dodge_duration":.05}
 if kind=="skeleton":d["player"]["actions"][0]["montage"]=u.load_asset(d["actions"][0]["source"]).get_editor_property("montage").get_path_name().split(".")[0]
 if kind=="cost":d["player"]["actions"][0]["values"]["stamina_cost"]=1000
 try:prepare(d)
 except (ValueError,RuntimeError) as e:u.log("EXPECTED_AUTHOR_REJECTION "+kind+": "+str(e))
 else:raise AssertionError("Invalid "+kind+" accepted")
assert hashes()==before,"Source assets changed during validation"
u.log("COMBAT_AUTHOR_FAILURES PASS")
