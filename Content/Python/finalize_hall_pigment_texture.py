"""Normalize new generated texture build settings without rebuilding scene materials."""
import unreal as u,runpy
from pathlib import Path
tex=u.EditorAssetLibrary.load_asset('/Game/Environment/OvergrownHall/TripoFull/IllustratedTextures/T_OH_PaintedMineral')
assert tex
tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_DEFAULT)
tex.set_editor_property('compression_no_alpha',True)
tex.set_editor_property('never_stream',False)
assert u.EditorAssetLibrary.save_loaded_asset(tex,only_if_is_dirty=False)
runpy.run_path(str(Path(u.Paths.project_dir())/'Content/Python/capture_hall_pigment.py'))
