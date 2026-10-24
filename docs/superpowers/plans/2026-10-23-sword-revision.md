# Sword acquisition requested revision — 2026-10-23

User-provided five corrections are the design: initial/reference shot cuts immediately; no camera move at 2–3s; QTE at approximately 4s; upper right/lower left grip with no right regrip; later camera preserves direction with slight dolly/upward motion; final gameplay camera is an immediate cut.

Implementation plan (writing-plans/executing-plans):
- Inspect installed graph and current timing. Test installed contract before modification.
- Keep B reference pose as initial shot, blend=0. Remove A and unused holds. Approach 3.3s plus short .7s beat yields QTE ~4s. Keep unlimited retry semantics.
- Use CameraMove on B, constant rotation, modest forward/upward displacement. No opposing-angle C switch. Remove CameraReturn and use existing End → StopDirector immediate camera restoration.
- Separate animation subtask produces preserved-source candidate with right-upper/left-lower grip. Drop RegripRight from runtime queue only when revised clips are ready; maintain matching extract/release/raise boundaries.
- Build once no Unreal/build active. Install backed-up assets, reload, assert runtime QTE time and stable early camera, camera direction and instant final return, grip continuity; validate real UI/unlock/input/toast. Background engine capture and hand/side samples.
- Preserve shared checkout and Intermediate. No automatic commits. Original source and production animation assets backed up; no desktop manipulation. User's concrete correction request authorizes these edits; no repeated design approval.

Inspection refinement: SceneDirectorPlayer::StopDirector already calls immediate SetViewTarget. Remove the explicit CameraReturn node and connect Commit → End to reuse that behavior; no new production camera-return option is needed. The initial schema RED result is retained as history, not the final contract. Read-only test helper observes actual remaining camera blend at handoff.

Completed 2026-10-23: source06 imported; installed contract and actual PIE passed. QTE onset3.933s; early fixed camera and instant gameplay return passed; scene rotation deviation0deg. Final38.433s/30fps video decoded. Source/engine joint visual review saved. User visual approval pending; physical swipe and audio excluded. Evidence: ArtSource/SwordAcquisition/AnimationIntegration_2026-10-23.txt.
