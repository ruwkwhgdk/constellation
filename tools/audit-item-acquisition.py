"""Read existing chest image assignments; never modifies assets or grants items."""
import unreal as u
import json, traceback
from pathlib import Path
out=Path(u.Paths.project_dir())/'Saved/ItemAcquisition'
out.mkdir(parents=True,exist_ok=True)
try:
    world=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
    rows=[]
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if 'Chest' not in actor.get_class().get_name():
            continue
        texture=actor.get_editor_property('Item')
        rows.append(dict(actor=actor.get_path_name(),texture=texture.get_path_name() if texture else None))
    (out/'existing-chest-images.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
    u.log('ITEM_ACQUISITION_AUDIT '+str(len(rows)))
except Exception:
    (out/'audit-error.txt').write_text(traceback.format_exc(),encoding='utf8')
finally:
    u.SystemLibrary.quit_editor()
