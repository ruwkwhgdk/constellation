# Gym Door Polish Implementation Plan

**Goal:** Apply the approved weathered navy gym-door appearance to BP_School_Gate, retaining the current gym door geometry and interaction logic.

**Architecture:** Reuse SM_GymDoorLeaf from School/Sets/GymCorridor. Create dedicated polished PBR materials and update its material slots; replace the old gate mesh in Blueprint defaults. Retain material slot order, glass, dimensions, hinges, collision and timelines. Verify loaded map instances before deciding whether any map override needs editing.

**Tech Stack:** Unreal 5.8 Python, guarded Blender 5.2 inspection, asset-local procedural material detailing.

**Spec:** User-approved concept at ArtSource/SchoolGymDoor/Polish_v001/approved-concept.png and conversation instructions.

## Constraints

- Preserve existing geometry and door-opening behavior.
- No build or Intermediate cleanup; do not stop user editors.
- Restrained rust, navy paint, lower plate wear and glass grime.

## Tasks

- [x] Inspect actual Blueprint templates, gym instances and mesh materials; archive approved concept and exported mesh.
- [x] Create local-coordinate PBR polish that follows the door through rotation; inspect actual UE render.
- [x] Apply to gym mesh and BP_School_Gate, comparing graph and component settings before/after.
- [x] Reload saved assets and map instances, verify closed/open geometry and collision configuration; report actual rendered and runtime verification separately.


