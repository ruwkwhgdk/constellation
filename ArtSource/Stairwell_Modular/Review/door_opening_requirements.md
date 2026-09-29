# Door opening requirements

User explicitly requires an opening door with separate leaf and frame.

- Asset 13: stationary frame, separate mesh and collision.
- Asset 14: moving leaf plus handles, hinge-axis pivot on its right edge when viewed from the front. Door perimeter trim moves with the leaf only if it is leaf trim; stationary frame geometry must never be included in the moving component.
- Assemble in an Unreal door Blueprint with independent frame and leaf components. Rotate only the leaf around its vertical hinge axis. Check open/closed collision, wall/rail interference, and heroine capsule clearance.
- Approved clear opening is 100×210cm. This is an opening specification, not an instruction to make both frame exterior and leaf exactly that size. Account for jambs, fitting gaps and open-door protrusions.

## Current verified state

door14_review_v001.blend is a visual review model, not an interactive door. Its object origin is centered; no hinge pivot, separate frame asset, Blueprint or opening test exists.

Connectivity audit finds six islands: one continuous main door body, three hinges and two knobs. No independently separable frame island is present. The perimeter trim visible in the render is connected to the main body; connectivity alone does not establish whether it visually reads as a frame. Compare against approved leaf concept before finalizing the moving geometry.

At review height 210cm, body bounds are approximately 110.283cm wide and 9.951cm thick, and knobs extend total depth to 30.676cm. These generated dimensions need correction for opening fit and plausible door proportions.

The audit retained the original review file. User subsequently approved Unreal import.

## Imported pair

Maintained import source: `Export/DoorPair/door_pair_source.blend`. Separate fitted procedural frame13 and corrected generated leaf14 exported to independent FBX files. Leaf body is 98.8×209.4cm with 4cm thickness, 0.6cm perimeter fit gap, hinge pivot at origin. Knob-inclusive depth is about14cm. Frame clear opening is100×210cm, no bottom crossbar. Decorative perimeter is retained as leaf trim and moves with the leaf; stationary structural frame is independent.

Unreal assets: `/Game/Environment/StairwellModular/Meshes/SM_Stairwell_DoorLeaf14`, `SM_Stairwell_DoorFrame13`, and `/Game/Environment/StairwellModular/Blueprints/BP_Stairwell_DoorAssembly`.

The dedicated map `/Game/Environment/StairwellModular/Maps/L_Stairwell_DoorVerification` contains closed and90-degree-open assemblies. Component rotation assertions confirm frame remains unchanged. Imported mesh bounds are correct in centimeters and collision data contains1 leaf hull/3 frame hulls. Report: `Export/DoorPair/unreal_import_verification.json`.

Not implemented or verified: gameplay interaction input, runtime animated opening/closing, pawn traversal in PIE, full stairwell wall/rail clearance. Blueprint is an assembly with a movable leaf, not yet a gameplay door controller. Basecolor is from Tripo; roughness/metallic are constant painted-metal settings, not generated PBR maps.
