# S0 wet classroom quality refinement

Approved: execute the comparison plan in order; keep a slightly cleaner atmosphere than ApprovedConcept.png.

1. Read saved map, capture fixed concept-facing and player-height views, record preserved actor state. Test water shading and local lighting without saving the map.
2. Evaluate actual render. Apply the selected water/floor treatment throughout the existing floor; add restrained non-colliding peripheral rock transitions using existing cave resources.
3. Save, reopen, compare baseline transforms/meshes/collision and out-of-scope materials; capture final views and record visual/play/performance limits.

Constraints: maintain develop, no unrelated commits, no global lighting/material edits, no actor movement or gameplay/cinematic changes; no Intermediate cleanup, builds, or stopping existing user processes.

Ruling: this is environment look development. Actual same-view renders and saved-map invariants are the verification gates; implementation-mirroring unit tests are not useful for material appearance. Preserve current source map backup before changes.

Progress: baseline audit/capture started. Trial materials will be independent V2 assets; trial map changes are unsaved until visually reviewed.

## Trial findings
- Shadowless ceiling key caused weak furniture grounding. Trial restores shadows and reduces its intensity from 3.5 to 2.0, with warmer color.
- UE 5.8 DeleteAllMaterialExpressions can skip entries while removing from its iterated collection. Graph reset now deletes an explicit expression-list snapshot and asserts zero expressions remain.
- SingleLayerWater was tested with actual transmission. At 1.8 cm depth, engine SingleLayerWaterComposite.usf applies `saturate(DeltaDepth * 0.02)` to reflections, limiting thin-puddle reflection. Existing project also has GenerateMeshDistanceFields=0; local Lumen settings alone do not supply missing distance fields.
- Clear-coat inputs were not exposed by the Python MaterialProperty enum; selected trial instead uses Default Lit masked thin-film shading with world-projected substrate and local planar/SSR reflections. This is an approximation, not refractive water.
- Trial state saved to /Game/Constellation/Review/SchoolOpening/Maps/L_S0_WetPolish_Trial to release our editor for another authorized animation build. Maintained map hash remains unchanged.

## Selected pass
- Film4: muted wood, desaturated blue-gray thin film, broad irregular coverage, restrained animated normals, expanded cave-edge material blend.
- Ceiling key shadows restored, warm intensity reduced; three local fill lights reveal cave forms and reflected surfaces. Ten shallow non-colliding rock transitions reuse cave meshes.
- Guarded save completed after checking source map SHA against the backup. Fresh-process render and invariant verification follow.
- Review fixes: capture completion requires changed file modification time; removed alternate unguarded commit entry point. Only save-s0-wet-polish.py saves selected state.
- Validation scope is explicitly actor transforms/collision flags, mesh assignments, materials and recorded local lights. It does not prove gameplay, cinematics, component collision or performance correctness.
- Final reopened render: four fresh views inspected; no material compile failure or Python error in final log. Invariant comparison passed for 4,789 original actors. Thirteen scoped additions. Evidence copied to ArtSource/SchoolOpening/WetFloor/Polish. Visual pass complete for floor/water/local lighting; original wall detail and large rock silhouettes still differ from concept.
