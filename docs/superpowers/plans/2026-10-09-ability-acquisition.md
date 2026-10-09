# Ability Acquisition Implementation Plan

> Execute inline in the existing project checkout; the user approved the maintained mockup and requested implementation. Existing unrelated local edits must be preserved.

**Goal:** Display the approved mural acquisition sequence when Jump, Combat or Transform is newly unlocked, then return safely to gameplay.
**Architecture:** Export transparent visual layers from the approved canvas source. A native UMG widget renders these layers and localized text. A tickable world subsystem queues transitions from the existing Ac_Ability unlock function, reads its current flags before mutation, and captures/restores input and pause state. An editor installer inserts three idempotent hooks before existing setters; grant logic remains intact.
**Spec:** ArtSource/UI/AbilityAcquisition/README.md and mockup.html (user approved 2026-10-09).
**Tech:** UE 5.8 C++, UMG/Slate, editor Python, PNG/WAV assets.

## Constraints
- Alpha Jump > Beta Combat > Gamma Transform sizes. Four slots remain reserved.
- Existing description DataTable, no new gameplay ability or save format.
- 6.2s before fresh input, .7s exit, real-time animation while paused.
- Existing detailed stars, newest gold glow, brushed dormant spaces, title-only CrB labels.
- No map changes; only Ac_Ability graph hook asset is edited, with backup.

## Tasks
- [x] Export background, emblem, dormant/old/new star sprites and six line layers from approved canvas; import UI textures and temporary SFX into a dedicated asset folder.
- [x] Add data asset, widget, queue subsystem and pre-unlock Blueprint callable hook. Preserve existing input mode/focus and pause using an input preprocessor, without forcing GameOnly on exit.
- [x] Add tests for invalid/duplicate grants, noncontiguous masks, early/repeated input, queue advancement and timeline. Build Editor.
- [x] Install graph hooks after schema validation; compile and save only intended assets. Verify idempotence and descriptions from DataTable.
- [x] Run automation and a standalone Unreal visual review; preserve screenshots/logs and provide launch instructions.

## Review focus
- Duplicate grants / re-lock events must not replay UI.
- Already held input must not dismiss immediately.
- Non-sequential acquisitions must show actual booleans, not index counts.
- PIE end / map teardown must unregister global input processing and restore state.
- Missing art/data must fail without trapping player input.

## Decisions
Use the maintained local checkout, because approved art and necessary existing game integrations are uncommitted here. Do not move or reset unrelated user work. Source art is exported from code-native canvas layers rather than flattened screenshots, preserving individual star control.

## Completion evidence
Editor Development build succeeded. Both automation tests passed (Rules, InstalledBlueprint). Standalone 1920x1080 review passed presentation, dismissal, pause/input restoration and held movement clearing. Final reviewer input finding reproduced before FlushPressedKeys fix and passed after it. Python binding finding rejected using runtime str/None signature evidence; second invocation assertion added. Font uses engine composite fallback because Hylia Greek glyph mapping was incorrect. Shipping packaging and complete story playthrough remain outside this verification. See ArtSource/UI/AbilityAcquisition/UNREAL.md.
