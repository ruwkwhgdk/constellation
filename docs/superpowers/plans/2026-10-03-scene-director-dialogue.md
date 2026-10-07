# Scene Director dialogue scene implementation

Goal: Build the first complete conversation workflow approved by the user: bind an existing actor, enter cinematic mode, compose cameras, gaze/expression, dialogue/voice, switch shots, return to gameplay.
Architecture: Keep compiled fixed-time MovieScene tracks for transforms/animation/cameras. Add serialized timed cues for dialogue, expression, gaze and game control. Runtime player and editor preview share deterministic cue sampling; interactive dialogue pauses the runtime clock at its end until advance. Compile-time character layout is explicit; existing actor bindings are resolved at runtime via player pawn or unique actor tag and restored on exit.
Tech stack: Unreal 5.8 C++, MovieScene, Slate, native post-process animation instance.

Constraints: Preserve enum values and old assets. No external asset changes. No editing shared animation assets. Korean designer labels. Presets are reusable per-character data. No conditional branching, lipsync generation, quest effects or combat scope in this increment.

Tasks:
- [x] Append node data, character presets, timed cue serialization. Test old enum compatibility and validation.
- [x] Compiler: BindNPC preview spawnable/runtime override; CameraPreset target-relative pose; CameraSwitch camera blend track; collect cues, validate keys/actors/presets, reject dialogue overlaps. Test schedule/camera conflicts.
- [x] Runtime: resolve actor bindings before playback; controls/HUD snapshot restore; dialogue display and voice with click advance; deterministic expression and gaze sampling; cleanup on natural finish/stop/failure. Test pause boundary, replay, missing/duplicate bindings, restore and existing actors surviving.
- [x] Gaze driver: per-component native postprocess AnimInstance preserving input pose, clamped head aim with configurable bone/axis. Restore previous component override on release; reject conflicting existing postprocess rather than overwrite silently. Test component isolation and bone changes.
- [x] Editor: categorized menus and labels, NPC references/rename, profile editor, dialogue subtitle preview plus shared performance sampler, safe preview restore.
- [x] Example: own plugin demo actor/profile and graph if production rig lacks compatible face presets; explicit distinction from final heroine resources. Usage guide with one-time setup and limitations.
- [x] Verify automation, Editor/Shipping builds and rendered preview. Fresh code review before completion.

Review focus: click pauses must not fire later cues; multiple references to same live actor rejected; old HUD/input state must survive cancellation; backwards scrub must reconstruct expression/gaze; missing profile/bones/morphs must produce actionable errors, never silent success.

Verification record: 25 automation tests pass, including runtime binding/click boundary (1024 seconds)/reentry, expression sampling and restore, actual gaze bone pose/70-degree clamp/main-instance preservation. Editor and Shipping builds succeeded. Read-only review identified 3 issues (float boundary, reentry camera cuts, mixed-height over-shoulder); all fixed, covered by regressions, scoped rereview clean. RenderOffscreen editor preview and standalone game subtitle screen inspected. Generated conversation asset, standalone BP/profile and review map saved. Original character/animation assets untouched.

Implementation limits: head gaze only (no independent eyes); existing postprocess rigs require integration; heroine source contains zero face morphs, so example omits expression and needs authored face morphs for actual facial acting. No recorded voice provided. Existing actors use configured layout and restore position on stop. AHUD and movement/look locks are supported; project-specific UMG/AI/combat logic remains separate. No full cook/package play verification.