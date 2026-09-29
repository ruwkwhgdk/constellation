# Door 14 — Tripo web job

- Date: 2026-09-24 (Asia/Seoul)
- Source: Concepts/concept_sheet_v002.png, approved asset 14.
- Website login confirmed; initial displayed credit balance: 2,530.
- Image settings: Nano Banana, 3:4, one image, 4K off.
- Submitted once; free-image counter changed 16/100 → 17/100.
- API generation remains stopped (API balance was zero).
- Image completed and transferred to 3D generation through the website's 3D button.
- Smart Mesh P2.0: one model, Triangle topology, target 3,000, private. Free trial used; balance stayed 2,530 after mesh generation.
- Model: https://studio.tripo3d.ai/ko/workspace/generate/c28e0efe-fb79-43ee-9156-9179dae9541c
- Website reports 3,346 triangles / 1,716 vertices. Target is approximate; Blender optimization required.
- Texture job submitted once for 20 credits; displayed balance became 2,510.
- Texture generation completed. Website reports 3,346 triangles and 2,354 attribute-split vertices after texturing.
- Export configured: GLB, 2K texture, filename SM_Stairwell_Door14_raw_v001. Export clicked, but browser download event did not arrive; no matching file exists in the user's Downloads folder. Do not report local delivery or Blender inspection as complete.
- Download resolved by user-provided file: C:/Users/User/Downloads/weathered+metal+door+3d+model.glb. Copied unchanged to Models/14_Door/door14_raw_v001.glb (783,844 bytes). Source and copy SHA256 match: FE07BC8951FB11C00E1A63D79ECC698D3AEB9FD96569BD562460DE36001AE61A.
- Visible material has more prominent scratches/cracks than the isolated reference; needs human review and later material adjustment.
- Blender inspection completed successfully via tools/run-blender.ps1 in approved normal-user context. Review mesh reduced 3,346 → 2,950 triangles, UV retained. After attribute seam merge: 64 boundary/nonmanifold edges remain; not automatically classified as visible holes.
- Review height uniformly normalized to 210cm. Overall bounds 110.283 × 30.676 × 210cm include protrusions, not door slab thickness. Opening fit and side proportions still need adjustment.
- Actual downloaded material has only one 2048×2048 base-color texture; no normal/roughness/metallic texture maps. Do not claim full PBR texture delivery.
- Review source: Models/14_Door/door14_review_v001.blend; report inspection_v001.json; front/back renders door14_view_a.png and door14_view_b.png.
- Status: local Blender review ready, awaiting human appearance comments. No Unreal import or final approval.

## Exact image prompt

Extract ONLY asset 14, the metal door leaf in row 4 column 2 of the reference sheet, as a single isolated game prop. Preserve its approved design: dull worn gray painted steel, subtle scratches and grime, small round handle on the left, hinges on the right. Full door leaf visible, upright, nearly front view with slight three-quarter angle revealing solid thin thickness. No door frame, wall, floor, other assets, grid, labels, numbers or text. Neutral gray background and soft diffuse unlit studio lighting, no strong cast shadow. Keep the original proportions approximately 100 cm wide by 210 cm high. Do not redesign or add decoration.
