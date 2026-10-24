import unreal as u
from pathlib import Path
import shutil
root=Path(u.Paths.project_dir());out=root/'Saved/DialogueRestyle';out.mkdir(exist_ok=True)
f=root/'Content/Constellation/UI/Widgets/WBP_Dialogue.uasset';backup=out/'WBP_Dialogue.before.uasset'
if not backup.exists():shutil.copy2(f,backup)
b=u.load_asset('/Game/Constellation/UI/Widgets/WBP_Dialogue');atlas=u.load_asset('/Game/Constellation/UI/Dialogue/T_Dialogue_QuietNebulaAtlas');assert b and atlas
before=u.ResourceRecoveryLibrary.export_blueprint_graphs(b)
assert u.DialogueStyleEditorLibrary.apply_quiet_nebula(b,atlas) is not None
assert before==u.ResourceRecoveryLibrary.export_blueprint_graphs(b),'Dialogue behavior graph unexpectedly changed'
assert u.EditorAssetLibrary.save_loaded_asset(b,False)
u.log('LEGACY_DIALOGUE_RESTYLED_GRAPH_UNCHANGED')
