"""Targeted final lighting/water balance, without rebuilding geometry or flock."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v019';D='/Game/Environment/OvergrownHall/TripoFull';DEST=D+'/ReferenceFinish';MAP=D+'/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools();L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP);actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
source=(ROOT/'Content/Python/complete_hall_reference_finish.py').read_text()
exec(source[source.index('def make_material('):source.index('\nadded=[]')])
exec(source[source.index('# Camera faces'):source.index('# Replace some rounded')])
exec(source[source.index('# Broad reflective'):source.index('# Selective broad')])
assert L.save_current_level()
runpy.run_path(str(ROOT/'Content/Python/capture_hall_reference_finish.py'))
