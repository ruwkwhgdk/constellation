"""Create presentation-only authoring assets; never touch pickup/grant graphs."""
import unreal as u
import traceback
from pathlib import Path
out=Path(u.Paths.project_dir())/'Saved/ItemAcquisition'
out.mkdir(parents=True,exist_ok=True)
try:
    tools=u.AssetToolsHelpers.get_asset_tools()
    folder='/Game/Constellation/UI/ItemAcquisition'
    path=folder+'/DA_ItemPresentation_Template'
    definition=u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else None
    if not definition:
        factory=u.DataAssetFactory()
        factory.set_editor_property('data_asset_class',u.ItemAcquisitionDefinition)
        definition=tools.create_asset('DA_ItemPresentation_Template',folder,u.ItemAcquisitionDefinition,factory)
        p=definition.get_editor_property('presentation')
        p.set_editor_property('sprite',u.load_asset('/Game/Constellation/UI/Art/coin_icon'))
        # Existing chest sprite is real; no invented names or descriptions.
        definition.set_editor_property('presentation',p)
        assert u.EditorAssetLibrary.save_loaded_asset(definition,False)
    actionpath=folder+'/BP_ShowSpecialItem'
    if not u.EditorAssetLibrary.does_asset_exist(actionpath):
        factory=u.BlueprintFactory()
        factory.set_editor_property('parent_class',u.ItemAcquisitionSceneAction)
        bp=tools.create_asset('BP_ShowSpecialItem',folder,None,factory)
        cdo=u.get_default_object(bp.generated_class())
        cdo.set_editor_property('definition',definition)
        assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
    (out/'setup-result.txt').write_text('Created reusable presentation template and SceneDirector action. Name/description intentionally blank; author before use. No grant or pickup graph changes.',encoding='utf8')
except Exception:
    (out/'setup-error.txt').write_text(traceback.format_exc(),encoding='utf8')
finally:
    u.SystemLibrary.quit_editor()
