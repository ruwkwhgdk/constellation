# Stairwell kit implementation plan

> Execute inline with superpowers:executing-plans. User explicitly requested continuing the existing process for every remaining asset.

**Goal:** Produce the entire adopted 01–22 kit and preserve a repeatable production workflow, with a reviewable handoff.
**Architecture:** Keep approved references and original generated models immutable. Build dimension-sensitive modules from a shared specification when the selected route allows it, then export separate FBX/UCX assets. Track technical acceptance independently from human appearance approval.
**Tech Stack:** Blender5.2.1 via guarded launcher; Unreal5.8 Python commandlet; Tripo website only for new external generation.
**Spec:** ArtSource/Stairwell_Modular/PRODUCTION_PROCESS.md and Review/review_v001.md.

## Global constraints

120cm rail clearance; 15/30cm stair; 30cm floor pitch; 3mm grout; 4cm rail diameter; 25cm vertical rail spacing; 220cm headroom; door frame/leaf separation. Preserve the working project delivery and existing imported door assets. No new API credit consumption. No human appearance approval inferred from silence.

## Review focus

Mirrored rail interfaces must preserve tangent directions and vertical spacing. Tile boundaries must not stretch for narrower panels. UCX must not close door/corner openings. FBX import must measure centimeters correctly. Raw generated textures must not be mislabeled full PBR.

## Tasks

- [x] Standardize the established workflow in PRODUCTION_PROCESS.md, including actual failures observed with downloads, approximate face limits and UE Interchange.
- [x] Store an ID-complete production manifest with build route, dimensions, budget, and review state.
- [x] Produce floor/stair/wall/ceiling/beam/nosing/skirting family with shared sizes and materials; export UV and collision.
- [x] Produce rail family09–12/17–19 using consistent tube cross sections, bend tangents and independent horizontal/slope returns; measure join interfaces.
- [x] Preserve door pair and prepare the generated light for shared kit review, recording any unresolved source artifact.
- [x] Generate Blender gallery, close-up renders, per-asset metrics and assembly-fit checks.
- [x] Import remaining kit to an isolated Unreal review folder and create a gallery/assembly review map; verify actual imported bounds/material slots/collision.
- [x] Final independent implementation review, resolve consequential findings, publish review entry points and unresolved appearance items.

## Execution ledger

- Ruling: retain this project's existing ArtSource and Content delivery paths; do not move work to another checkout. This continues the user's already-imported project assets. Cost if wrong: user would need to copy generated binaries between checkouts.
- Ruling: user explicitly requested execution under the current workflow; do not add a separate plan-confirmation gate. The production route preference is asked asynchronously; human appearance review remains a real gate.
- Validation uses produced geometry and import metrics instead of mock tests duplicating Blender operations. Never claim successful geometry without a generated report and visual review.
- User selected hybrid route: precision modules in Blender, retain Tripo door and light. No new API/website generation or credit expenditure.
- Build complete: 22 adopted IDs / 31 mesh variants, 29 new FBX files plus 2 preserved door assets. Per-mesh budgets pass. Blender source gallery, 32 PNG renders and HTML index saved.
- Independent final review: kit_final_review identified inconsistent corner facing and inward brackets on one side; also required actual engine axis verification.
- Final fixed corner facing: corner_regression_before.log reproduced assertion on original inner corner. Corrected second-leg facing and overlapping outer core. geometry_verification.log now reports KIT_GEOMETRY_VERIFIED 31 / 12 rail variants. Rendered both corner variants for visual inspection.
- Final fixed imported scale: actual Unreal bounds exposed 1.8cm instead of 180cm. Exported explicit centimeter vertices; all 29 imported bounds and collision counts now match manifest.
- Final fixed assembly: assembly_regression_before.log exposed stair end X180 vs landing start X360. Actual Y reflection measured from imported bounds. Corrected landing/rail/light placements and mirrored Y only on near-side straight rails. Saved-map verification now passes stair/landing seam, lateral alignment, 120cm clearance and outward brackets on both sides.
- Unreal import: STAIRWELL_KIT_IMPORTED 29, engine commandlet exit0; 2 door assets reused unchanged. ReviewKit map saved. Material compilation error scan empty.
- Light 15: 2,869 triangles. Preserved Tripo body/textures, added 3mm upper cover and separate emissive tubes. 133 source boundary edges remain; not classified as watertight. Appearance still pending.
- Remaining gates: human appearance review (especially weathering and light underside), PIE movement/camera, full scene headroom and original-view recreation. No final-game-ready claim.
- No merge or commit performed: this is an in-place asset handoff. Git status hit LFS write restrictions; unrelated repository settings and content were not altered to work around it.
