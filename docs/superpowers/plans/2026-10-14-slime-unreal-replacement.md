# Slime Unreal replacement implementation plan

> Execute in this session with superpowers:executing-plans; the user has authorized integration, testing, and removal after successful verification.

**Goal:** Replace the shipped slime with the maintained liquid slime, preserve gameplay animation and collision, verify engine playback, then remove superseded model assets.

**Architecture:** Audit Unreal references and original bind pose first. Prepare an export compatible with the gameplay skeleton, retaining gameplay clips and introducing the liquid Idle. Build engine-native gel materials, replace references through Unreal, and remove old model assets only after reference and runtime checks pass.

**Tech Stack:** Unreal 5.8 Python/editor tools, Blender through tools/run-blender.ps1, FBX.

**Spec:** User request in this chat; ArtSource/Slime/Production/README.md and revision-10.json define the approved model and motion.

## Constraints and review focus
- Keep the maintained Blender source intact; create integration exports separately.
- Preserve attack, damage, death, jump and movement timings, collision and montage notifies.
- Verify units, facing, component material overrides, bind-pose compatibility, and hidden droplet return.
- Never count NullRHI as visual verification. Reload saved assets in a fresh process.
- Back up replaced packages outside Content. Delete through Unreal after checking hard and soft references. Completed exception: two zero-reference ObjectRedirector files remained after engine deletion; exact orphan files were removed after class and reference verification.

## Tasks
- [x] Audit: create ArtSource/Slime/Integration/audit_unreal.py; write asset classes, skeleton tracks, CDO/component settings and referencers to audit.json; export old neutral mesh for bind-pose comparison.
- [x] Prepare: create integration export script using inspected reference transforms. Check neutral dimensions and every source clip against the new mesh. Keep all original gameplay animations functional.
- [x] Import: create import_unreal.py to import the combined skinned mesh and new Idle into /Game/Constellation/Characters/Enemies/Slime_Liquid; assign deliberate Unreal gel, inner-density and eye materials.
- [x] Replace: back up all affected packages; update mesh, animation and material references in Blueprints, review maps, and fixtures. Compile affected Blueprints and save.
- [x] Verify: run a fresh asset audit, real engine render, and PIE/game smoke checks for Idle, movement, attack, hit/death and collision. Capture evidence under Saved/SlimeIntegration.
- [x] Clean: query referencers again, delete superseded mesh/material/texture packages only when unused, rerun load/compile checks, and record final asset paths and verified limitations in Integration/README.md.

