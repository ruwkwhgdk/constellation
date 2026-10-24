"""Compile/save the existing tracker child, preserving the HUD's creation path and refresh graph."""
import unreal as u
import json, shutil
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'Saved/QuestTracker';out.mkdir(parents=True,exist_ok=True)
path='/Game/Constellation/UI/Widgets/WBP_QuestTracker'
src=root/'Content/Constellation/UI/Widgets/WBP_QuestTracker.uasset'
backup=out/'WBP_QuestTracker-before.uasset'
if not backup.exists():shutil.copy2(src,backup)
bp=u.load_asset(path);assert bp
before=u.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
u.BlueprintEditorLibrary.compile_blueprint(bp)
after=u.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
assert 'OnTrackerRefreshed' in after
assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
(out/'WBP_QuestTracker-after.txt').write_text(after,encoding='utf8')
(out/'apply.json').write_text(json.dumps({'asset':path,'backup':str(backup),'refresh_event_retained':True,'graph_unchanged':before==after},indent=2),encoding='utf8')
u.log('QUEST_TRACKER_APPLIED')
