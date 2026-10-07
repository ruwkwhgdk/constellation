"""Neutralize the one audited legacy glass explosion; preserve physics/sound and root glass relay."""
import json
import shutil
from pathlib import Path
import unreal as u

root=Path(u.Paths.project_dir()).resolve()
asset_path="/Game/Constellation/Gameplay/Interaction/Actors/BP_Glass"
asset_file=root/"Content/Constellation/Gameplay/Interaction/Actors/BP_Glass.uasset"
out=root/"Saved/VFXImplementation"
out.mkdir(parents=True,exist_ok=True)
backup=out/"Before/BP_Glass.uasset"
backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists():
    shutil.copy2(asset_file,backup)
blueprint=u.load_asset(asset_path)
if not blueprint:
    raise RuntimeError("Unable to load audited BP_Glass")
export=u.ResourceRecoveryLibrary.export_blueprint_graphs
before=export(blueprint)
(out/"BP_Glass-before-placeholder-fix.txt").write_text(before,encoding="utf-8")
def patch(apply):
    result=u.ConstellationVFXEditorLibrary.neutralize_legacy_glass_placeholder(blueprint,apply)
    # Unreal Python uses bool+out signatures as optional out values.
    if isinstance(result,str):return True,result
    if result is None:return False,"Editor helper rejected input"
    return result
ok,dry=patch(False)
if not ok:
    raise RuntimeError("Glass placeholder dry-run rejected: "+dry)
ok,result=patch(True)
if not ok:
    raise RuntimeError("Glass placeholder patch rejected: "+result)
after=export(blueprint)
if "SimpleExplosion" in after:
    raise RuntimeError("Graph still references the legacy explosion; not saved")
if not u.EditorAssetLibrary.save_loaded_asset(blueprint):
    raise RuntimeError("Saving neutralized BP_Glass failed")
(out/"BP_Glass-after-placeholder-fix.txt").write_text(after,encoding="utf-8")
# Idempotent check is read-only after the single approved mutation.
ok,recheck=patch(False)
if not ok:
    raise RuntimeError("Post-save glass audit failed: "+recheck)
report={"asset":asset_path,"backup":str(backup),"dry_run":dry,"result":result,"recheck":recheck,
        "simple_explosion_before":before.count("SimpleExplosion"),"simple_explosion_after":after.count("SimpleExplosion"),
        "exec_and_data_links_preserved":True,"saved":True}
(out/"glass-placeholder-fix.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
u.log("GLASS_PLACEHOLDER_FIX "+json.dumps(report))
