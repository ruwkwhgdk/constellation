"""Read-only inventory of the maintained school's starting room."""
import json
from pathlib import Path
import unreal as u

out = Path(u.Paths.project_dir()) / 'Saved/PickupTutorial'
out.mkdir(parents=True, exist_ok=True)
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
rows = []
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    p = a.get_actor_location()
    if -500 < p.x < 4000 and -2000 < p.y < 2000 and -500 < p.z < 1000:
        center, extent = a.get_actor_bounds(False)
        rows.append(dict(name=a.get_name(), label=a.get_actor_label(), cls=a.get_class().get_name(),
                         location=[p.x,p.y,p.z], extent=[extent.x,extent.y,extent.z]))
(out/'room.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
u.log('PICKUP_ROOM_AUDIT '+str(len(rows)))
