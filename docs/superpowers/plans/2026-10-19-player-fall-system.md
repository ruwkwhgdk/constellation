# Player fall system implementation plan

Goal: Implement the approved airborne tracking, height-based landing damage and recovery input lock; animations/VFX/death remain deferred.
Architecture: Native PlayerFallComponent on BP_Player_Heroine, pure FallMath policy, existing CarryInputLibrary action routing and SteepSlopeMovementComponent safeguards. Use legacy Ac_Stats health with explicit environmental damage, no defense or death callbacks.
Spec: User-approved chat specification, 2026-10-19. H=160cm configurable; 1H/3H/6H/12H thresholds; weak 5–10%, strong 10–100% of max HP; never reduce HP below 1 or resurrect dead actors.
Constraints: Preserve unrelated shared-checkout changes. No Clean/Rebuild or deleting Intermediate. Only incremental build when no other build is active. No animation assets modified.

- [x] Test and implement pure classification, interpolation, peak tracking, consume-once landing and nonlethal health arithmetic in FallMath.h / Tests/FallMathTests.cpp.
- [x] Implement PlayerFallComponent with configurable recovery timers and generation-tagged animation-completion hook, movement delegates, teleport/mode/owner cleanup, HUD notification and health-changed event.
- [x] Gate existing input router and movement/jump paths. Preserve other owners' input locks and permit release events and camera input.
- [x] Install only on heroine BP through a repeatable editor script; save and reload verify latest assets.
- [x] Run native math tests, incremental Unreal build and targeted engine automation for landing lifecycle, actual collision landing, health floor, duplicate landing, cancellation, controller lock ownership and authored player installation.

Review focus: low ledges; peak above starting point; already-dead/low HP; interruptions/teleports/controller replacement; preexisting scene locks. Add assertions for each. Defaults chosen: temporary recoveries .2/.45/.8 seconds, no recovery below 1H; external cinematic/input locks suppress tracking. Animation integration exposes landing id and FinishLanding(id) with watchdog fallback.

## Delivery and validation
- Installed PlayerFall on the current BP_Player_Heroine; backup is Saved/FallSystem/install-20261019-040602/BP_Player_Heroine.uasset. No animation asset changes.
- Final incremental editor build succeeded. Native math regression: zero failures.
- Saved/FallSystem/tests3.log: all 7 requested tests passed (Fall Lifecycle, Cancellation, PhysicalLanding; 3 Carry regressions; StarlightHUD ResourcesAndFeedback).
- Physical collision test: 1498.97cm drop, Strong tier, HP 300 -> 118.414249, recovery lock active. Movement used actual capsule collision against a floor.
- Saved/FallSystem/asset-verified.json: fresh process spawned saved heroine with native movement component and verified all damage tiers.
- Independent code review findings fixed: attack release cannot commit a carry throw during recovery; native cinematic mode cancels tracking/recovery even without movement suppression.
- Temporary recovery durations .2/.45/.8 seconds are implementation defaults, editable on heroine PlayerFall component. Falls below 1H have no lock. Camera remains usable. Damage ignores defense; only damaging landings abort carried-object handling.
- Future animation hookup: poll State for airborne loop; OnLanding provides result and LandingId. On successful montage start call SetLandingRecoveryDuration(id, montage duration plus safety margin), then FinishLanding(id) on completion/interruption. Timeout is finite (max 30s). Obsolete ids cannot unlock later landings. Use SetFallSuspended for custom scripted movement, ResetFall for external discontinuities not using engine teleport.
- Death is intentionally not connected: actual damage always leaves HP1 and never heals an already-dead actor. Animation/VFX/camera shake and full rendered gameplay feel remain unverified/deferred as requested.
- No commits, unrelated modifications, Clean/Rebuild, or Intermediate cleanup performed.

## Height tuning revision
User playtest requested doubled ranges: <2H, 2–6H, 6–12H, >=12H. Updated native defaults, saved heroine component and boundary/physical tests. Maximum damage height is doubled to 24H. Damage ratios, HP1 floor and recovery durations remain unchanged.
