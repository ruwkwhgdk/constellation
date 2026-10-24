# Heroine environment lighting — 2026-10-14

## Applied change

The playable `SK_Heroine_GamePilot` now uses dedicated materials under
`/Game/Constellation/Characters/Heroine/GamePilot/Materials/EnvironmentLit`.
`manifest.json` records all 60 original/new slot references and the 107 saved
material / material-instance assets (58 root materials).

The imported shaders mixed the character's texture colour into Emissive. Some
face patches put their entire colour there. This kept clothing and skin bright
in shade, independently of scene lighting. The dedicated graphs reconstruct
Base Color from the original Base Color + Emissive outputs and use Default Lit.
Original custom shader code, textures and face parameters are retained.

`EnvironmentReadabilityFill = 0.02` supplies a small albedo-scaled emission floor.
The zero-emission candidate was too dark in this map's current GI-disabled setup.
This value is a tuning parameter, not a guaranteed luminance percentage.
The visible translucent eye materials (slots 2 and 57) also receive lighting,
with surface-per-pixel translucency lighting and unchanged opacity processing.
The invisible translucent duplicate at slot 3 is unchanged. The former Unlit
temple support uses roughness 1 / specular 0 to match adjacent skin.

Only the playable mesh's material references and the new dedicated materials
were saved. Original materials, geometry, textures, skeleton, morphs, animation,
Blueprint, map, lights and exposure were not edited. The mesh has no assigned
physics asset; that state is preserved.

## Verification

- Background Unreal PIE used the actual player Blueprint, GamePilot mesh and
  `GP_ABP_Player_Heroine`, with separate original/candidate PIE starts.
- Same-camera comparisons covered bright classroom, shaded wall/rock-side and
  cyan lighting, plus frontal and oblique face views. Capture post processing
  copied `PPV_AbandonedSchool_Mood`: histogram exposure, min=max 0.1, bias 0.
  The project GI setting stayed disabled. Earlier manual-exposure/Lumen
  diagnostics were rejected as unrepresentative.
- Controlled half/full blink fixtures checked morph and material-parameter
  readback before exporting. These verify compatibility with the maintained
  face-control bridge, not the game's automatic facial timing.
- A movement-input smoke check moved the actual pawn 101.7 cm with its animation
  Blueprint active. This is not a full walking/running/interaction playthrough.
- Fresh-process disk reload passed all 60 slot mappings, 58 root shader checks,
  unchanged custom HLSL, skeleton, physics reference, morph list and slot names.
- After saving, a new background PIE session completed all six full-body/face
  lighting captures using the updated mesh defaults.
- Background render comparisons are SceneCapture images, not screenshots of
  the user's viewport. Film grain and current hard face shadows remain visible.
  Arbitrary deepest-dark locations and all quality presets were not exhaustively
  tested; hair/skirt can read very dark in shade under the current lighting.

Selected comparison images are in `Review/`. Full diagnostic scripts, captures,
readbacks and logs are in `Saved/HeroineLightingReview/` (local working evidence).

## Loading and reverting

The already-open user editor was not controlled. Restart it, or explicitly
reload the changed mesh and new material packages, before checking the change.
Avoid saving a stale in-memory copy of the mesh over the updated disk asset.

To revert this lighting change, restore each mesh slot to the `before` reference
in `manifest.json`, preserving its slot name, and save only that mesh. The
original material assets remain present. A pre-change mesh binary backup is
also recorded in the manifest under `Saved/HeroineLightingReview/backup/`.
Reimporting the GamePilot mesh may replace its material mapping: retain/reapply
the manifest's `after` references when doing a future mesh handoff.
