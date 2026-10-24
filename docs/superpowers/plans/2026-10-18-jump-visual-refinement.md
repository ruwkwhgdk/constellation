# Jump acquisition visual refinement — 2026-10-18

Approved scope: camera, star scale/material, light clipping, shot transitions, production resource list. The reaching animation remains provisional at the user's explicit request.

- [x] Add editable low-energy response/fill lighting and disable cinematic motion blur; preserve cancellation cleanup.
- [x] Author a preview with heroine left / star right, eye-visible 3/4 face, smaller map star and dedicated post-UI framing.
- [x] Capture actual game shots/video; camera approval remains a user review step before final map framing save.
- [x] Document animation/VFX/audio deliverables and integration contracts.
- [x] One final review, build/PIE checks, release shared editor.

Ruling: use the shared checkout because this is the user's actual mapped event; no worktree conversion or unrelated commits. Do not touch Intermediate. Ruling: approved visual-first proposal allows changing the camera side from the earlier literal left-front-45 label. Preview must make that change clear. Ruling: pose and full production VFX are separate resources; this pass improves presentation and records their requirements rather than claiming placeholder animation is final.

Validation: build-visual1 succeeded; VisualCandidate01 real PIE completed with jump unlock/input restore; VisualLifecycle01 cancel/retry and all point-light intensities zero on cancellation/completion passed. MP4 decode passed. Final reviewer found fixed output-folder reuse; future visual review sessions now use timestamped directories.
Resource handoff: ArtSource/JumpAbility/Production/ResourceRequests_v02.txt (6 animations, 3 core VFX with material dependency, 3 audio cues; optional aura/confused loop).
User review: requested camera revision, not approved for final map/graph save. Awaiting shot/time and adjustment direction. commit-jump-visual-candidate.py is prepared but MUST NOT run until revised preview approval. Current map/graph retain previous saved framing; runtime light settings and motion-blur improvement are built, candidate material exists as a separate resource.

Camera revision v03 requested: initial blend becomes an instant cut; Reach handoff starts with Inspect push-in; Contact and Surprise hold Inspect framing; Absorb uses a 12% chest push from the same angle. Revised preview must be reviewed before map/graph save.

V03 validation: VisualCandidate_20261018_211446_699984 completed (638 frames), jump unlock/input restore passed, MP4 decode passed. Contact/Surprise camera positions identical; representative frames visually checked; small Absorb push verified. Editor released, map/graph not saved. Fresh capture lacks earlier startup hold, so matching beats occur at ~2s Reach, 6.5s Contact, 7.5s Surprise, 8.7s Absorb. Awaiting revised video approval.

User approved v03. Committed to actual map and graph in VisualCommit_20261018_212900, save calls succeeded and map reload verified star scale/material. Original map/graph backed up. Shared editor released. Arm animation and production VFX remain separate deliverables.
