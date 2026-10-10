# Wake vision implementation plan

> Execute inline using superpowers:executing-plans; final fresh review.

Goal: approved 4-second S0 waking performance, two blinks then full opening, blurred white haze fading to normal; reusable editor nodes.
Architecture: append Eyelids, Vision, ClearVision node types; deterministic cue evaluation shared by runtime and editor. Slate background blur below dialogue plus haze and curved feathered eyelids; never change camera or level postprocess. Sequence time drives effects, so pause and reverse scrub are deterministic. Stop removes session overlay.
Spec: user's approved in-chat design immediately preceding implementation request.

Constraints: retain existing uncommitted work in current checkout; backup touched files/assets; no blanket commit. Existing live assets unavailable from HEAD, so current checkout is necessary. User already approved execution; proceed without another planning approval.

- [x] Task 1: reflection contract test fails for missing node types. Build editor and run Constellation.SceneDirector.Vision.Contract. Add data types in SceneDirectorAsset.h, pure evaluator SceneDirectorVision.h/.cpp, scheduling/validation/conflict support in compiler, names/menu, shared SDirectorVision widget. Add tests for default blink checkpoints, reverse seek, reset, concurrent channels, overlap rejection and invalid values.
- [x] Task 2: runtime Player owns vision overlay, initializes before first visible frame and removes on stop; editor Viewport overlays same widget below dialogue. S0 bootstrap mask hands off when common eye node actually starts. Tests inspect current state and cancellation/retry cleanup.
- [x] Task 3: targeted saved DA migration replaces only OpenEyes + its wait at intro with parallel Eyelids/Vision and join. Back up DA and map before edit; preserve existing later cues and branching. Run actual-map PIE with early eye-state samples, both investigation orders and cancel during effects. Capture rendered intermediate states and verify visuals.
- [x] Task 4: full SceneDirector tests, fresh scoped review, docs, final report with real captures and limitations.

Review focus: pause/seek; simultaneous same-channel writes; initial exposure; cancel/restart cleanup; low frame rate and resolution. Tests cover pure evaluation and schedules, PIE covers session lifetime and scene regression. Slate renderer requires rendered captures, not only numeric checks.

Execution notes: reflection contract RED confirmed in red-tests.log; compiler node-range omission caught by schedule test and corrected. Independent review corrected ordered same-frame ClearVision handling and delayed bootstrap handoff. Build review-build.log succeeded; all 87 SceneDirector tests passed in final-tests-console.log. S0 graph saved via authoring API with GUID value comparisons; existing IDs and edges retained. First rendered PIE passed both investigation orders (2 blink cycles each); cancellation test was corrected because SceneEventSubsystem destroys its runner immediately, making reflected getter return values invalid. Final PIE now checks active state, input restoration and a rendered cancel frame. Only the DA changed; map backup was unnecessary as no map edits were made.

Final verification: 87/87 automated tests PASS; final PIE two investigation orders both record 2 blink cycles and blur .8438 maximum, all effects zero at choices, normal handoff passes. Cancel during first blink destroys runner, clears stage ownership and restores input. Additional delayed cancel capture after existing level fade shows normal sharp gameplay without eyelids/haze. Logs: Saved/WakeVision/pie-final.log and cancel-visual.log. Screenshots: Saved/S0Opening/S0_Wake_FirstBlink.png, S0_Wake_SecondBlink.png, S0_Wake_Recovery.png, S0_Wake_Cancel.png. No packaged-platform/low-quality Slate renderer performance claim.
