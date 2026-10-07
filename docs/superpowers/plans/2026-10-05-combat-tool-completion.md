# Constellation Combat Tool Completion Plan

> Execution: superpowers:executing-plans, inline. User explicitly authorized continuous work while away. Maintain this ledger between tasks; no per-task approval pause.
>
> Spec: docs/2026-10-04-combat-ai-direction.md plus the subsequent workbench, observation, input and dodge documents.

## Goal
Complete the designer-facing combat authoring/test workflow and its required runtime features: configurable player basic combo, dodge, skill and ultimate; monsters and multi-enemy encounter; reusable versioned creation/import/export; validation, manual play and diagnostics. Do not label numeric tuning alone as completion.

## Constraints and rulings
- Soulslike baseline with action-RPG skill/ultimate behavior. Preserve existing camera and 500 cm/s default player movement.
- No animation production. Reuse existing motions for functional tests and maintain animation requirements separately.
- Preserve source assets and unrelated workspace changes/processes. New generated content uses new IDs; no automatic overwrite or deletion.
- Work in this existing shared checkout: untracked combat code/assets and cross-task Unreal modules are prerequisites absent from a new Git worktree. Do not commit unrelated changes.
- Automated runtime correctness and human combat-feel approval are separate. Deliver tested tooling and clearly list the latter as handoff review, without claiming visual/feel approval.
- Single-player scope. Full online replication, arbitrary combat genre support and final production art are outside the approved first implementation scope.
- Read repository animation/environment workflow files before touching those maintained art sources; current combat work does not require doing so.
- Schema upgrades preserve explicitly supported older files; malformed/current-version missing fields remain failures.
- Completion is not a timer or a token target. Continue until the criteria are met or an actual external dependency prevents progress.

## Ordered deliverables
- [x] 1. Special-action foundation: skill/ultimate slots, separate ultimate charge, cost/cooldown/start-failure semantics, UI availability.
- [x] 2. Dash skill and area ultimate primitives: collision-aware action movement, occluded radial hits, cancellation/death cleanup. Reused animation samples and backlog.
- [x] 3. Complete action authoring: slots, motion references, timing/shape/movement/resource fields in validation and versioned import/export; source isolation; designer sample loadout.
- [x] 4. Multi-enemy control and encounter lifecycle: configurable attack concurrency, release on every interruption/death/return path, three-enemy test, reset/completion without duplicate outcomes.
- [x] 5. Encounter/monster creation workflow: template duplication and new version creation, editable configurations, validation and test-map launch without terminal commands. Preserve source assets.
- [x] 6. Persist play tuning as a reviewed new authored version: bridge runtime preset/report to generated assets with provenance and reload verification, not an untracked second source of truth.
- [x] 7. Authoring usability: search/select templates and targets, undo/redo of drafts, useful validation navigation, diagnostics/reproduction export; resizing and manual launcher.
- [x] 8. Integration boundary: test against existing project controls/interaction constraints and selected isolated battle-zone integration; packaging/reference check without replacing the main map blindly.
- [x] 9. End-to-end acceptance: author a second same-type monster plus three-enemy encounter without C++/BP changes, save/reload/play, test failure paths, performance/frame-rate smoke checks, fresh independent code review, final guide and animation handoff list.

## Task 1 implementation brief
Files: CombatAttributes.h/.cpp, CombatActionDefinition.h/.cpp, CombatAbilitySystem.h/.cpp; player slot input in CombatLabCharacter; workbench clone/signature/fields and HUD; dedicated tests alongside existing montage fixtures.
- Add clamped 0..100 ultimate charge as a single authoritative combat attribute, initially0.
- Actions declare charge cost and charge gained on successful damaging hits (default basic hit gain10; ultimate sample gain0). Capture values before callbacks.
- Gate insufficient charge before activation. Commit costs once; guard reentrant starts while multiple resource deductions are in flight. Failed preflight spends nothing.
- Add optional SkillAction/UltimateAction references and Q/E input. Empty slots report unavailable. Same shared action lifecycle/cooldown/hit logic; no parallel execution.
- Clone all slot actions through the same clone graph and include slot paths in source compatibility.
- Add HUD resource/availability and F1 tuning, migrate old preset versions only for known additions.
- Tests: resource limits, exact gain/cost, immune/zero/duplicate hits, rejected casts, cancellation/death/reentrant callbacks, input and preset isolation. Then real game configured sample.

## Ledger
2026-10-05: Baseline before this plan: full Editor build,40 CombatCore tests,1280x720 and1600x900 Save/Load game checks pass. Attack→dodge enabled only per action and default false; current preset schema3, report envelope1.
2026-10-05: Scope audit confirms missing skill/ultimate, multi-enemy/zone and authored-version creation bridge. Continuous work goal created; start task1.

Task1 progress: ultimate resource/cost/gain implemented;42 core tests PASS. Existing single-SP reentrant replacement behavior preserved; multi-resource ultimate commit blocks nested action/dodge until both costs settle. VFX build dependency resolved by its owning work; no VFX files changed here. Starting Q/E slot/clone tests.

Task1 progress: Q/E slot execution, isolated clone graph and schema4 resource fields implemented;44 core tests PASS. VFX hit-event additions retained alongside captured charge gain. HUD and explicit schema3 migration verification added next; sample loadout remains pending task2/3.

Task2 progress: action dash root motion with cancel/end cleanup and grounded preflight; radial overlap with per-target visibility obstruction, hit ledger and VFX event preservation. RadialOcclusion and ActionDashLifecycle RED→GREEN;46 tests PASS. Adding physical collision/frame-rate/death checks and schema4 workbench fields.

Task2 physical verification:47 core tests PASS including actual CharacterMovement collision at20/100Hz, equal free-space dash distance, cancellation and death source retirement. Task3 recipev2 parser:28 Python recipe/compare tests PASS; adds loadout, named action graph, montage/hit windows, stats and placements while retaining v1 contract.

Task1/2/3 sample: CombatTool_v1 generated and actual1600x900 Q/E viewport input, insufficient charge rejection, dash displacement and radial damage PASS; image reviewed. Task4: EncounterConcurrency/EncounterFailureCleanup RED→GREEN,50 core tests PASS. Task5 browser UI editing/undo-redo/search/validation/diff/layout PASS via headless Edge; native browser tool failed sandbox initialization. Multi-enemy CombatTool_v2 apply crashed in UnrealEd actor duplication after profile saves; preserved partial version, switching commandlet duplication to template-based World spawn (no GUnrealEd dependency). New v3 will validate recovery without overwrite.

Task3/4 authored integration: CombatTool_v3 successfully generated with3 enemies, Guard isolated HP220/Heavy28, player full loadout, native director limit1, full resolved snapshot and source manifest. Original v2 partial assets preserved. Pure Python suite38 PASS including tuning report source/key/number/individual override checks. Actual report→new version roundtrip pending.


## Final acceptance — 2026-10-05
All nine scoped deliverables implemented and verified. Kept existing shared checkout because generated/untracked project sources are prerequisites. No source animation production, main-map replacement, broad commit or unrelated process termination.

- Runtime: final full Editor build and52 CombatCore tests PASS. Skill/ultimate, cost/reentrant semantics, dash collision20/100Hz, radial obstruction/crowd, director concurrency/death/return, Carry gate, SceneEvent signal included.
- Python:42 tests PASS. Schema1 compatibility, schema2 graph/placement/stats/overrides, report provenance, individual tuning, partial version and missing snapshot rejection.
- Browser: editing/undo/redo/search/1280 layout PASS; damage-only enemy override preservation PASS; player movement field/error navigation/diagnostic download PASS. Report2edits→CombatTool_Tuned_v1 saved and built through UI.
- Fresh engine reload: CombatTool_v3 playerHP100/GuardHeavy28 and tunedHP117/Heavy31; both ScoutHP150/Heavy22 and GuardHP220,3enemies preserved. Evidence Saved/CombatAudit/authored-reload.json.
- Real viewport input: Q/E dash/insufficient charge/radial damage PASS at30FPS1280 and60FPS1600. Group30FPS:598samples,3distinct AI attackers,active<=1,damage,victory,Rrestart PASS.
- F1 old singleenemy1280 and new3enemy1600 Save/Load processes PASS: viewmode stable, changes/undo/report import, death open/close/restart, slow mode,input and dodge windows.
- Existing Carry/InteractionPrompt6tests PASS after bridge addition. Full standalone Development Game build PASS; two preexisting editor-only StringTable tests now use WITH_EDITOR guard, preserving their EditorContext coverage.
- Cook selected v3/Tuned maps PASS,1876packages,0errors. ReferencedSet confirms both maps.2 existing warnings: BP_Player_Heroine DodgeTimeline invalid curve; broad default GameplayCue scan. Neither prevented the isolated combat tool tests. Cook uses engine Zen output plus separate metadata folder; no distributable package claimed.
- Invalid resolved perenemy dodge interval, wrong montage skeleton and impossible cost rejected; validation preserves source asset hashes.

Independent final code review requested via requesting-code-review skill. Fixed both Important findings with red→green tests: damage-only override visibility/data loss and zero dodge distance. Also fixed direct launcher partial-version gating, perenemy resolved interval check, player speed form, incomplete snapshot pair. No unfixed Important findings. UI test initialHP100 assumption updated to the authored snapshot so tuned117 is tested correctly.

Completed guide: docs/2026-10-05-combat-author-guide.md. Animation requests updated only in docs/2026-10-04-combat-animation-backlog.md; existing motion reused. Final human feel/animation review, arbitrary new skeleton templates, multiplayer and migration of all main-map battle zones remain outside this tool completion scope.
