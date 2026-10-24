import unreal as u
from pathlib import Path
import shutil
root=Path(u.Paths.project_dir());out=root/'Saved/ChoiceRestyle';out.mkdir(exist_ok=True)
f=root/'Content/Constellation/UI/Widgets/WBP_Choice.uasset';backup=out/'WBP_Choice.before.uasset'
if not backup.exists():shutil.copy2(f,backup)
b=u.load_asset('/Game/Constellation/UI/Widgets/WBP_Choice');atlas=u.load_asset('/Game/Constellation/UI/Dialogue/T_Choice_StardustAtlas');assert b and atlas
before=u.ResourceRecoveryLibrary.export_blueprint_graphs(b)
assert u.DialogueStyleEditorLibrary.apply_stardust_choices(b) is not None
assert before==u.ResourceRecoveryLibrary.export_blueprint_graphs(b),'Choice behavior graph unexpectedly changed'
assert u.EditorAssetLibrary.save_loaded_asset(b,False)
u.log('LEGACY_CHOICE_RESTYLED_GRAPH_UNCHANGED')
