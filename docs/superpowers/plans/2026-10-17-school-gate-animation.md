# School Gate Animation Implementation Plan

> Execute inline using executing-plans; shared checkout, no cleanup or competing builds.

Goal: approved Candidate12 6.5-second animation drives BP_School_Gate, synchronized creak SFX, reliable player control restoration.
Architecture: gate-owned runtime component starts from Interact, drives leaf rotation from montage position, owns only its input locks/audio. Preserve parent interaction bookkeeping and disable legacy door timelines. Use separate animation/SFX assets. Preserve map geometry and existing scene work.
Tech: Unreal 5.8 C++, Blueprint editor helper, Python animation data controller, Blender export.

- [x] Export approved 94-bone poses and fixed morph values; export in-place motion and drive 65cm capsule travel; legacy root scale100 makes direct root-motion export invalid.
- [x] Add regression test for two-effort door curve and completion timing; baseline missing-component assertion recorded; native timing test executed successfully after implementation.
- [x] Implement gate runtime start/tick/cleanup, input lock balance, interrupted playback and owner destruction cleanup.
- [x] Install on BP_School_Gate without changing map transforms; preserve parent interaction event.
- [x] Add original metallic creak audio, two effort envelopes and finish clunk, spatial attenuation.
- [x] Incremental build with no competing build and separate validation processes; import/verify assets.
- [x] Actual PIE: input trigger, sync angle at key times, animation finish, movement input restoration, interruption and repeat guard. Capture video with audio.
- [x] Record verified scope and all limitations.

Evidence: GateOpen01/Unreal01/build6.log, timing_test.log, Run09/runtime.json, Run11_Interrupted/runtime.json, Delivery/video_audit.json. No packaged-build claim.
