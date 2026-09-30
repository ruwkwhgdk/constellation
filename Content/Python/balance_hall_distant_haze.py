"""Final backdrop-only calibration at the maintained fixed exposure."""
import unreal as u,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());D='/Game/Constellation/Environments/OvergrownHall/TripoFull';DEST=D+'/PainterlyFinish'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull')
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
source=(ROOT/'Content/Python/refine_hall_painterly_finish.py').read_text()
exec(source[source.index('def make_material('):source.index('\nadded=[]')])
exec(source[source.index("m=make_material('M_OH_DistantHaze')"):source.index("\nplace('DistantHaze'")])
runpy.run_path(str(ROOT/'Content/Python/capture_hall_painterly_finish.py'))
