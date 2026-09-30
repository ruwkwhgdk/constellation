"""Reuse v020 final light recipe without touching saved vegetation or materials."""
import unreal as u,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level('/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull')
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
source=(ROOT/'Content/Python/refine_hall_light_foliage_water.py').read_text();exec(source[source.index('# Reduce competing'):source.index('# Remove selected')])
assert L.save_current_level()
runpy.run_path(str(ROOT/'Content/Python/capture_hall_atmosphere_finish.py'))
