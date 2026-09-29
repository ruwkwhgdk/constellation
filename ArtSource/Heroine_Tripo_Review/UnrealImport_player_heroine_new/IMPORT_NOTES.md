# player_heroine_new — Constellation import

Content Browser folder: `/Game/Resources/Characters/PC/player_heroine_new`

- `SK_player_heroine_new`: skeletal mesh; validated imported height 160 cm.
- `SKEL_player_heroine_new`: separate skeleton for this character.
- `PHYS_player_heroine_new`: automatically generated preliminary physics asset. This is not a tuned full-body ragdoll; it currently contains pelvis, spine_03 and neck_02 bodies.
- `Materials/M_player_heroine_new`: lit, two-sided master material.
- `Materials/MI_player_heroine_new_*`: 18 material instances preserving the source texture assignments and scalar material properties.
- `Textures/T_player_heroine_new_*_BC`: 12 base-color textures.
- `Animations/AS_player_heroine_new_PreviewRelaxed`: short static relaxed-pose preview, not a locomotion animation.
- `Preview/L_player_heroine_new_Preview`: isolated preview scene.

Source: `../RigContourFix/Delivery/Heroine_Skeletal.fbx` and matching Blender material textures. The source Blender/FBX files are preserved. The legacy FBX importer required an explicit 100x import scale for this export; both mesh and preview animation use that setting. The saved Unreal mesh bounds, not the import setting alone, are checked against 160 cm.

Existing player Blueprints, Animation Blueprints, input logic and project default maps are not replaced. Gameplay integration, animation retargeting and production physics tuning remain separate work.

`verify.py` validates saved assets and writes `import_result.json`. `preview.py` builds the preview scene and requests an Unreal viewport screenshot. `preview_result.json` and `unreal_preview.png`, when present, record the editor check.
