"""Run in PIE after the opening eye animation (about 20 seconds)."""
import json
from pathlib import Path
import unreal as u

out = Path(u.Paths.project_dir()) / "Saved/SchoolBlackScreen_20261021"
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
assert world
bindings = [b for b in u.GameplayStatics.get_all_actors_of_class(world, u.SceneEventBinding)
            if b.get_editor_property("director")
            and b.get_editor_property("director").get_name() == "DA_S0_Opening"]
assert len(bindings) == 1
binding = bindings[0]
stage = u.GameplayStatics.get_actor_of_class(world, u.SchoolOpeningSceneActor)
girl = stage.get_editor_property("girl")
assert girl and list(binding.get_editor_property("objects").values()) == [girl]
events = next(e for e in u.ObjectIterator(u.SceneEventSubsystem) if e.get_outer() == world)
runner = events.get_editor_property("active_player")
assert runner, binding.get_editor_property("status")
assert runner.has_started_eye_effect()
assert runner.get_eye_open() > .99, runner.get_eye_open()
assert runner.get_vision_blur() < .01
dialogue = str(runner.get_editor_property("current_dialogue"))
assert dialogue, "Opening must reach its first dialogue"
report = {
    "world": world.get_path_name(), "status": binding.get_editor_property("status"),
    "girl": girl.get_path_name(), "eye_open": runner.get_eye_open(),
    "vision_blur": runner.get_vision_blur(), "dialogue": dialogue,
    "passed": True
}
(out / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
u.SystemLibrary.execute_console_command(world, 'Shot SHOWUI -nosuffix filename="' + str(out / "fixed.png") + '"')
u.log("SCHOOL_BLACK_SCREEN_VERIFIED " + json.dumps(report, ensure_ascii=False))
