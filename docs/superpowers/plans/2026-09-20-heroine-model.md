# Heroine model production plan

> **For agentic workers:** Execute inline using superpowers:executing-plans. The user approved the production direction on 2026-09-20.

**Goal:** Produce a Blender character matching heroine_illust.png, targeting approximately 70,000 LOD0 triangles, with inspectable renders and game export.

**Architecture:** Keep existing Unreal assets intact. Work in ArtSource/Heroine_Rebuild, use the existing FBX as proportion and skeleton reference, and inspect every material change through rendered views. Reuse existing data only where the visual and deformation quality warrants it.

**Tech Stack:** Installed Blender 5.2.1 LTS in background mode, Python bpy, FBX.

**Spec:** User-approved chat design: asymmetric dark bob, reddish eyes, beige cardigan, white shirt, blue bow, plaid skirt, dark thigh-high socks, loafers and accessories. Existing animation compatibility is a target, not a verified assumption. Back design inferred from original mesh where reference art does not show it.

## Global constraints

- Target roughly 70,000 triangles for the complete visible LOD0 character.
- Preserve original source FBX and Unreal content.
- Do not equate increased mesh density with artistic quality.
- Deliver blend, FBX, textures and multiple rendered views; identify any unverified engine behavior.

## Tasks

- [x] Import and audit reference FBX, inspect textured front/side/back renders and skeleton/rest transforms.
- [x] Build and visually review a draft character; prioritize face silhouette, separated hair locks and garment shape.
- [x] Prepare draft UV/material textures, skeletal weights and FBX export.
- [x] Reopen deliverables and check triangle count, UVs, materials, finite normalized weights, skeleton hierarchy and basic pose deformation.
- [x] Deliver multi-angle draft renders and a production report separating achieved and outstanding quality requirements.
- [ ] Achieve requested commercial subculture-game art quality and validate the full Unreal animation/material pipeline. This remains outstanding; the delivered model is explicitly a draft.

## Outputs

- ArtSource/Heroine_Rebuild/scripts: reproducible Blender build/audit scripts.
- ArtSource/Heroine_Rebuild/reference: source audit and baseline renders.
- ArtSource/Heroine_Rebuild/textures: exportable material textures.
- ArtSource/Heroine_Rebuild/renders: review images.
- ArtSource/Heroine_Rebuild/Heroine_Rebuild.blend and Heroine_Rebuild.fbx.
- ArtSource/Heroine_Rebuild/REPORT.md: measured statistics and compatibility limitations.
