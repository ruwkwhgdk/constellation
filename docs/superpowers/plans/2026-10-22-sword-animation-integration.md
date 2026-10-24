# Sword animation integration

Scope: connect approved Final03 character delivery to existing sword event and record final background engine footage. Preserve source clips, mesh/rig/weights, other events, and shared build working files. Existing storyboard and latest user instruction authorize integration.

1. Inspect delivered sequences, sword tracks and production mesh pivot/scale. Run installed animation contract before implementation (expected missing AnimationSet).
2. Add a serialized animation/prop-track set and scoped stage playback. Preserve gameplay ABP. Use real loop sections, finish a requested loop at its matching boundary, synchronize actual sword to authored component-space track. Pause graph for one-shot clip queues; UI continues RaisedHoldLoop until confirmation. Restore original sword/animation/input on cancellation.
3. Install animation set and graph durations/cameras. Back up only changed packages, reload in owned hidden engine, verify QTE and UI waits longer than a full loop, cancellation/retry, all clips, final attack/input/toast. Inspect full/hand/side transitions and loop exits before final movie.
4. Fresh read-only code review, required fixes, final recorded evidence and handoff notes.

Shared-workspace ruling: retain existing shared checkout and installed scene; no worktree copy or automatic commits. No build while an engine/build is active. No Clean/Rebuild/Intermediate deletion. Test-owned Saved suffix isolates user saves. Review QTE outcomes injected internally, no desktop manipulation.

Quality gate: match delivered pose/hand grip, no large wrist/finger/knee snaps; approved source remains unchanged. Runtime loop exits are boundary-aligned (up to one 2.4s cycle), rather than unverified arbitrary-pose crossfades. Verify this timing in final footage. Input/ability/UI semantics of prior implementation remain in force.

Interfaces: animation set carries sequence + 30fps sword transform samples; stage uses the same montage time for body/prop. Graph cues pause until clip queue completes; QTE HOLD must not freeze the independent skeletal loop. UI pause must not freeze raised loop.

Completed 2026-10-22: all eight delivered clips and prop tracks installed; native build succeeded; fresh code review verification gaps fixed. Fixed-step PIE result (002003) passed cancellation/restoration, actual loop wraps, UI/commit/input/toast/attack checks. Installed contract and InputOwnership passed. Final 55.9s/30fps movie decoded successfully. Supplemental lit front/side/hand engine samples (003051) inspected; no newly introduced gross joint defect found in inspected samples. Physical swipe and exhaustive all-angle/per-frame visual certification remain outside this run. See ArtSource/SwordAcquisition/AnimationIntegration_2026-10-22.txt.
