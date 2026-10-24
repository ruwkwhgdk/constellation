import unreal as u
import json
from pathlib import Path

out = Path(u.Paths.project_dir()) / "Saved/SchoolBlackScreen_20261021"
out.mkdir(exist_ok=True)
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
rows = []
for actor in actors:
    if any(term in (actor.get_name() + actor.get_actor_label()).lower() for term in ("girl", "opening")):
        rows.append({
            "path": actor.get_path_name(), "label": actor.get_actor_label(),
            "class": actor.get_class().get_path_name(),
            "transform": str(actor.get_actor_transform()),
            "meshes": [{"component": c.get_name(), "mesh": str(c.get_skinned_asset())}
                       for c in actor.get_components_by_class(u.SkeletalMeshComponent)]
        })
asset = u.load_asset("/Game/SceneDirector/School/DA_S0_Opening")
rows.append({"objects": str(asset.get_editor_property("objects")),
             "bind_steps": [str(s) for s in asset.get_editor_property("steps")
                            if s.get_editor_property("type") == u.DirectorNodeType.BIND_NPC]})
(out / "audit.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
u.log("SCHOOL_BLACK_SCREEN_AUDIT_DONE")
