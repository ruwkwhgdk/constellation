"""Save the visually selected in-memory trial, only if the source map is unchanged."""
import unreal as u,hashlib,json
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/RoutePass_20261017'
source=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
backup=O/'AbandonedSchool.before.umap'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(source)==digest(backup),'Maintained map changed externally; do not overwrite it.'
world=u.EditorLevelLibrary.get_editor_world()
assert world.get_path_name().startswith('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.')
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(O/'saved.json').write_text(json.dumps({'map':world.get_path_name(),'before_sha256':digest(backup),'after_sha256':digest(source)},indent=2))
u.log('S0_POLISH_SAVED')
