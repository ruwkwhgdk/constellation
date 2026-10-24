"""Restore S0 references after replacement of its placed girl actor."""
import json
import shutil
from pathlib import Path
import unreal as u

root = Path(u.Paths.project_dir())
out = root / "Saved/SchoolBlackScreen_20261021"
out.mkdir(exist_ok=True)
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name() == "/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.AbandonedSchool"
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
girls = [a for a in actors if a.get_actor_label() == "S0_LittleGirl_Blocking"]
stages = [a for a in actors if isinstance(a, u.SchoolOpeningSceneActor)]
bindings = [a for a in actors if isinstance(a, u.SceneEventBinding)
            and a.get_editor_property("director")
            and a.get_editor_property("director").get_name() == "DA_S0_Opening"]
assert len(girls) == len(stages) == len(bindings) == 1
girl, stage, binding = girls[0], stages[0], bindings[0]
objects = dict(binding.get_editor_property("objects"))
assert len(objects) == 1 and str(next(iter(objects))).lower() == "girl"
key = next(iter(objects))
assert objects[key] is None and stage.get_editor_property("girl") is None
assert girl.get_component_by_class(u.SkeletalMeshComponent).get_skinned_asset()
backup = out / "AbandonedSchool.before.umap"
assert not backup.exists(), "Backup already exists; inspect before reapplying."
shutil.copy2(root / "Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap", backup)
with u.ScopedEditorTransaction("Restore S0 opening girl references"):
    binding.modify()
    stage.modify()
    objects[key] = girl
    binding.set_editor_property("objects", objects)
    stage.set_editor_property("girl", girl)
assert binding.get_editor_property("objects")[key] == stage.get_editor_property("girl") == girl
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(out / "fix.json").write_text(json.dumps({
    "girl": girl.get_path_name(), "binding": binding.get_path_name(),
    "stage": stage.get_path_name(), "saved": True,
    "changed_properties": ["SceneEventBinding_4.Objects.Girl", "SchoolOpeningSceneActor_0.Girl"]
}, indent=2), encoding="utf-8")
u.log("SCHOOL_BLACK_SCREEN_REFS_SAVED")
