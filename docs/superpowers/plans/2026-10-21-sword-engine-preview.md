# Sword acquisition temporary engine preview

**Goal:** Record an actual Scene Director camera/QTE blockout in the current AbandonedSchool map. User explicitly accepted missing-animation placeholders on 2026-10-21.
**Spec:** ArtSource/SwordAcquisition/Storyboard/2026-10-21-v01/Storyboard_Direction_v01.txt
**Architecture:** Standalone owned editor; load production map read-only, transient scene graph and table, existing player idle. No animation retarget/import or production map save. Scene Director executes cameras and upward unlimited QTE; recording annotates missing animation and item award integration.
**Tech stack:** Unreal 5.8 Python, SceneDirector, viewport capture, ffmpeg.

- [x] Inspect animation chat and saved map inventory. Only mannequin pull/recovery available; high raise/hold/lower not delivered. Notify animation chat of explicit production request.
- [x] Build transient graph with input/HUD locks, A/B/C camera beats, unlimited DirectionDrag Up, dialogue, camera return. Inspect actual runtime frames and adjust framing.
- [x] Capture actual engine frames with editor-only outcome injection per user's background-work preference. Physical pointer input remains untested.
- [x] Encode video, inspect sampled frames, record limitations and unchanged map hash. Owned editor exited.
- [x] Arrange follow-up for animation completion and approved-clip integration (hourly thread heartbeat).

Review focus: QTE UI/character visibility, framing, held pose headroom pending actual animation, input restoration. Required product fixes and incremental builds are recorded below.

Ruling: actual graph compile rejected QTE at SceneDirectorCompiler.cpp:49 because enum validation ended at StopCameraShake (33), while QTE is 34. Reproduced in EnginePreview02 and SwordPreview02.log. Scoped one-line bound fix and incremental 4-action build authorized as necessary to deliver requested QTE preview. No build competitors or Unreal editors present at start. Existing QTE regression suite will be run.

Ruling: QTE first actual paint crashed at SDirectorQTE.cpp:100 (Outline.Add(Outline[0]) TArray CheckAddress); copied first point to an external value before Add. Incremental build succeeded. EnginePreview06 then rendered QTE for an extended hold without crash, production map SHA unchanged. Native input tool repeatedly timed out capturing PIE window; requested user upward drag for EnginePreview07 rather than claim input success.

User steering: prefer engine MCP/background execution, avoid computer control. No Unreal MCP is currently available. Stop native UI/manual input workflow. Explicit editor-only PIE QTE outcome injection added for autonomous footage; physical swipe input remains UNTESTED. Tests are separated from footage because automation framework stops PIE when beginning tests.

Final temporary footage: Saved/SwordAcquisition/EnginePreview09/SwordAcquisition_EngineBlockout.mp4 (27.5 seconds). Result: no script error, map SHA unchanged, QTE SUCCESS, movement/look input restored. 250 capture requests, 249 files; 2 startup captures from the editor window excluded. QTE retirement effects intentionally skipped by review injection. PlayerLifecycle regression passed in SwordQTERegression.log; BranchPrefix passed in SwordPreview07.log. Incremental build succeeded.

Outstanding production scope: approved character animation, actual WBP_GetItem and item grant, attack unlock, toast, normal interaction and physical swipe/retry tests, production star removal/map integration. Star component hidden only in transient preview. Camera C still exposes existing development signage; polish after approved raised-pose framing. No claim of finished gameplay event.
