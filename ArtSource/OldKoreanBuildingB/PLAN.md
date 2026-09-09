# Old Korean Building B — playable blockout v01

Approved scope: human-scale third-person exploration, three storeys and accessible roof; modular Blender source and FBX for review before detailed art.

## Design
Coordinates in Blender are metres; front is -Y, height is +Z. Footprint 14.4 x 12 m, storey pitch 3.4 m, floor thickness 0.2 m, wall thickness 0.24 m. Floor surfaces: 0, 3.4, 6.8, 10.2 m. Clear ceiling 3.2 m. Four front bays of 3.6 m. Interior and hidden elevations are inferred, not measured from the reference.

Rear-left U stair: 1.8 m clear flights, 10 risers per half-flight, 0.17 m rise, 0.30 m tread; 2 m landings. Side entrance leads to the stair lobby. Front rooms and rear room connect to a 2.4 m circulation band. Door openings 1.4 x 2.4 m. Roof stair enclosure retains the same stairwell opening. Doors remain open during blockout.

## Execution and checks
- [x] Generate mesh modules with shared data, local assembly pivots, UVs and simple material identifiers; separate convex UCX collision per solid component.
- [x] Assemble three levels and accessible roof, retaining stair openings at every elevated slab; output original blend, individual FBXs, assembly FBX and placement manifest.
- [x] Render exterior, cutaway and interior views for review.
- [x] Validate dimensions, closed collision hulls, foot route support and overhead clearance; round-trip FBX and inspect rendered result.

## Output contract
`generate_blockout.py` reproduces the Blender asset. `Modules/` contains reusable FBXs. `OldKoreanBuildingB_Blockout.blend` contains assembly and module library. `OldKoreanBuildingB_Assembly.fbx` preserves object placement. `assembly.json` records metre positions and rotations. `Previews/` contains review images. `validation.json` records geometry checks. Unreal runtime movement/camera checks must be distinguished from Blender geometry checks; no claim of gameplay verification without engine evidence.

## Limitations
This milestone excludes final brick textures, signs, furniture, interactive doors, LOD authoring and lighting polish. Material colours distinguish parts only. Actual project character capsule and camera settings need an engine playtest.
