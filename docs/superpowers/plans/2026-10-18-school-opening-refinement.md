# Starting classroom concept refinement implementation plan

Goal: improve the approved wet classroom while keeping player routes clear and preserving V12/V13 performance gains.
Architecture: current AbandonedSchool only; isolated asset variants, exact mutation manifests, latest-map hash checks before save. Shared editor/build access is sequential. Do not run historical regeneration scripts.
Tech: UE5.8 Python, existing CarryEditorLibrary PIE helpers, GeometryScript; Blender only through guarded project launcher if needed.

- [ ] 1. Test both ramps with the saved player in PIE: uphill/downhill, endpoint contact, camera. Record route coordinates and failures. Fix only demonstrated route defects before art changes.
- [ ] 2. Rebuild cave side silhouettes with protected playable surfaces; no rocks/vegetation on ramps. Compare actual concept and player cameras.
- [ ] 3. Improve upper-platform thickness and junctions, keeping gameplay geometry fixed.
- [ ] 4. Refine focus/depth with existing lights before adding new shadow casters. GPU compare against maintained baseline.
- [ ] 5. Refine window glass and frames without emissive blue slabs.
- [ ] 6. Refine water/wood boundaries, maintain broad shallow water and reflections.
- [ ] 7. Place dampness/moss along structural seams, reduce repeated blotches.
- [ ] 8. Refine furniture materials and controlled variation, avoid cluttering paths.
- [ ] 9. Add restrained local detail only outside protected routes.
- [ ] 10. Fresh map reload, final actual-player tests, screenshots and GPU sampling. Report remaining limitations separately.

User authorized continuing in order without repeated approval. No Git operations or unrelated gameplay/BP edits. Other chat owns jump acquisition work.

## 2026-10-18 route review checkpoint

- Actual PIE pawn: BP_Player_Heroine; capsule radius 34 cm, half-height 88 cm; max step 45 cm and walkable angle 45 degrees.
- Read-only surface sampling found one lower-ramp facet around (3000,-1200,13.2) at 53.31 degrees. This is a candidate for traversal testing, not a confirmed obstruction.
- Initial movement automation failed before producing valid traversal results due to Python callback namespace. Fixed the pawn binding and prepared six uphill/downhill paths, including the lower-ramp edge.
- Arrival checks now include height; endpoint capture waits before teleporting to the next route.
- Actual walking and player-camera review remain pending. No map or asset was changed in this phase.
- Shared editor/build is reserved by jump-acquisition work according to Saved/JumpAcquisition/coordination.txt. Wait for explicit release, then load the latest map and record a fresh baseline before proceeding. Do not start a competing editor or build.

## Route test result — 2026-10-18 20:55 KST

Fresh PIE used the latest AbandonedSchool after JumpAcquisition release. Six actual CharacterMovement paths reached endpoints: lower center uphill/downhill, lower edge uphill/downhill, upper uphill/downhill. Initial spawn teleport only; subsequent movement used add_movement_input. Completion tolerance: 45 cm horizontally and vertically. Upper descent stopped on the ramp shoulder 33.45 cm above nominal destination height; this meets tolerance but is not an exact landing-center test.

Initial captures were controlled by the opening cinematic. They are not camera evidence. Stopped SceneDirector only in the transient PIE session, restored pawn view target, and repeated all six paths. Valid endpoint screenshots and trajectory JSON: Saved/S0WetFloor/PlayRoute_20261018/Retry02/PlayerCamera/. Endpoint views reviewed; continuous-camera clipping and normal input/interaction behavior remain unverified. The test forces movement input and does not validate input gating.

No map or asset changes. No shape fix is justified by the sampled 53.31-degree facet: the tested edge path traversed it. Own editor exited 20:54:41; shared editor/build access released for the other chat's authorized follow-up. Next: complete continuous camera review, then protected cave-side geometry and platform junction work.

## Ledge candidate review — 2026-10-18 21:12 KST

Prepared and executed tools/preview-s0-ledge-depth.py in a fresh exclusive editor. Seven existing non-colliding fascia actors were scaled downward while preserving world top heights and XY bounds. Baseline and candidate captured at three fixed viewpoints in Saved/S0WetFloor/LedgeDepth_20261018.

REJECTED: increased vertical scale exaggerates open edges and stretched faces. Restored transforms in memory, quit without saving. Original map SHA verified unchanged: F3044B4EFE43394CE1EC51D20762F8252BA301471A5A2E3A5BDA03CE2D425035. This is an evaluated candidate, not a completed visual improvement. Next iteration needs dedicated closed underside geometry rather than stretching the rock-wall mesh. Route geometry remains unchanged. Editor released for pending jump-camera review.

## Closed underside saved — 2026-10-18

Step 3 partial implementation: seven fascia meshes replaced by three closed underside variants, same XY bounds/top heights, collision still disabled. Fresh reload and four-view render completed. Verification: Saved/S0WetFloor/ClosedLedge_20261018/verification.json. 4,847 other actors and lights preserved. Step 2 main cave silhouette remains pending, along with continuous player-camera review and post-change GPU/PIE checks. Do not mark all stages complete.

## 2026-10-18 post-change validation

Fixed-view GPU paired comparison complete (old11.05ms/new11.17–11.21ms). Post-ledge traversal and sampled player-camera review completed. Full upper approach exposed existing blocking furniture; six props relocated aside and saved, reload positions and new-process uphill/downhill PIE passed. See WetFloor README and RouteValidation. Wall-side y=-2500 is not a walk route; use the verified central y=-2300 approach. Main cave silhouette and later art stages remain open.

## 2026-10-18 side facets checkpoint

Step 2 partial: V14 side-facet variants saved for 14 existing rock actors. Three-view comparison selected 17-degree normals. Upper vertex positions and original collision asset preserved; 4,840 unrelated actors plus lights unchanged on fresh reload, four editor screenshots captured. Improvement is subtle, major rounded masses remain an art limitation. No new route decoration or reflection cost settings. V14 actual-player and GPU follow-up pending; previous tests are not current-version performance evidence. See WetFloor/SideFacets and Saved/S0WetFloor/SideFacets_20261018. Own final editor PID21592 exited22:39:27.

## 2026-10-18 V14 validated checkpoint

Fresh saved V14: six uphill/downhill routes pass, six midpoint camera views reviewed. Forced movement and transient cinematic stop; normal input/continuous camera not validated. Fixed-view paired GPU retry old13.4152ms versus new13.3482/repeat13.1301ms; no detected regression, not a proven speedup or game FPS result. First malformed CSV excluded, retry adds10-second finalize pause. Evidence linked in WetFloor README. Map SHA unchanged33fddf6aedd7a81656ad5969dbe3f1bb2497d59852c1dbe355d72bed6ab2c22a. Next: upper route soft-light readability and platform material continuity, with larger silhouette work still open.

## 2026-10-18 V15 upper finish checkpoint

Steps3/4 partial: two upper platforms now use dedicated dry wood material aligned with lower floor scale; existing shadowless ceiling fill moved toward upper ramp and35→40cd. Three-view candidate reviewed, saved/reloaded with four captures. 4,851 other actors unchanged; meshes/collision and other lights preserved. V15 fresh PIE/GPU not rerun. See UpperFinish/verification.json and WetFloor README. Next: saved-map player-lighting view and GPU check, then opaque blue windows and remaining structural/material seams.

## 2026-10-18 V15 tests / V16 windows checkpoint

V15 six paths passed; upper midpoint player views confirm improved readability. Paired GPU old12.89335/new12.8576/repeat12.8381ms, essentially unchanged. Step5 partial: five lower broken window infills use subdued opaque gray-green glass variation; no exterior transmission. V16 saved/reloaded with four views, 4,849 unrelated actors and all transforms/meshes/collision/lights unchanged. V16 separate GPU/play not run. Remaining upper blue windows and main silhouette still pending. See WetFloor README for sources and hashes.

## 2026-10-19 geometry trial review

Step2 still open. Two rear-wall boulder radial-remesh candidates rejected: regular facets artificial, asymmetric version insufficient wall integration. Maintained map unchanged (V16). Dedicated layered wall-integrated geometry needed; see WetFloor README and RockJunction rejected.json. No candidate traversal or performance claims.

## 2026-10-19 authored rock trial
Two closed layered buttresses authored/reopened (1050/1106 tris), imported and reviewed in three placements. Not adopted: wall contact improved but terraces/material stretching unacceptable. No map save, V16 hash retained. Step2 remains open. Next: measure wall face first, build shallow geometry at intended depth with matched UVs. See WetFloor/LayeredBackRock/REVIEW.md.

## 2026-10-19 shallow rock checkpoint
Two shallow closed meshes authored/reopened1870tris each. Corrected junction diagnosis: floor22 vertical infill face y2000, structural wall y2800. Existing rock shader world-triplanar; UV stretching diagnosis unproven. UE y2000 candidate removes infill intersections. Dedicated normal-blend preview script property error corrected but not rerun; editor released for requested gameplay integration. Map unchanged, Step2 remains pending. See ShallowRock/STATUS.md.

## 2026-10-19 V18 adopted material-only refinement
Shallow authored geometry rejected: slab-like silhouette. Instead dedicated normal blend on original two rear rocks adopted. Fresh map reload verifies2material overrides only,4852otheractors unchanged and all meshes/transforms/collision/lights unchanged. Latest Jump animation integration retained. MapSHA3d2465069ef4abfdd43cf2e6120f4b32e9de036e837b2b9048f60b69be00d127. Four final views captured; no new PIE/GPU run. Large silhouette integration still pending; source/captures WetFloor/OriginalNormal.

## 2026-10-19 V19 upper windows checkpoint
Step5 partial: 26 upper window backing material overrides saved/reloaded, subdued gray-blue finish. All transforms/meshes/collision/lights and 4828 unrelated actors unchanged. Four final captures in WetFloor/UpperWindows. Lower windows/main door unchanged. No fresh PIE/GPU measurement. Main cave silhouette and final integrated validation remain open; do not mark all stages complete.

## 2026-10-19 traversal and V20 window continuity
V19 six saved-map forced-movement routes pass. Midpoint lower/upper uphill images reviewed. They reveal remaining blue z600 backing outside V19 scope. V20 applies existing gray-blue backing material to remaining14 actors; fresh reload4840 other actors and all transforms/meshes/collision/lights preserved. Two final editor views retained in WetFloor/LowerBacking. No post-V20 PIE/GPU measurement. Main cave silhouette and integrated performance remain open.

## 2026-10-19 V20 performance diagnosis
Fixed-view five-condition GPU isolation: planar reflection contributes ~1.93ms to10.71ms baseline; screen75→50% saves only0.12ms. ShadowDepths remains~6.4ms even without planar/SSR. No saved setting changes; keep water quality pending moving-camera checks. Next: per-light shadow isolation, then gameplay CPU/streaming investigation if hitches persist. Evidence WetFloor/ReflectionV20. Large cave silhouette remains open; this is diagnosis, not completion or measured gameplay FPS.

## 2026-10-19 V21 shadow optimization adopted
Scoped blue fill group4 shadow flags disabled after seven-condition GPU isolation and three candidate viewpoints. Fixed-view GPU10.77→5.81ms (transient candidate; not game FPS). Water reflections, global directional and ceiling key shadows preserved. Saved/fresh reload4flags only;4854 actor transforms/meshes/materials/collision unchanged. Final captures WetFloor/WindowShadowV21. Post-save PIE/moving-camera performance still pending; large silhouette not complete. SHA525bb53e50b2f359b3d31710ed2039c04d53ab0228bcc297e5ca0fa2ff8edd4c.

## User correction 2026-10-19: intentional furniture gate
Step1 route criteria corrected: Desk_2_5/6 and Chair_2_6/8/9/10 intentionally block walking-only progress after first ramp. Do not move these props again. Prior full upper-clear route tests are not correct level-design acceptance. User requests six-position rollback only, preserving all subsequent map work. See WetFloor README / RestoreGate_20261019 evidence.

## 2026-10-19 protected layout and seam candidate
All6 intentional gate positions verified in fresh map snapshot; PROTECTED_LAYOUT.json now provides maintained guard data. Material-only floor22 rock swap rejected from two actual views; map unchanged. Next isolate/measure exact seam/trim and author localized transition outside gameplay surfaces, not another full-wall slab. Shared editor released for requested falling/landing plugin build; wait for release before UE continuation.

## 2026-10-19 continuation checkpoint
JunctionFit saved/reloaded: vertical infill top fitted to floor underside, overlap removed. UpperContinuity saved/reloaded: floor19 slot0 uses maintained upper wood;4853otheractors preserved. SavedViews independent fixed-view GPU6.20/6.24ms main and3.17ms upper; not PIE FPS. Six gate furniture protected. Large rock silhouette, adjacent upper-platform seam and integrated normal-input/gameplay performance remain open.

## 2026-10-20 UpperJoin checkpoint
Upper ramp wood continuity and side infill coplanar marks corrected; saved/reloaded and actual two-view reviewed. Ramp/floor geometry retained after exact vertex survey.1material +1infill scale only;4852others preserved. Large rock form remains next art priority; integrated gameplay/GPU separate.

## 2026-10-20 planar-distance optimization
80m distance cap adopted after fixed-view test and multi-view visual review. Saved/fresh reload preserves4854actor layout/meshes/materials/collision and lights; reflection resolution75 unchanged. User save lock resolved. Gameplay trace and rock silhouette still open. See WetFloor/ReflectionDistance.

## 2026-10-20 input validation
Real EnhancedInput ground-aisle PIE walk34.71m verified after natural opening completion. No forcedmovement/teleport; originalmaphash unchanged. CPU median exceedsGPU in this small PIEviewport; next InsightsCPUtrace at targetresolution. No full gate/ramp traversal acceptance; see PIEPerformance report.
