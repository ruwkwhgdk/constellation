"""Import designer handoff unchanged as dedicated UI textures. No item data edits."""
import unreal as u
import traceback
import time
from pathlib import Path
r=Path(u.Paths.project_dir())
out=r/'Saved/ItemAcquisition'
try:
    folder='/Game/Constellation/UI/ItemAcquisition/RelicArt'
    source=r/'ArtSource/UI/ItemAcquisition/Production/2026-10-21'
    for file,name in [('relic-panel-frame-constellations.png','T_RelicPanel'),('relic-item-halo-stardust.png','T_RelicHalo'),('relic-title-divider.png','T_RelicDivider')]:
        task=u.AssetImportTask()
        task.filename=str(source/file);task.destination_path=folder;task.destination_name=name
        task.automated=True;task.replace_existing=True;task.save=True
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        asset=u.load_asset(folder+'/'+name)
        assert isinstance(asset,u.Texture2D),name
        for key,value in [('lod_group',u.TextureGroup.TEXTUREGROUP_UI),('compression_settings',u.TextureCompressionSettings.TC_EDITOR_ICON),('mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS),('srgb',True),('never_stream',True),('address_x',u.TextureAddress.TA_CLAMP),('address_y',u.TextureAddress.TA_CLAMP)]:
            asset.set_editor_property(key,value)
        assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
    (out/'relic-import-result.txt').write_text('Imported panel, halo, divider; original color and alpha preserved.',encoding='utf8')
except Exception:
    (out/'relic-import-error.txt').write_text(traceback.format_exc(),encoding='utf8')
finally:
    # Initial ExecCmds can run before editor-mode construction has completed.
    # Quit on a later tick, after startup callbacks and asset saves have drained.
    stop_at=time.monotonic()+5
    def finish(dt):
        if time.monotonic()<stop_at:return
        u.unregister_slate_post_tick_callback(handle)
        u.SystemLibrary.quit_editor()
    handle=u.register_slate_post_tick_callback(finish)
