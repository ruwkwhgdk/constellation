# Project logic audit and repair

> **For agentic workers:** Execute inline using systematic-debugging and verification-before-completion.

**Goal:** Inventory project Blueprints and native gameplay code, repair demonstrated defects, and preserve reproducible evidence and remaining limitations.

**Architecture:** Preserve public Blueprint interfaces and asset paths. Verify native changes with Unreal automation and project Blueprints with the engine compiler. Use an isolated save slot for tests. The user closed the interactive editor to permit asset saves.

**Tech Stack:** Unreal Engine 5.8, C++, Blueprint, Python, PowerShell.

**Spec:** User request of 2026-10-01 to inspect and repair structural/logical errors throughout project code and Blueprints.

## Constraints

- Preserve unrelated `.claude/` files and existing asset work.
- Do not run gameplay tests against the player's save slot.
- Do not change character animation or environment art without reading their maintained workflows.
- Distinguish compiler success, static graph inspection, and actual play validation.

## Audit checklist

- [x] Inventory runtime source, editor plugin, configuration, existing tests, and working tree.
- [x] Compile and inventory project Blueprints, including graph and level-script coverage; the existing showcase level-script compile error is fixed.
- [x] Reproduce save interleaving, missing inner-progress persistence, and missing currency persistence using isolated saves.
- [x] Repair confirmed persistence defects; new field defaults to zero. Actual legacy save migration remains untested.
- [x] Check quest transitions, delegate reentrancy, UI lifecycle/projection, movement numerics, and streamed travel; record limits of gameplay verification.
- [x] Run native automation, existing Python/C++ tests, and project Blueprint compiler.
- [x] Record reviewed scope, concrete repairs, and unverified scenarios in docs/project-logic-audit-2026-10-01.md.
- [x] Apply and reload-verify four Blueprint repairs after the user closed the editor.
- [x] Resolve obsolete showcase level-script call and confirm all 27 maps compile or have no level script.
- [x] Investigate missing dodge curve in eight autosaves. User explicitly deferred dodge changes.
- [ ] Complete actual viewport/gameplay validation; not covered by compiler and automation checks.

## Review focus

1. Alternating currency and quest saves must retain both systems' newest data.
2. Reloading an inner objective must retain its exact counter.
3. Blueprint event callbacks may mutate quest maps while delegates execute.
4. Camera-behind targets must produce finite, directional marker positions.
5. Zero sampling counts, zero grace durations, and large positive increments must not yield NaN, division by zero, or signed overflow.
