"""Create designer tables once and connect existing blueprints. Existing rows are preserved."""
import json
import shutil
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
out=root/'Saved/CarryReview/DataTables'
(out/'backups').mkdir(parents=True,exist_ok=True)
paths=['/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine',
       '/Game/Constellation/Environments/School/Blueprints/BP_School_Chair',
       '/Game/Constellation/Environments/School/Blueprints/BP_School_Desk',
       '/Game/Constellation/Gameplay/Interaction/Actors/BP_Holdable_TestBox']
for path in paths:
    disk=root/('Content/'+path.removeprefix('/Game/')+'.uasset')
    backup=out/'backups'/disk.name
    if not backup.exists(): shutil.copy2(disk,backup)
blueprints=[u.load_asset(p) for p in paths]
result=u.CarryEditorLibrary.create_carry_tables(*blueprints)
assert result.startswith('OK:'),result
folder='/Game/Constellation/Gameplay/Interaction/Data/'
for name in ('ST_CarryMessages','DT_CarrySettings','DT_HoldableItems'):
    assert u.EditorAssetLibrary.save_loaded_asset(u.load_asset(folder+name),False)
for bp in blueprints:
    u.BlueprintEditorLibrary.compile_blueprint(bp)
    assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
(out/'setup.json').write_text(json.dumps({'result':result,'folder':folder,'blueprints':paths},indent=2),encoding='utf-8')
u.log('CARRY_DATA_TABLES_SAVED '+result)
