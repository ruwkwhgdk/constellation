# Special Item Acquisition Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development. Shared checkout changes must remain narrowly scoped; only the parent builds and launches Unreal.

**Goal:** Explicitly invoked special-item cards using real project data, with queued presentation and safe input restoration.

**Architecture:** A project runtime presentation subsystem owns a FIFO and input snapshots. A native UMG/Slate widget displays a data-only presentation payload. Blueprint async invocation exposes completion/cancellation; SceneDirector may use its existing authored integration instead of a new duplicate inventory system. Never grant items from presentation.

**Tech Stack:** Unreal 5.8, C++, UMG/Slate, existing Texture2D and localized FText data.

**Spec:** ArtSource/UI/ItemAcquisition/Concepts/2026-10-21/implementation-handoff.txt

## Constraints
- Only explicit special acquisition calls. No automatic inventory listener or replacement of ordinary pickups.
- Navy clipped-corner card, gold border and corner stars, transparent exterior; real untinted sprite on left and wrapped name/description on right.
- Preserve aspect ratio and allow item-specific scale/offset. No fabricated item lore or inventory data.
- Appearance 0.5s, confirmation waits for a fresh press, exit fade. Restore input/cursor/focus on every terminal path. World continues ticking.
- FIFO cards; cancellation does not grant or revoke anything. Sound hooks may remain explicitly unconnected.
- No Intermediate cleanup, Clean/Rebuild, concurrent builds, unrelated asset edits, or unsolicited pushes.

## Tasks
- [x] Audit current item UI, item data, special acquisition callers and confirm input.
- [x] Implement data contract, explicit async queue, lifecycle/input management and tests.
- [x] Implement reusable card layout/resources, fitted sprite, wrapping and visual tests.
- [x] Connect an explicit game/authoring path using existing data without changing grant policy; document callable API.
- [x] Build and test FIFO/input/cancel/data invariants; actual coin sprite and long Korean verified in PIE. Tall/wide sprite geometry covered by native tests; final authored item art and hardware gamepad checks remain outside this fixture.

## Review focus
Held interaction entering confirmation; cancellation while queued; externally owned input lock; world teardown; very long localized text; UI display without any item grant side effects.

## Ledger
Approved design already supplied. Reuse shared checkout because approved assets and ongoing UI work are here; preserve all unrelated work. Audit must establish real data sources before populating examples.

2026-10-21 verification: final incremental build succeeded. ItemAcquisition's 5 native tests passed. Combined ItemAcquisition/SceneDirector run: 121/123 passed; ContextNodeCreation and ConversationNodes retain stale node/category count assertions (30 vs 31, 5 vs 6). SchoolVisualParity regression caused by broad GameAction clock clamp was corrected with an opt-in presentation boundary and now passes. PIE confirmed fresh input, FIFO, PageDown scrolling, cancellation, restoration of cursor/move/look state, and unchanged currency. Evidence under Saved/ItemAcquisition; authoring guide under ArtSource/UI/ItemAcquisition/implementation-guide.txt. Definition template deliberately has no invented names/descriptions. Optional AppearanceSound is unassigned.
