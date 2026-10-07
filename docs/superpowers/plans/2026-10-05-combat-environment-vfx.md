# Combat and Environment VFX Implementation Plan

Goal: Deliver approved stages 1-3: sword attack/hit/block/parry, slime attack/hit, glass break, running dust, cave ambience, with combat and scene playback.
Architecture: ConstellationVFX runtime plugin owns presentation, glass and cave actors. CombatRuntime owns confirmed-hit context and an optional presentation component. Existing authored VFX reused after inspection. Effects never apply damage.
Spec: Approved in-chat design and explicit unattended execution authorization, 2026-10-05.

## Constraints and rulings
- Work in current checkout because active combat/scene code is untracked; clean worktree would omit it. Snapshot modified files, preserve unrelated work, no broad commits.
- All three stages authorized; no further optional design questions.
- No stopping existing interactive apps; serialize builds/asset writes.
- Non-gory stylized effects. Block/parry presentation callable and demonstrated; do not invent unrequested gameplay block mechanics.
- Separate visual/runtime/performance validation; do not claim visual approval.

## Shared API
ConstellationVFX module. EConstellationFXKind enum: SwordHit, SwordBlock, SwordParry, SlimeAttack, SlimeHit, RunDust, GlassBreak, CaveDust, CaveMist, WaterDrop, WaterRipple, CaveSpore.
UConstellationFXLibrary::SpawnEffect(const UObject* WorldContext, EConstellationFXKind Kind, FVector Location, FVector Direction, FLinearColor Color, float Scale=1.f) returns AConstellationFXActor*.
UConstellationFXLibrary::StopEffectsForOwner(AActor* Owner).
Spawned actor supports SetOwner; auto lifetime bounded. Attack trail may use existing /Game/Constellation/VFX/NS_SwordTrail after validation.

## Task 1 shared effects/assets (root)
- [x] Inspect existing assets; add plugin, reusable effects, bounded actor lifecycle.
- [x] Author materials and review level with idempotent setup script.
- [x] Verify lifecycle and asset reload.

## Task 2 combat integration (delegated)
- [x] Preserve hit position/normal; confirmed event only after successful damage, never duplicate damage.
- [x] Opt-in CombatVFXComponent on CombatLabCharacter, real attack windows and cancellation.
- [x] Weapon-following sword trail, distinct slime attack/hit, grounded surface-aware foot dust.
- [x] Regression tests for miss/invulnerability/death/one-hit context and cancellation.

## Task 3 glass/cave/scene (root)
- [x] Breakable glass intact/broken states and collision, bounded shards, reset.
- [x] Local cave dust/mist/droplets/ripples/optional spores with distance limits.
- [x] Scene action adapter with abort/restart cleanup; inspect actual map placements.
- [x] Verify repeat break/reset and scene cancellation.

## Task 4 verification
- [x] Editor build, combat/scene/VFX tests.
- [x] Reload assets in fresh process; actual Unreal captures of combat, glass, dust and cave.
- [x] Simultaneous-effect performance measurement with limits stated.
- [x] Independent review and user documentation.

## Progress
All implementation tasks completed. Editor build succeeded. Final focused suite: 16/16 passed (Saved/Logs/VFX-final-scope-tests.log), including the concurrently updated EncounterSceneSignal test. Real first-use combat rendering passed after bounded offscreen resource warmup. Gallery, authored glass Chaos relay and cave captures inspected. Benchmark: RTX 4070, 1280x720, 92 effect actors/1196 instances, baseline 3.95ms, load 5.91ms mean/7.78ms p95. Independent review found no remaining confirmed P1/P2. Delivery guide: docs/2026-10-05-vfx-delivery.md. Existing unrelated work preserved; no commit or release package produced.
