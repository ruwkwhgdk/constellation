# PCG-Based Corridor-Type Apartment: Walkable Interior Implementation Workflow (UE 5.8)

This document picks up the **procedural PCG apartment generation** task that was left as an
"unresolved item" in section 2.7 of the earlier document (`terrain-detail-and-roads-workflow.md`).
The goal is to procedurally generate a single building of a Korean corridor-type apartment with
PCG — not just a greybox, but a **collision/navigation structure that lets the player character
actually walk through the entrance, down the corridor, and into a unit**.

**Scope locked in for this round** (based on the clarifying Q&A):

- PCG coverage: **both** the building's structural shell (floors, walls, ceilings, stairwell,
  railings) and repeated props (partition walls, door frames, etc.) are generated procedurally.
- Scale: **single-building prototype** (multi-building expansion is left as a roadmap item only,
  in Chapter 8).
- Assets: **blockout primitives only** (`/Engine/BasicShapes/Cube`, `Plane`, `Cylinder`) — this is
  the stage before modular assets are acquired.

---

## 0. Workflow Summary

1. Define the real-world structure of a corridor-type apartment (single-loaded vs. double-loaded
   corridor, unit count, core placement) in game-ready dimensions.
2. Expose floor count, unit count, corridor width, etc. as PCG Graph **User Parameters** for a
   data-driven design.
3. Build a 3-tier graph hierarchy: `MainGraph → SG_Floor (per-floor loop) → SG_UnitRow (per-unit loop)`.
4. Apply the **Attribute Partition + Loop Subgraph** pattern to both the floor loop and the unit
   loop.
5. Leave a door-width gap in the walls, and place a railing (parapet) on the open side of the
   single-loaded corridor.
6. Set up the Nav Mesh Bounds Volume and Generation Trigger, then verify the character can
   actually walk through the space.

---

## 1. Defining the Corridor-Type Apartment Structure (Converted to Game Dimensions)

### 1.1 Single-Loaded vs. Double-Loaded Corridor

Korean apartments broadly split into stairwell-access type (계단식/홀식) and corridor-access type
(복도식); the corridor-access type further splits into single-loaded (편복도) and double-loaded
(중복도).

| Category | Stairwell-access | Corridor-access (single-loaded) | Corridor-access (double-loaded) |
|---|---|---|---|
| Units per floor | 2–4 | 6–12 | 6–12 |
| Shared corridor | None / minimal | Open corridor on one side (hotel-like) | Enclosed corridor at the building's center, units on both sides |
| Ventilation / daylight | Both sides for most units | Only the side opposite the corridor; corridor-facing windows limited | Middle units get daylight from only one side |
| Core (stairwell/elevator) | Small core repeated per unit cluster | One central core, corridor extends left/right from it | Central core + double-loaded corridor |

**This prototype adopts the single-loaded corridor as the default**, for two reasons:

- It's closest to the archetypal image of a "Korean corridor apartment" — the old 5-story public
  housing type.
- Structurally only one face (the opening/railing side) needs to be handled, which keeps the
  first blockout simpler.

The double-loaded variant is only briefly noted in Chapter 5 as a `CorridorType` branch; the
actual implementation described here is written around the single-loaded case.

### 1.2 Baseline Dimensions (Parameter Defaults)

Real-world architectural ranges, rounded to values that work comfortably for gameplay.

| Item | Real-world range | Default for this project |
|---|---|---|
| Floor height (slab-to-slab) | ~2.8–3.0 m | **300 cm** |
| Units per floor (single-loaded) | 6–12 | **6** (3 on each side of the core) |
| Unit frontage width | ~6–9 m | **700 cm** |
| Corridor width | 1.2 m minimum, typically 1.5–1.8 m | **180 cm** |
| Core (stairwell + elevator) width | ~4–6 m | **500 cm** |
| Entry door width | standard 90–100 cm | **100 cm** |
| Wall thickness | — | **20 cm** |
| Single-loaded corridor railing (parapet) height | practically waist-to-chest height | **110 cm** |

These numbers aren't "correct answers" — they're PCG graph input parameters. The key point is
being able to change just the numbers later to pull out a different floor plan.

---

## 2. Data-Driven Parameter Design (User Parameters)

In UE 5.8, defining parameters in a PCG Graph asset's **Details panel → User Parameters** tab
exposes them directly in the Details panel of any PCG Graph Instance (or PCG Component) placed in
the level, so each instance can be given different values. This is the same philosophy used for
non-destructive editing with Landscape Edit Layers in the roads document — "produce multiple
variants by changing numbers, not by rebuilding the graph."

Parameters to define:

- `FloorCount` (int) = 5
- `FloorHeight` (float, cm) = 300
- `UnitsPerSide` (int) = 3 — number of units on one side of the core (6 per floor combined)
- `UnitWidth` (float, cm) = 700
- `UnitDepth` (float, cm) = 800 — blockout depth of a unit's interior (a single room, for the
  prototype)
- `CorridorWidth` (float, cm) = 180
- `CoreWidth` (float, cm) = 500
- `DoorWidth` (float, cm) = 100
- `WallThickness` (float, cm) = 20
- `ParapetHeight` (float, cm) = 110
- `CorridorType` (enum: `SingleLoaded` / `DoubleLoaded`, default `SingleLoaded`)

---

## 3. Graph Hierarchy

```
MainGraph
 └─ (Create Points Grid: 1D along Z, count=FloorCount, spacing=FloorHeight)
     └─ Attribute Partition (Index) → Loop Subgraph: SG_Floor
         ├─ Core blockout (stairwell/elevator mass, repeated at the same position on every floor)
         └─ (Create Points Grid: 1D along X, count=UnitsPerSide, spacing=UnitWidth) ×2 (left/right, mirrored via Transform Points)
             └─ Attribute Partition (Index) → Loop Subgraph: SG_UnitRow
                 ├─ Floor/ceiling slab (Static Mesh Spawner: Cube)
                 ├─ Inter-unit partition wall (Static Mesh Spawner: Cube, thin and tall)
                 ├─ Corridor-facing exterior wall + entry opening (2-segment wall + door frame)
                 ├─ Open-side parapet (single-loaded corridor railing)
                 └─ Unit interior blockout room (floor/3 walls/ceiling, sized by UnitDepth)
```

A Loop Subgraph must receive **partitioned data** for it to process one point at a time. The
required procedure, confirmed from the official forum, is:

1. Create an index attribute on each point (copy `$Index` into an `Index` attribute via Copy
   Attribute, or otherwise use the sequential order value with Create Attribute — no Attribute
   Noise needed).
2. Split the data with an **Attribute Partition** node keyed on that `Index` attribute so that
   each point becomes its own partition (subset).
3. Feed the partitioned data into the **Loop Subgraph** input.
4. Inside the subgraph, only that one partition (= one point) is present, so use Attribute Select
   and similar nodes to pull out that point's attributes (floor index, unit index, etc.) for
   position/size calculations.

Apply this same pattern in both places: `MainGraph → SG_Floor` and `SG_Floor → SG_UnitRow`. The
most common mistake is plugging the raw point data directly into a Loop Subgraph without
partitioning — everything then gets processed as a single batch, so you don't get "a different
position per floor."

---

## 4. MainGraph: Building the Floor Loop

1. Use **Create Points Grid** to create a 1×1×`FloorCount` grid along Z, with spacing
   `(0,0,FloorHeight)`. Each point becomes a "floor origin."
2. Copy the point index into a `FloorIndex` attribute.
3. Connect **Attribute Partition** keyed on `FloorIndex` → **Loop Subgraph (SG_Floor)**.
4. **Merge** the output of each floor's subgraph (all the Static Mesh spawn data for floors,
   walls, railings, units, etc.) into the final output. Since the actual spawning (Static Mesh
   Spawner) already happens inside the lower subgraphs, the Merge at the MainGraph level can be
   used purely for debugging/statistics if you like.

---

> **⚠️ Design change — see Chapter 14:** Sections 5.1 and 5.2 below describe the original
> prototype design ("a single central core"). Through actual playtesting it was confirmed that
> **there needs to be a separate core (stairwell) at each end of the building** (confirmed by the
> user — see Chapter 14), so any further work on this graph should treat **Chapter 14, not
> sections 5.1/5.2, as the current source of truth** for the floor plan. Sections 5.1/5.2 remain
> useful only as a reference for understanding how the stair itself is generated inside a core
> (the structure of SG_Stair).

## 5. SG_Floor: Core + Left/Right Corridor + Unit Rows

### 5.1 Core (Stairwell/Elevator) Blockout

The core repeats at the same local coordinates on every floor, so there isn't much need for
procedural "variation." Using the floor origin point (Z = current floor height) passed into the
floor subgraph, place the following at fixed offsets with a **Static Mesh Spawner**:

- One stairwell mass box (`CoreWidth` × stairwell depth, extruded to the full floor height —
  actual stair treads can be omitted in the prototype and represented with a ramp-shaped Cube
  instead)
- One elevator shaft mass box
- The core's landing floor slab

Since this part only needs to "repeat per floor," you can wire 3–4 Static Mesh Spawners in
parallel directly inside SG_Floor, without a Loop.

### 5.2 Building the Left/Right Corridor Unit Rows

Single-loaded corridors are often laid out with "the corridor extending left and right from a
central core," so create one `Create Points Grid` (1D along X, count=`UnitsPerSide`,
spacing=`UnitWidth`, start offset = `CoreWidth/2 + UnitWidth/2`) on each side of the core. Keep
the right side as-is, and mirror the left side along X with **Transform Points** (scale -1, or a
180° rotation) to reuse the same graph. In other words, build the unit-generation logic
(SG_UnitRow) only once, and feed in different position/orientation for the input points on the
left vs. the right.

Assign a `UnitIndex` attribute to each point, then connect Attribute Partition (keyed on
`UnitIndex`) → Loop Subgraph (SG_UnitRow).

### 5.3 `CorridorType` Branch (room left for double-loaded expansion)

When `CorridorType == DoubleLoaded`, simply generate one more identical unit row on the opposite
side. It's enough to check the `CorridorType` value with an Attribute Filter to toggle the second
unit-row branch on or off. This prototype only actually verifies `SingleLoaded`.

---

## 6. SG_UnitRow: One Unit = Walls + Opening + Parapet + Interior Blockout

What comes into this subgraph is the origin point of a single unit (position relative to the
core, including the floor origin's Z).

### 6.1 Floor/Ceiling Slab

Place a `Static Mesh Spawner` (Cube) scaled to `UnitWidth × (CorridorWidth + UnitDepth) × slab
thickness`. **Join the corridor floor and the unit floor into a single continuous slab so there's
no threshold step** — if there's a step that exceeds Character Movement's Max Step Height
(roughly 45 cm by default), the character gets stuck and can't pass through, so keep the step at
zero entirely during the prototype stage.

### 6.2 Inter-Unit Partition Walls

Place a thin, long `Static Mesh Spawner` (Cube, thickness=`WallThickness`, height=`FloorHeight`)
at each unit boundary (both sides). Since neighboring units share a partition wall, it's simplest
to set a rule like "only the right-hand boundary spawns it" to avoid duplicate spawns (you can
also do this with an Attribute Filter that spawns only on even/odd `UnitIndex`).

### 6.3 Corridor-Facing Exterior Wall + Entry Opening ("doors" from blockout primitives)

With no modular door mesh available, the practical way to create an opening isn't a boolean cut
into the wall — it's to **pre-split the wall into segments sized around the door width**.

1. Compute the leftover after subtracting `DoorWidth` from the unit width (`UnitWidth`), split
   evenly into two wall segments: `SegmentWidth = (UnitWidth - DoorWidth) / 2`.
2. Generate two wall-segment points (left/right) and spawn each with a `Static Mesh Spawner`
   (Cube, width=`SegmentWidth`). Since no point is ever created for the middle `DoorWidth` span,
   the wall ends up looking like it has an opening.
3. At the door location, add only a thin, collision-free decorative frame (left/right vertical
   posts + a lintel) via `Static Mesh Spawner`. An actual openable door leaf is out of scope for
   the prototype — just leave it as an open gap.
4. Filter out the wall segments at door locations using `Attribute Filter` or `Density Filter` —
   creating a boolean attribute like "this point is a door" makes it easy to reuse across several
   downstream nodes.

### 6.4 Open-Side Parapet (Single-Loaded Corridor Railing)

On the side opposite the corridor (the open-air side), erect a waist-height box
(`ParapetHeight` = 110 cm) instead of a wall. Since this height comfortably exceeds Character
Movement's default Max Step Height (~45 cm), **this one box alone is enough fall-prevention
collision, with no separate invisible blocking volume needed** — just double-check in an actual
playtest that it doesn't block the camera's view (if using third person).

### 6.5 Unit Interior Blockout Room

Within the prototype's scope, the unit interior is implemented only as a single room. Past the
entry opening, at a depth of `UnitDepth`, erect the floor/left wall/right wall/back wall/ceiling
with `Static Mesh Spawner`. Windows could reuse the same "split into segments, leave a gap"
technique from section 6.3 on the back wall (unlike a door, a window starts at some height above
the floor, so it needs one more split along the vertical axis) — this is skipped for this round
and left as a follow-up item.

---

## 7. Collision & Navigation Mesh Setup (Making It Actually Walkable)

Even with the whole structure built, if collision and the NavMesh don't line up the player will
walk through walls or get stuck in the corridor. Points to check:

### 7.1 Basic Collision

Engine default primitives like `/Engine/BasicShapes/Cube` and `Plane` ship with a `BlockAll`
collision preset by default, so they work as walls/floors with no extra setup. Just confirm the
collision preset on the Static Mesh Spawner node's Static Mesh Descriptor hasn't been accidentally
switched to `NoCollision`.

### 7.2 Nav Mesh Bounds Volume

Place a `Nav Mesh Bounds Volume` that covers the entire building (width × depth ×
`FloorHeight` × `FloorCount`, plus margin). As floor count grows it's easy to miss the vertical
(Z) extent, so size the volume with reference to `FloorCount × FloorHeight` (ideally keeping this
value in sync via data as well).

### 7.3 Generation Trigger — Prefer Static During the Verification Stage

Setting the PCG component's Generation Trigger to **Runtime/Dynamic** can run into a regression
reported on the community forums (as of 5.6.1: Instanced Static Meshes spawned by PCG don't
automatically trigger a NavMesh update). During the structural-verification stage, the safest
approach is **GenerateOnLoad (static generation)**, so PCG fully generates first and the NavMesh
is baked once afterward.

If you later need dynamic runtime regeneration (e.g., an on-the-fly reroll with different floor
plan parameters), keep these workarounds in mind:

- On the PCG graph's generation-complete event (e.g. `OnGraphGenerated`), force-call
  `SetCanEverAffectNavigation(true)` + `UpdateComponentInNavOctree` on the spawned components.
- Alternatively, place a `NavModifier` actor with rectangular collision at the PCG spawn location
  to handle the navigation update separately.
- Setting the NavMesh itself to Dynamic is a baseline prerequisite either way; the two methods
  above are workarounds for the specific symptom of "generation succeeded, but the NavMesh didn't
  notice."

### 7.4 ISM vs. Individual Static Mesh Actors

By default, Static Mesh Spawner spawning as Instanced Static Meshes (ISM) is better for
performance, but there are reported cases where ISM navigation recognition lags behind. **During
the blockout verification stage, temporarily set it to "Spawn as Actors" (individual Static Mesh
Actors) to rule out navigation issues first**, then switch to ISM for optimization once the
structure and traversal are verified.

### 7.5 Checking Agent Radius Against Narrow Openings

A `DoorWidth` of 100 cm is comfortably wider than the default NavMesh Agent Radius (~34 cm,
meaning the width needed for passage is roughly Agent Radius × 2 plus margin), but if a corner or
a decorative door-frame mesh slightly intrudes into the opening, Recast's voxelization can end up
marking the opening as non-navigable. Test by actually walking a character through it, and if it
gets stuck, widen the door or adjust the Agent Radius/Cell Size.

---

## 8. Verification Checklist

- Does the Nav Mesh Bounds Volume generously cover the full `FloorCount × FloorHeight` extent?
- Can a character walk uninterrupted from the ground-floor lobby → stairwell → each floor's
  corridor → a unit's entry → the unit's interior (confirm zero step height between corridor and
  unit floors)?
- On the single-loaded corridor's open side, does the character fail to fall past the parapet?
- Does the character pass through door openings without getting stuck (check Agent Radius per
  section 7.5)?
- In both `MainGraph` and `SG_Floor`, is there no mistake of feeding data into a Loop Subgraph
  without an Attribute Partition first (the classic cause of floors/units overlapping)?
- With Generation Trigger set to Static (GenerateOnLoad), does the NavMesh accurately reflect the
  whole structure without a separate regeneration step?
- After changing parameters (floor count, unit count, corridor width, etc.) and regenerating, do
  all of the above still hold (this is how you confirm the data-driven design is actually
  reusable)?

---

## 9. Suggested Next Steps

- Add window openings to unit interiors (the part deferred in section 6.5 — requires an
  additional vertical segment split).
- Blockout actual stair treads inside the stairwell — currently handled as a plain mass box only.
- Once modular wall/door/window assets are available, keep the current "split into segments, leave
  a gap" logic exactly as-is and just swap the primitive Cubes for real meshes (swap only the
  Static Mesh Descriptor, with no graph-structure changes).
- When expanding to multiple buildings, reuse the Landscape Spline from
  `terrain-detail-and-roads-workflow.md` as a PCG Spline input, adding an upper-level graph that
  samples building placement positions along the road.
- Actually implement and verify the double-loaded corridor branch (`CorridorType = DoubleLoaded`).
- For large-scale placement, review PCG Partition Actor / World Partition grid sizing.

---

## 10. Facade Detail Expansion: Stairwell Entry Doors, Windows, and Elevator on Both Cores

This is the detail pass that follows the first blockout (mass + floor slabs + the core notch
repeated on every floor). None of the three items needs a new kind of node — all three are solved
by applying the **split-into-segments** pattern already used in Chapters 5 and 6 once more, to the
core walls and the facade walls.

### 10.1 Stairwell Entry Door (Opening in the Core Wall)

Right now, per section 5.1, the core is likely spawning "one solid stairwell mass box." To add a
door, don't leave that box solid — instead, **split off just the core's corridor-facing wall into
its own points**, using the same approach used for unit entries in section 6.3.

- Subtract `DoorWidth` from the core width (`CoreWidth`), split the remainder into left/right wall
  segments, and spawn each with its own `Static Mesh Spawner`; never create a point for the
  middle `DoorWidth` span at all (= an open gap).
- If there's a core at each end of the building (a left core and a right core), reuse the same
  logic by **mirroring with Transform Points** rather than building the graph twice — identical to
  how the left/right unit rows were mirrored in section 5.2.
- Keep the floor at the door location flush with the corridor floor, with no step (same reasoning
  as section 6.1 — a step exceeding Max Step Height blocks the character).
- Since this is still the prototype stage, an actual openable door leaf isn't needed. A plain open
  gap is passable; a thin decorative frame (left/right vertical posts + a lintel) is enough.

### 10.2 Windows (An Additional Vertical Split on the Facade Wall)

This is the item deferred as a "next step" in section 6.5. Up to now the wall has only been split
**horizontally (along X)** into left/right pieces because of the door; to add windows, it needs
one more split **vertically (along Z)**.

- Split the wall segment that will hold a window into three vertical tiers: a solid lower sill
  wall (e.g., 90 cm from the floor), the window opening itself (e.g., the next 120 cm — either
  create no point there, or substitute a thin glass-panel mesh), and a solid lintel section up to
  the ceiling.
- The fastest way to represent "glass" during blockout is to spawn one more thin Cube in that span
  and temporarily assign it a translucent/tinted Unlit material (e.g., pale sky blue) via the
  Static Mesh Descriptor. Swapping in the real glass mesh/material later can reuse this same point
  position during the detail pass.
- The same technique can add windows to the core notch area (the stairwell's exterior wall) —
  stairwells genuinely tend to get a lot of windows in real buildings too, since daylighting
  matters there.

### 10.3 Elevator (A Separate Shaft + a Door on Every Floor)

This fleshes out the part that section 5.1 lumped together as "one elevator shaft mass box."

- Place a separate shaft box (`Static Mesh Spawner`) inside the core width, next to the
  stairwell — you can either extrude it once to the full height (`FloorHeight × FloorCount`) or
  repeat it per floor; visually there's no difference since it's a solid mass either way.
- Cut a door-width opening on the shaft's corridor-facing side **on every floor** — this is
  exactly the same "split into segments" pattern as section 10.1. This isn't a real elevator door
  that opens and closes; for now, an opening that simply signals "there's an elevator here" is
  enough.
- The prototype doesn't need the player to be able to walk into the elevator car itself, so seal
  the inside of the opening with a wall at a shallow depth (50–80 cm) — this prevents the
  character from walking in and getting stuck with no way out.

### 10.4 Additional Verification Items

Add these three lines to the Chapter 8 checklist and confirm them:

- Does the character pass through both the left and right core entry doors without getting stuck
  (10.1)?
- Are the window openings fully open with no leftover collision, or, if using a glass panel, is
  its material/collision setup such that it doesn't block the character (10.2)?
- When entering the elevator opening, does the character naturally hit the dead-end wall, and does
  the NavMesh correctly avoid marking the space beyond it as "reachable" (10.3)?

---

## 11. Stairwell Real Stair Blockout: the Typical Dog-Leg (Half-Turn) Stair Shape

Up to this point, the core is only represented as a mass/notch, with no actual stair treads. The
typical stairwell in a Korean corridor-type apartment is almost always a **dog-leg (half-turn)
stair**: over the course of one floor, it climbs half the height in one direction, turns 180° at a
mid-landing, then climbs the remaining half in the opposite direction. It's also usually open to
the outdoors for daylight and ventilation, so the sides of the flights and landing are visible from
outside — that vertical slit/notch already in the screenshot is exactly that open void.

### 11.1 Additional Parameters

- `StairRiser` (float, cm) = 18 — the height of one step (riser)
- `StairTreadDepth` (float, cm) = 28 — the depth of one step (tread)
- `StairWidth` (float, cm) = 120 — stair width
- `LandingDepth` (float, cm) = 150 — depth of the mid-landing
- `StepsPerFlight` = `(FloorHeight / 2) / StairRiser`, rounded to an integer (compute this with
  integer division + rounding inside the graph). With the defaults, 300 cm / 2 = 150 cm,
  150 / 18 ≈ 8.3 → 8–9 steps.

### 11.2 Building One Floor's Worth of Stairs (Flight A + Landing + Flight B)

The easiest technique is **to build one inclined spline and sample points along it at even
intervals**. Unlike the "split horizontally into segments" trick used for doors/windows, a stair
climbs, so a spline-based approach is much cleaner here.

1. Draw a 2-point spline for Flight A: start point `(0,0,0)`, end point
   `(StepsPerFlight × StairTreadDepth, 0, StepsPerFlight × StairRiser)` — a straight spline that
   moves horizontally by `StepsPerFlight` steps while simultaneously rising by that same amount
   vertically.
2. Bring this spline into PCG with **Get Spline Data**, and set **Spline Sampler** to "point
   count = StepsPerFlight" mode to sample evenly spaced points. Since the spline is a straight
   line at a constant slope, the sampled points automatically come out shifted "forward and up,
   one step at a time."
3. Spline Sampler orients points along the spline's tangent by default (so pitch tilts with the
   slope); correct this with **Transform Points**, zeroing out Pitch/Roll so the tread stays
   level (keep only Yaw).
4. Spawn a `Static Mesh Spawner` (Cube, sized `StairWidth × StairTreadDepth × StairRiser`) at each
   point — each tread becomes a single solid stair block that already includes its riser, so the
   collision naturally follows the stair shape.
5. Place the **landing** at the top of Flight A: a `Static Mesh Spawner` (Cube,
   `StairWidth × 2 × LandingDepth`) positioned at the height where Flight A ends
   (Z = `FloorHeight`/2).
6. Reuse the exact same graph for Flight B by **rotating it 180° and repositioning it to the
   landing with Transform Points** — this is exactly the same pattern used to mirror left/right in
   sections 5.2 and 10.1. Flight B starts at the landing and climbs to the next floor's floor
   height (Z = `FloorHeight`).
7. Wrap this Flight A + landing + Flight B bundle into an **SG_Stair** subgraph, replacing the
   "stairwell mass box" from section 5.1. Since SG_Floor already repeats per floor, SG_Stair
   repeats per floor automatically along with it.
8. When placing SG_Stair at both ends of the building (or at both directions of a central core),
   use the same **Transform Points mirroring** approach from section 10.1 so the graph doesn't
   need to be built twice.

### 11.3 Fall-Prevention Railings for the Open Stairwell

Korean corridor-apartment stairwells are almost always open to the outdoors, so the sides of the
flights and landing are open. Erect the same box used for the parapet in section 6.4
(`ParapetHeight` = 110 cm) along the open side of each stair flight and the edge of the landing —
since this follows the spline structure, just create one more parapet point offset sideways by
`StairWidth/2 + parapet thickness/2` from the same point list used to spawn the stair steps.

### 11.4 Collision/Navigation Notes

- Since `StairRiser` = 18 cm is well under Character Movement's default Max Step Height
  (~45 cm), Recast's NavMesh should recognize each individual stair tread as "climbable" without
  needing any separate ramp collision. In other words, the solid step-block approach from
  section 11.2 should be walkable up and down with no extra work.
- If, during actual playtesting, the character feels like it's catching slightly on every step
  while climbing, try lowering `StairRiser` (e.g., to 15 cm) or nudging up the Nav Mesh Agent's
  `Max Step Height` in the project settings, and compare.
- Double-check there's no step between the landing and the stair treads (for the same reason as
  section 6.1).

### 11.5 Additional Verification Items

- Can the character actually walk up both the left/right (or both-ends) stairwells from the
  ground floor to the top floor?
- Does the character turn naturally at the 180° landing turn (no snagging or getting stuck)?
- Does the character fail to fall past the parapet on the open side of the stairs?

---

## 12. Troubleshooting: Stair Entrance Hidden Behind a Wall, or Stairs Not Generated on Both Sides

Two symptoms that commonly show up right after implementing Chapter 11. In both cases the root
cause is usually not "the graph logic is wrong" so much as **coordinates or data computed
independently in two different sections drifting apart, or a branch's output never getting merged
in**.

### 12.1 Symptom A — The Stair Entrance Is Hidden Behind a Wall

Section 10.1 (cutting a door-width opening in the core wall) and section 11.2 (the spline-based
stair flight) most likely compute their opening position / stair start position from two different
local coordinate references. If those two reference points drift apart, the core wall genuinely
does have a door-width gap, but that gap doesn't line up with where Flight A's spline actually
starts — producing exactly the symptom of "it looks open from the corridor, but something else
(a partition wall, the door-frame decoration, the elevator shaft wall, etc.) overlaps right in
front of it and blocks it." Checking order:

1. Print and compare the local X center of the core wall's opening against the local X of Flight
   A's spline start point (via PCG debug points or an Attribute Debug node). If the two values
   differ, that's the cause.
2. The real fix is to make both sections derive from **one shared reference attribute** (e.g.
   `DoorCenterX`), so the wall-segment split in 10.1 and the spline start point in 11.2 are always
   computed from the same value — never calculate the coordinate twice in two places.
3. If the coordinates match and it's still blocked, check whether the decorative door frame from
   10.1 (left/right posts + lintel) has its post width accidentally scaled to the full
   `DoorWidth` — the decorative frame should be a thin border around the edge of the opening, not
   a piece that covers the whole opening.
4. If it's still blocked, check whether the elevator shaft wall (10.3) or an inter-unit partition
   wall (6.2) is spawning on top of the same spot — three or four independently-authored wall
   spawners landing on the same coordinates by mistake is the single most common bug in a
   multi-stage graph like this one.

### 12.2 Symptom B — Stairs Only Appear at One (Central) Location, Not on Both Sides

Both sections 10.1 and 11.2 say "don't build the graph twice — reuse it by mirroring with
Transform Points." If stairs still aren't appearing on both sides, it's most likely one of these:

1. **Only one core position point is actually being generated**: the step that creates the
   left/right core positions (there should be 2 points, one at each end of the building) may have
   its count set to 1, or a filter may be excluding one side. Check this point count first with
   Attribute Debug — confirming it's 2 is the first thing to verify.
2. **The mirrored branch's output was never wired into the Merge**: this is one of the most common
   PCG mistakes. If you build the left-side branch with Transform Points but forget to connect its
   output into the final Merge/output node, the computation runs fine but nothing shows up in the
   level — the most common cause of something looking like "it didn't generate." Check that both
   the left and right branches feed through one Merge node into the final output inside the graph
   that wraps SG_Stair.
3. **Missing partition before the Loop Subgraph**: the same issue emphasized in Chapter 3. If the
   2 core-position points are plugged into the SG_Stair call without partitioning first, they get
   processed as a single batch instead of individually — which can result in only one side (or
   both collapsed into one) appearing to generate. Re-check that `Attribute Partition` is properly
   keyed on the core index.

### 12.3 Debugging Order, Summarized

1. Check the core-position point count first (is it 2?).
2. Do those 2 points go through an Attribute Partition before entering the Loop Subgraph?
3. Do both branch outputs feed into the final Merge?
4. Do the core wall's opening coordinate and the stair flight's start coordinate come from the
   same shared reference value?
5. Is the decorative door frame, elevator shaft wall, or a partition wall encroaching on the
   opening's space?

---

## 13. Confirmed-in-Practice Constraint: This Project's Unreal MCP Tool Cannot Build a Loop Subgraph

Claude Code opened the live graph and confirmed that the MCP graph-editing API used on this
project **cannot set a Loop node's `subgraphInstance` property, so the Attribute Partition + Loop
Subgraph combination described in this document simply cannot be built** (the tool can't
construct the `PCGGraphInstance` object the Loop node requires). As a result, the actual graphs
(`PCG_Apartment_Main` / `_Floor` / `_Stair`) replace the pattern described in Chapters 3–5 with a
**plain Subgraph node + Copy Points, cartesian-stamping duplicated coordinates in one batched
call** instead. This is functionally equivalent at the current point counts, but it means the
per-branch isolation that Partition used to give you automatically now has to be **built by hand
as separate explicit branches, each one wired into the final Merge without exception**. Wherever
Chapters 3–5 and 10–11 say "Attribute Partition → Loop Subgraph," read that, for this project, as
"one explicit branch per point, built by hand, plus Merge."

This constraint is exactly why Chapter 11's Flight A/B don't both appear automatically — if you
build a branch for Flight A, you must build a **separate second branch** for Flight B and wire it
into the Merge; skipping that reproduces precisely the "one side of the stairs appears, the other
doesn't" symptom seen here.

### 13.1 Applied to This Case: Flight B Is Entirely Missing

Per Claude Code's report, only Flight A (local X=-65) was found inside `SG_Stair`
(`StairLocalTemplate`) — Flight B, which should continue from the far side of the landing up to
the next floor, was never mentioned. The real cause of "stairs should generate on both sides but
don't" isn't the "core at each end, only one side generates" problem worried about in sections
10.1/10.2 — it's that **this project's structure genuinely has a single core (as designed in
sections 1.1/5.1/5.2), and one of the two flights of that core's dog-leg stair (Flight B) simply
isn't in the graph at all.**

Fix: inside `SG_Stair`, build one more branch that **duplicates Flight A's point set (Copy
Points) → rotates it 180° and moves it to the far end of the landing with Transform Points**, then
feed this branch's output into the same Merge Points node as Flight A and the landing, and send
that out as `SG_Stair`'s final output. Since Loop isn't available, this means explicitly drawing
in a few more nodes by hand.

### 13.2 A Wall Blocking the Middle of the Stairwell Passage

The full-floor-height vertical wall panel running up and down through the center of the
stairwell passage — circled in red in the screenshot — should not be sitting in the path people
actually need to walk. Two likely candidates:

- **The elevator shaft wall (section 10.3)** — after moving DoorCenterX from -125 to -190, the
  stair flight positions were recalculated, but the elevator shaft wall likely kept its old
  coordinates, so it probably ended up sitting in the middle of the passage as a result.
- **A leftover piece of a core wall segment (section 10.1, `CoreLocalTemplate`)** — even though
  the left/right segment widths were reportedly recalculated after the DoorCenterX fix, it's worth
  re-checking whether those segments' Z range (the full floor height) extends into a span that
  overlaps the stair passage's width.

Fix: enumerate every Static Mesh Spawner template inside `SG_Stair` and `CoreLocalTemplate`, and
find whichever one has a local X range overlapping "the passage width between Flight A and Flight
B" while its Z range spans the full floor height. Once found, either move that wall outside the
passage (toward the elevator shaft side, or further into the core wall) or shrink its X range so
it no longer overlaps the passage — and be sure to recompute it from the newly confirmed Flight
A/B coordinates from section 13.1, so it doesn't drift again the way section 12.1 already warned
about.

---

## 14. Design Correction: Two Stair Cores, One at Each End of the Building

After several turns of debugging, here's what's actually been confirmed: "stairs on the left and
right" never meant "Flight A/B of the single dog-leg stair inside one core" — it meant **there
needs to be a separate core (stairwell) at each end of the building** (confirmed by the user).
Flight A/B themselves are already verified working, since Claude Code took them through a clean
regenerate plus a full world-space transform cross-check. So the SG_Stair subgraph from Chapter
11 stays exactly as-is; the entire scope of this change is **going from one core position to
two**. In other words, this isn't a bug fix — it's re-laying-out the floor plan itself.

### 14.1 What Changes

- **Core**: previously, there was one core at the building's center with the corridor extending
  left and right from it (section 5.2). Now there's a Core A and a Core B, one at each end of the
  building, with a single corridor connecting them.
- **Unit row**: previously, units were placed as "`UnitsPerSide` units on each side of the
  central core" (section 5.2). Now they're placed as "a single row of units filling the span
  between the inner edge of Core A and the inner edge of Core B." Whether the total unit count
  (currently 6) stays the same or grows to fit the building's actual length should be decided
  after seeing the real distance between Core A and Core B.
- **SG_Stair itself**: unchanged. Flight A/B, the landing, and the slit guard are all reused
  as-is at both Core A and Core B.

### 14.2 Graph Change Procedure (applying Chapter 13's "no Loop support" constraint)

Since it's already confirmed that this project's MCP tool can't build a Loop Subgraph
(Chapter 13), going from one core to two isn't automatic repetition either — it has to be handled
the same way as everything else here: **explicitly draw one more branch and wire it into the
Merge**.

1. Leave the existing `StairAnchorPoint` (Core A, local `(-125, 0, 0)`) as-is.
2. Create a new `StairAnchorPoint_B` at the opposite end of the building. Compute its coordinates
   so it's symmetric to Core A across the building's full width (e.g., if the building width is
   `W`, Core B's local X should land near `W - 125` — but don't just estimate this by hand; have
   Claude Code pull the actual current unit/core width totals from the live graph and compute it
   from there).
3. Instantiate `Call_Stair` a second time, identically to Core A's instance, and wire it to
   `StairAnchorPoint_B` — this is the same "duplicate the graph" pattern used to mirror the doors
   left/right in section 10.1. First check whether Core B's stair needs a 180° Yaw rotation via
   Transform Points so it faces the corridor the same way Core A's does (Core A opens toward the
   corridor; simply relocating the same points without rotating could leave it facing the wrong
   way).
4. Wire Core B's branch output into the same final Merge Points node as Core A's branch — the
   "built the branch but forgot to wire it into Merge" mistake flagged in section 13.1 is the most
   common failure mode here too.
5. Recompute the unit-row generation logic (the relevant part of section 5.2) so it fills the span
   between Core A's inner edge and Core B's inner edge. Simply moving the core positions while
   leaving the current "extend left/right from a central core" code in place will make the unit
   row overlap the cores or spill outside the building — this part genuinely needs its coordinates
   recomputed, not just repositioned.
6. Check whether sections 10.1 (door opening) and 10.3 (elevator) are applied to Core B as well as
   Core A — since all of that detail work so far has only ever targeted Core A, Core B is likely
   still sitting there as a plain mass box missing all of it.

### 14.3 Verification

- After a clean regenerate, can a character actually walk from the ground floor to the top floor
  at both Core A and Core B?
- Do the units placed in the corridor between the two cores avoid overlapping either core's walls?
- Does Core B have the same door opening, elevator, and windows as Core A?
- Viewed from outside the building, do both ends show a symmetric, stairwell-style open
  slit/notch?

---

## 15. Stairwell Shaft Void and Headroom Clearance

Playtest screenshot: the character climbs the stairs and gets blocked by the floor/ceiling of the
level above, unable to continue. Everything through Chapter 11 only verified "are the stair
treads walkable" — it never checked **whether some other floor's slab or the landing blocks
passage through the space above the stairs**. The cause is one of two things (possibly both).

### 15.1 Cause A — the Floor Slab Solidly Covers the Stair Passage's Footprint

In a real building, a stairwell needs a genuine **vertical shaft void through each floor slab**,
sized to the plan-view footprint of both flights, exactly where the stairs pass through. That's
what lets a character who's climbed Flight B all the way up step cleanly onto the corridor level
above instead of hitting a solid floor. If section 5.1's "core lobby floor slab" is currently
spawning as one solid rectangle covering the entire core width (`CoreWidth`) at every floor, that
rectangle is exactly what would be covering the space Flight A/B on the floor below need to pass
through — appearing as a blocking ceiling.

Fix:

1. Shrink the core lobby floor slab from "one solid `CoreWidth × core depth` rectangle" down to
   just **the small arrival platform right where Flight B lands** (roughly
   `StairWidth × 150 cm`).
2. For the rest of the core's plan area (the full X/Y range both flights occupy), **create no
   points at all** at that floor's Z level — that's the actual shaft void. The landing from
   section 11.2 sits at the half-floor height between floors, so it's unaffected by this rule.
3. Apply this to every floor's slab except the top one (floor 1 through `FloorCount`-1). There's
   nothing to climb above the top floor, so the roof can stay solid.
4. Since Chapter 14 introduced two cores, apply this identically to both Core A and Core B.

### 15.2 Cause B — Insufficient Headroom Above the Landing or the Opposite Flight

If it's still blocked after fixing Cause A, this is likely a headroom problem instead — **the
underside of the landing or the opposite flight sits low enough to intersect the head height of
someone climbing**. In a "scissor" dog-leg stair like this one, where the two flights run
parallel and stacked, the underside of Flight B (or the landing above it) passes directly over
someone climbing Flight A, so **the vertical distance from every tread of Flight A up to whatever
solid geometry sits directly above it needs to be at least ~210 cm** (a commonly used real-world
architectural minimum). The current graph most likely never factored this in.

Fix: for every tread of Flight A (seeds 201–208 and similar), compute the vertical distance
straight up to the first solid geometry it hits (the landing's underside, Flight B's step-box
underside, etc.), and check whether any of them come in under 210 cm. If so, resolve it with one
of the following:

- Nudge the landing's height up or down to rebalance the vertical gap between the two flights.
- Lengthen the stairwell's overall depth (the `CoreWidth`/Y-axis dimension) so each flight's run
  is longer, and let the actual riser count per flight adjust accordingly.
- At this project's scale (a prototype with `FloorHeight` = 300 cm), both of these are achievable
  without large dimension changes, so the fastest path is to jointly re-tune
  `StairRiser`/`StepsPerFlight`/landing height until the 210 cm headroom is satisfied everywhere.

### 15.3 Verification

- Can the character walk up every tread of each flight in order without getting blocked by
  geometry above at any point (verify by actually playtesting all the way to the top)?
- Does the opening cut into the floor slab line up exactly with the stair passage (i.e., do the
  opening from 15.1 and the flight plan coordinates from 11.2 come from the same shared
  reference — apply the "share the coordinate" principle from section 12.1 here too)?
- Is the roof the only floor left fully solid, with every other floor genuinely open?

---

## 16. Missing Core-Facing Wall on the End Unit (the Unit Adjacent to a Core)

Screenshot taken after the Chapter 15 shaft-void work: the unit directly adjacent to a core (the
"end unit") has an open wall on its core-facing side, so that unit's interior overlaps the stair
passage's space, both visually and physically.

### 16.1 Cause

Section 6.2's "inter-unit partition wall" only covers the boundary **between two units**. The
boundary at either end of the unit row — **between the end unit and a core** — has never been
explicitly covered by any section so far. The original section 5.2 design (a single central core)
implicitly assumed the core's own wall (section 10.1) would seal this boundary, but Chapter 14
changed the layout to "two cores with a unit row filling the span between them," and that
assumption was never re-verified for either core. On top of that, Core B's side was built via
mirroring (a 180° Transform Points), so it's quite likely the left/right sign got inverted,
putting the wall on the wrong side or omitting it entirely.

### 16.2 Fix

1. At each end of the unit row (the first unit adjacent to Core A, the last unit adjacent to
   Core B), explicitly add a wall of the same spec as section 6.2 (`Static Mesh Spawner`,
   thickness=`WallThickness`, height=`FloorHeight`) at **the boundary between the core and the
   unit row**. Treat this as its own new template — a "unit-to-core boundary wall" — separate
   from section 6.2's "inter-unit wall," so the two don't get conflated.
2. This wall's local X coordinate must be taken directly from "that core's inner-edge
   coordinate" — the exact same value already computed in section 14.2 when the unit row's
   start/end were recalculated relative to each core's inner edge. Don't re-estimate the
   coordinate; reuse the value that's already been computed, to avoid repeating the "computed
   independently, drifted apart" problem flagged in section 12.1.
3. Per the Chapter 13 constraint (no Loop support), build the Core A-side wall and the Core B-side
   wall as **two separate explicit branches**, and wire both into the final Merge. Since Core B's
   side went through mirroring, its left/right sign may be inverted — directly check the
   coordinates to confirm the wall is actually sealing off the core side (and wasn't accidentally
   placed at the opposite, exterior-facing wall position instead).

### 16.3 Verification

- At both Core A's and Core B's end units, is the wall fully sealed when looking from inside the
  unit toward the core (stairwell)?
- Walking from inside the end unit toward the core, does the character fail to cross into the
  stair passage (verify against collision, not just visuals)?
- Does adding this wall keep the unit interior blockout room (section 6.5)'s dimensions from
  encroaching into the core's space?

---

## 17. Core A/B Symmetry Audit · Unfinished Space Inside the Stairwell · Revisiting Headroom

Through Chapter 16, one individual omission or misplacement after another kept turning up on
Core B (the mirrored side) — a mistakenly-flagged missing Flight B, a mistakenly-flagged blocking
wall, a missing end-unit wall, and now a breached railing plus an asymmetric structure between the
two sides. At this point, **auditing Core A against Core B as a whole** is faster than patching
one item at a time.

### 17.1 Symptom 1 — Core A/B Asymmetry (a structure on the left is missing on the right, replaced by a hole in the railing)

This looks like another instance of the "left/right sign gets inverted during mirroring, landing
geometry in the wrong spot or not at all" problem already seen repeatedly in Chapter 13. The
difference this time is that **it's unclear how many more such omissions exist in the whole Core B
branch**, so treat this as an audit rather than another one-off fix:

1. List every template (point set) wired into the Core A branch, with its name, local
   coordinates, and size.
2. List every template wired into the Core B branch the same way.
3. First check whether the **counts match** — if Core A has an entry with no counterpart in Core
   B's list, that's the "missing structure."
4. If the counts match, cross-check each Core B item's coordinates against "Core A's coordinates
   mirrored across the building's centerline" one by one — is it just a sign flip, or did the
   wrong axis get mirrored?
5. Where something that should stay solid (like a parapet/railing) ended up treated as a door
   opening on Core B's side, that's often because a "this is a door" boolean or filter condition
   got inherited by mistake onto the railing template (section 10.1's door-opening filter logic
   possibly leaking onto the parapet template too).

### 17.2 Symptom 2 — a Genuinely "Empty" Unfinished Space Inside the Stairwell

The screenshot (the third image, marked "추가"/"add") shows a spot inside the stairwell that has
neither floor nor stairs — just an open gap. This is different from the shaft void intentionally
built in Chapter 15 (that one deliberately leaves open exactly where the stairs need to pass
through). This one is "a spot where something — stair or floor — should exist, and nothing does."

Fix: for each floor, break down Core A's and Core B's plan area and check that every X/Y point
falls into one of five categories: ① a Flight A tread, ② a Flight B tread, ③ the landing, ④ the
intentional shaft void from Chapter 15, or ⑤ the core's exterior wall/door/railing. Whatever
doesn't fall into any of these five is the empty spot from the screenshot — this usually happens
because one flight's point count/range falls short of covering the core's full depth and cuts off
partway, so start by checking whether the computed `StepsPerFlight` matches the actual number of
treads that got spawned.

### 17.3 Symptom 3 — Insufficient Headroom: Likely a Stair Layout Problem, Not a Floor-Count Problem

**Short answer up front: you probably don't need more floors.** In this project's dog-leg stair,
Flight A and Flight B sit at different local X positions (placed side by side rather than stacked
directly on top of each other), so this is unlikely to be a case of "the upper tread directly
caps the lower tread." It's much more likely that **the landing extends backward far enough to
overlap the last few treads of Flight A, and that overlap is exactly where the low ceiling is
happening** — this is precisely the headroom check flagged as not-yet-done back in section 15.2,
so this result isn't surprising.

If you try to solve this by raising `FloorHeight`, keep in mind that the minimum headroom near the
landing can drop to roughly "`FloorHeight`/2 − slab thickness." To get a clear 210 cm there, you
might need `FloorHeight` at 1.5× today's value or more (roughly 450 cm+) — unrealistically tall
for a residential floor. **So raising the floor height is not the recommended direction.**

Instead, work through it in this order:

1. For **every tread** of Flight A and Flight B, compute the actual vertical distance straight up
   to the first solid geometry it hits — measure it directly, don't estimate.
2. Pin down exactly which element (the landing? the opposite flight? one of the floor-slab pieces
   from Chapter 15?) is responsible for any point under 210 cm.
3. Adjust only that one element. Usually this comes down to recomputing the landing's start
   position to begin right after Flight A's last tread coordinate (with no overlap) — if the
   landing had been covering part of Flight A's own run, that overlap is exactly the blocked
   stretch.
4. If some point still falls short of 210 cm after fixing the specific culprit, only then consider
   a modest `FloorHeight` increase (e.g., 300 → roughly 330–350 cm) — don't jump to a large increase
   up front; rule out every other cause first and adjust by the smallest amount needed.

### 17.4 Actual Verified Results (some of the guesses above were wrong — kept for the record)

Once Claude Code actually measured things, some of the guesses in 17.1–17.3 held up and some
didn't. Recording the outcome here so the same wrong guess isn't repeated in a future debugging
pass.

- **17.1 (Core A/B asymmetry) was wrong.** Cross-checking all 130 points on each core showed they
  were perfectly symmetric via a pure translation (`ΔX=+4700`), and this graph has no
  Filter/Boolean node at all, so the "door filter leaked onto the railing" mechanism was never
  even possible. Core A and B were structurally identical the whole time — meaning the left/right
  asymmetry in that screenshot wasn't a code-level problem at all, so the first thing to do is
  re-shoot both sides from matching angles and see if it still looks asymmetric now (it may have
  been a stale render or just a different camera position).
- **17.2 (unclassified space inside the stairwell) was correct.** But the cause wasn't "part of it
  never got built" — it was that **the shaft void built in Chapter 15 opened up more than it
  needed to, also voiding the deep interior area the stairs never pass through (Y:384→800, the
  spot symmetric to the elevator side)**. Fixed by re-filling the floor there on floors 1–4, on
  both Core A and B. Lesson: section 15.1's "void only what's needed" principle needed to be read
  more narrowly than it was.
- **17.3 (insufficient headroom) had the right approach but the wrong suspect.** The landing
  overlapped **Flight B**, not Flight A as the document guessed (Flight A and B sit side by side
  rather than stacked, so Flight A never actually had a clearance problem). Fixed by shrinking
  `LandingDepth` from 150 to 80 cm, keeping the edge that connects to Flight A fixed at Y=234, and
  recomputing Flight B's 8 treads and the outer railing from that new value — minimum headroom
  improved from 167.5 cm to 223.75 cm. The "adjust one element, recompute what depends on it"
  approach itself held up fine.
- **Side finding (unresolved, cosmetic):** the outer railings are built at the full floor height
  (300 cm) rather than the project's `ParapetHeight` = 110 cm used everywhere else. Not a
  functional problem (if anything, it's even more fall-proof), but visually inconsistent with the
  other railings — worth conforming to 110 cm as a later polish pass.

---

## 18. Closing Out Chapter 17: Guardrail Confirmed Clean, and the Oversized Slit-Guard Panel Was a Real Headroom Bug

This chapter closes the two items Chapter 17 left open, using an autonomous Cowork↔Claude Code
loop (a local script repeatedly invoking Claude Code headlessly against a shared handoff/report
file pair, with the Cowork session writing each round's instructions and reading back the
evidence) rather than manual screenshot relaying. Two rounds were needed; both are now verified
closed with live data, not assumptions.

### 18.1 Guardrail continuity at the top/bottom floors — confirmed not a bug

Round 1 pulled every guardrail panel's point data straight from a forced clean regenerate
(`ExecuteGraphInstance` + `GetNodeDataView`). Result: the 20 slit-guard panels (2 panels × 2 cores
× 5 floors) are byte-identical across all floors and stack edge-to-edge with zero gap or overlap
(world Z 0–1500 across the 5-floor stack). There is no per-floor branching anywhere in
`PCG_Apartment_Floor`/`PCG_Apartment_Stair` that could truncate the top or bottom floor
differently from the middle ones. The apparent "gap" at the roof line and ground floor in the
original screenshot is the correct architectural endpoint (nothing above the roof or below the
ground to continue into), and the visual read was most likely the unlit blockout material plus
the elevator-shaft mass occluding the top flight from that camera angle.

Round 2 re-confirmed this visually with clean, unobstructed straight-on elevation shots of both
cores (`dev/shot_coreA_clean.png`, `dev/shot_coreB_clean.png`) — the dog-leg stair silhouette now
reads continuously from ground to roof on both Core A and Core B, mirror-symmetric as expected.
**No graph change was needed for this item — it was a camera-angle read, not a defect.**

### 18.2 The oversized slit-guard panel: not just cosmetic debt — a real Flight-B headroom bug

Chapter 17.4 had flagged the outer slit-guard panel (spanning the full 300 cm floor height instead
of `ParapetHeight` = 110 cm) as an "unresolved, cosmetic" side finding, since geometry inspection
alone couldn't confirm whether it actually obstructed movement. Round 2 resolved the ambiguity:

- **Fix applied**: in `PCG_Apartment_Stair`'s `StairLocalTemplate`, the two slit-guard panels
  (seed 219/220) were corrected from `z=150, scale.z=3` (spanning 0–300 cm) to `z=55, scale.z=1.1`
  (spanning 0–110 cm = `ParapetHeight`, resting on its own floor) — now matching spec and how the
  unit corridor parapet (section 6.4) is already built. Verified via fresh point data after
  regeneration: all 20 panels now sit exactly at `floor_base .. floor_base+110` on both cores, on
  disk (both the graph asset and the level were saved, not just live in the open editor).
- **Root cause confirmed, quantitatively**: before the fix, the panel's full 0–300 cm span
  overlapped Flight B's tread zone (which starts at local Z=150) at every single floor — this is
  exactly what produced the "collision point repeating identically at every floor" symptom
  originally reported. After the fix, an exact Z-range comparison against every Flight-B tread
  (`dev/check_overlap.py`) shows **zero remaining overlap anywhere**, with the closest approach
  being a 9 cm gap at the landing transition. Flight A was never affected either way — its
  clearance only ever depended on the panel's outer 8 cm edge, well clear of a centered walker,
  consistent with Chapter 17's original math.
- **Visually confirmed**: `dev/shot_stair_interior.png`, shot from inside Core A at the Flight B
  landing looking up the ascending flight, shows the treads continuing unobstructed in the direct
  sightline, with the corrected panel visible only as a flat side rail off the walking line.

**Conclusion: the ParapetHeight correction was not merely good hygiene — it fixed a real,
reproducible Flight-B headroom obstruction present at every floor, confirmed both by exact
geometry (zero overlap) and by a post-fix interior screenshot.** With this, all three findings from
Chapter 17 (asymmetry — was a false alarm per 17.4; unclassified shaft space — fixed per 17.4; and
now this headroom bug) are closed.

### 18.3 Process note: what the autonomous loop demonstrated well

Both rounds followed the same evidence discipline established since Chapter 13 — no claim was
made from screenshot appearance alone; every finding was backed by live `GetNodeDataView` point
data, an explicit overlap computation, or a purpose-shot screenshot from known coordinates. Round
1 explicitly declined to guess whether the oversized panel was actually blocking movement, and
proposed the exact follow-up needed to find out — round 2 then did precisely that follow-up and
reported the corrected, evidence-based answer. This is the intended failure mode for the
loop's `STATUS: CONTINUE`/`BLOCKED` protocol: uncertainty gets carried forward as a concrete next
step, not papered over with an assumption.

A queued next milestone — temporary Cube-primitive placeholders for railing bars, window frames,
and AC condenser units (slots for the user to later swap in real assets) — is deliberately **not**
auto-started after this fix; it awaits explicit human review of this round's result first.

---

## 19. Phase 2: Placeholder Blockout for Railing Bars, Window Trim, and AC Units

With Phase 1's structural bugs closed, the user approved starting the queued Phase 2 milestone: a
purely additive placeholder pass, not a materials/styling pass, so the user can later swap each
placeholder for a real asset without re-deriving placement or scale. This was completed in a
single round of the same autonomous loop, with default engine primitives only
(`/Engine/BasicShapes/Cube`, default materials).

### 19.1 A stale doc note, corrected

Before making any change, the round inspected the live graph structure and found that
`UnitLocalTemplate`'s back wall (the unit's exterior facade, opposite the corridor) was **already**
split into a 0–90 cm sill and a 210–300 cm lintel, leaving a genuine 120 cm window opening between
them. This contradicts this document's own chapter 6.5/9 notes, which called window openings
"deferred" — they must have been added during the chapter 10 facade-detail pass without the doc
being updated. Recorded here so this doesn't get re-litigated: **window openings already exist in
`PCG_Apartment_UnitRow`**, so placing trim and an AC unit there was a placement task, not a design
decision requiring a human call (the handoff's BLOCKED escape hatch for "no window openings exist
yet" turned out not to be needed).

### 19.2 What was built

- **Railing bars** (item 1): the solid `ParapetHeight`=110 cm parapet block (both the unit corridor
  parapet, section 6.4, and the stair slit-guard panels fixed to spec in chapter 18) was **replaced**
  with a row of thin vertical bars — 4×4 cm cross-section, 110 cm tall. Unit corridor bars are spaced
  20 cm apart across each unit's 700 cm frontage (35 bars/unit, with a deliberate small gap at the
  unit seam so adjoining units' bars don't double up); stair bars use 16 cm spacing chosen so the
  224 cm run divides evenly (15 bars per flight side, both endpoints landing exactly on the original
  panel's edges). Chosen as a full replacement rather than bars-in-front-of-the-solid-block, since
  keeping both would double up collision and defeat the point of a see-through railing. This needed
  no Loop Subgraph workaround beyond what the project already does elsewhere — the bar list is
  computed as literal baked points, the same technique already used for the door/window segment
  splits (chapters 6.3, 10.1).
- **Window frame trim** (item 2): four thin 5 cm trim Cubes per unit tracing the existing opening's
  perimeter (bottom at Z=90, top at Z=210, sides at the opening's left/right edges), centered on the
  wall's outer face.
- **AC condenser unit** (item 3): one 80×30×60 cm Cube per unit, wall-mounted flush against the
  exterior face just below the window sill. Wall-mounted rather than floor-resting because this
  facade is the building's outer skin, not a walkable balcony surface — there's no floor beneath it
  on any floor.

### 19.3 Verification

`ExecuteGraphInstance` returned zero messages after both `UpdateNode` calls. The full merged output
(1963 points — an exact match for 389 floor-local points × 5 floors + 18 stairwell-slab points, so
nothing else in the graph was disturbed) was filtered by each new element's scale signature:

- Railing bars: 1350 total (1050 unit-corridor + 300 stair). A first pass with a naive
  positive-scale filter found only 1200 — the missing 150 turned out to be Core B's bars correctly
  inheriting the pre-existing mirrored (negative X-scale) convention from `StairAnchorPoint`
  (already used by the original treads/panels) rather than a bug. Both cores confirmed present once
  the sign convention was accounted for.
- Window trim: 60 horizontal + 60 vertical pieces — exact match for 2 × 6 units × 5 floors.
- AC units: 30 — exact match for 6 units × 5 floors, sampled at the expected per-floor Z offsets.

Both `PCG_Apartment_UnitRow` and `PCG_Apartment_Stair` graph assets and the `AbandonedSchool` level
were saved to disk (`is_dirty` false afterward, on-disk mtimes updated) — not left only live in the
open editor.

Screenshots confirming all three elements post-regenerate: `dev/shot_corridor_railing_bars.png`
(evenly-spaced bars across a unit seam), `dev/shot_stair_railing_bars.png` (both stair flights'
guard rails as bar rows, comparable to chapter 18's solid-panel silhouette), and
`dev/shot_unit_window_ac_angle.png` / `dev/shot_unit_window_ac.png` (window opening with visible
trim border, AC unit mounted beside it, corridor bars visible through the opening in the
background).

### 19.4 What's next

Per the handoff's completion rule, no further aesthetic milestone was auto-started after this one.
This was placeholder geometry only (default engine materials, no color/texture work) — real asset
integration (actual railing, window, and AC meshes/materials) is a manual next step for the user to
direct once they've reviewed the result in-editor.

---

## 20. Phase 3: Rescale, Railing Simplification, Open-Air Stair Cleanup, Elevator Core, Main Gate, Doubled Floor Count

After reviewing the Phase 2 screenshots, the user came back with two kinds of feedback: four
corrections to the existing output and three entirely new structures. Since this round changed the
core dimensions themselves (`UnitWidth`, `FloorHeight`), none of the old formulas could just be
reused for everything downstream (door/window segment widths, railing lengths, stair step counts) —
they all had to be re-derived from the live graph values. The work was split into six ordered
milestones (3A–3F), each with its own regenerate, point-data verification, screenshot, and interim
report.

### 20.0 A blocker before the work could even start: two bugs in the loop driver script

Phase 3's handoff was much longer than earlier rounds (about 10.5KB), which pushed
`run-claude-loop.ps1` (v2) past a limit it had never hit before: it passed the entire handoff
content as a literal command-line argument to `claude -p`. Since `claude` resolves through a `.cmd`
shim on Windows, that argument passes through `cmd.exe`'s command-line length limit (~8191
characters) and got truncated mid-sentence — Claude Code itself noticed and reported that the
handoff looked cut off. On top of that, this same round never actually updated `claude-report.md`,
yet the script read the **stale "STATUS: COMPLETE" line left over from Phase 2** in that file and
incorrectly concluded the work was done, stopping the loop before anything happened.

Both were fixed in the script (v3):

- **Truncation bug**: instead of passing the whole handoff as an argument, the script now passes a
  short, fixed instruction telling Claude Code to read `dev/claude-handoff.md` itself. Claude Code
  already has `Read` in `--allowedTools`, so it can load the file directly — this removes the
  command-line length ceiling entirely, no matter how long a future handoff gets.
- **Stale-report bug**: the script now records `claude-report.md`'s modification time before
  invoking Claude, compares it after the round, and refuses to trust the STATUS line (or stop the
  loop on it) unless the file actually changed that round.

### 20.1 Milestone 3A — Rescale (`UnitWidth`×2, `FloorHeight`×1.5)

- `UnitWidth`: 700cm → **1400cm**. `FloorHeight`: 300cm → **450cm**.
- Before touching anything, `GetGraphStructure` on all four graphs (`Main`/`Floor`/`UnitRow`/
  `Stair`) revealed something not previously documented: **the exposed User Parameters were never
  actually wired to anything — every dimension is baked as a literal coordinate in a `Create
  Points` node** (the `FloorOrigins` node's own comment said "not yet wired"). So this milestone
  meant hand-deriving the formula behind every baked constant, not moving a parameter slider.
- Several relationships that had never been written down anywhere were derived and verified this
  round (now captured in `dev/phase3_model.py`): the core-center offset
  (`UnitsPerSide*UnitWidth + CoreWidth/2`), the stair anchor's X position (`±CoreWidth/4` from the
  core center), and the unit-to-core boundary wall's X position. Each formula was validated by
  first reproducing the exact **pre-change** baked values before it was trusted to compute new ones.
- The window opening (sill 0–90cm, opening 90–210cm) was kept as a **fixed absolute** dimension
  rather than scaling with `FloorHeight` — only the lintel above it stretches to the new 450cm
  ceiling, since real windows don't grow taller with the ceiling.
- `StepsPerFlight = round((FloorHeight/2)/StairRiser)` was recomputed for the new floor height
  (225cm per flight); `StairRiser` = 18.75cm needed no adjustment since 225/18.75 = 12 exactly.
- Verification: `ExecuteGraphInstance` → 0 messages; total point count **3233**, an exact match to
  the hand-computed formula. Screenshot: `dev/shot_3a_rescale.png` — visibly wider window spacing
  (700cm → 1400cm) and taller floor bands. Phase 1's headroom fix was re-confirmed unaffected,
  since it's keyed off `ParapetHeight` (unchanged), not `FloorHeight`.

### 20.2 Milestone 3B — Collapse multi-bar railings into one box per run

Phase 2's dense row of vertical bars (35 per unit corridor run, 15 per stair flight side) each
stood in for one piece of a real asset — but the user decided the real railing will be a single
prefab per run. Each run was replaced with one thin long box (8cm thick, `ParapetHeight` tall,
spanning the run's full length): one per unit corridor run, one per stair flight side.

- Verification: point count dropped from 3233 to **743**, an exact match — confirming nothing else
  changed besides the bar-row-to-single-box collapse.
- Screenshot comparison: `dev/shot_3b_railbox_close2.png` (new — a smooth unbroken panel at close
  range) versus `dev/shot_corridor_railing_bars.png` (Phase 2 — fine repeated vertical striping at
  the same distance) makes the "many → one" change visually obvious.

### 20.3 Milestone 3C — Match stair Y-depth to the building, remove the wall blocking the stair

**Depth mismatch.** Against the building's full Y depth (`UnitDepth + CorridorWidth` = 980cm), the
stair's own occupied Y range was still only 416cm (about 42%) even after 3A. The lever was
`LandingDepth` (reduced to 80cm back in section 17.4) — the flight run length itself
(`StairTreadDepth × StepsPerFlight` = 336cm) is a real physical stair dimension and wasn't touched.
Solving for a landing that reaches almost to the back wall gave `LandingDepth` = **440cm**, leaving
a deliberate 14cm clearance rather than a flush seam.

**Wall blocking the stair.** Converting every point in `CoreLocalTemplate` into the stair's own
coordinate frame and checking for overlap turned up seed 105: a full-floor-height wall panel with
no door gap cut into it, sitting squarely inside the stair's footprint — the same class of bug as
section 13.2 ("a wall left over from an old coordinate system"), this time confirmed by measurement
rather than assumed. It was removed entirely, leaving the stair's side fully open, matching the
reference photos' open-air read.

- Verification: point count 743 → **733** (an exact 2-points-per-core × 5 floors × 2 cores drop,
  matching the one removed wall point per core per floor). Screenshot:
  `dev/shot_3c_stair_depth.png` — the zigzag flights and the much deeper cantilevered landing now
  read as deep as the building mass, with no wall crossing in front of the stair. Full
  material/styling match to the reference photos was explicitly noted as out of scope for this
  primitives-only round.

### 20.4 Milestone 3D — New dedicated elevator core at the building center

The building's exact center (X=0) is where the two innermost units' own party wall already sits —
zero clearance for a new core without pushing the unit rows outward. Claude Code considered
reporting this as `STATUS: BLOCKED`, but treated the symmetric outward shift as the same kind of
parametric recompute 3A already did wholesale, rather than a genuine structural fork — so it picked
a default and documented the reasoning (the user had already approved a "dedicated core" approach
ahead of time).

- New parameter `ElevatorCoreWidth` = 300cm (narrower than the existing 500cm end-core `CoreWidth`
  since this core only needs to fit an elevator, not a stair). Every unit/core/stair anchor shifted
  outward by `CenterOffset` = 150cm.
- The new core (`ElevatorCoreLocalTemplate`) was built open-sided from the very start, applying the
  3C-2 lesson immediately instead of reintroducing the same class of wall-overlap bug.
- Overlap check: the innermost unit's edge (150cm) and the elevator core's boundary (150cm) meet
  exactly — 150.0 == 150.0 — verified arithmetically, not just by eye.
- Verification: point count 733 → **763** (the +30 matches the new core's contribution exactly).
  Screenshot: `dev/shot_3d_elevcore.png` — a clean vertical gap (sky visible through it) splits the
  facade, with a lobby-slab ledge crossing it at each floor line, confirming the new core reads as
  distinct rather than overlapping.

### 20.5 Milestone 3E — Ground-floor main gate

Because 3D's elevator core deliberately has no parapet at its Y-plane, a 300cm
(`ElevatorCoreWidth`) gap already existed at the building's center. The gate opening was sized to
250cm (2.5×`DoorWidth`, within the handoff's 2–3× guidance), leaving 25cm clearance on each side.

- `Main:MainGateGround` (two posts + a lintel) was stamped onto the ground floor only.
- Since upper floors (1–4) don't get a gate but would otherwise inherit the same open 300cm gap
  (a safety issue on a normal corridor edge), a plain filler rail (`Main:CenterRailingUpper`, same
  style as the unit corridor rail) was added on those floors — not explicitly requested by the
  handoff, but a direct consequence of "ground floor only."
- Verification: point count 763 → **770** (gate: +3, filler rail: +4, exact match). Screenshot:
  `dev/shot_3e_gate.png` — a distinct post-and-lintel frame with an open, sky-visible passage
  behind it.

### 20.6 Milestone 3F — Double the floor count (`FloorCount` 5 → 10)

The structurally safest change of the six, since every other milestone was already built to repeat
parametrically per floor — only `Main:FloorOrigins` (10 points) and `Main:FloorOrigins_Upper` (9
points) needed editing.

- Verification: point count **1540**, an exact match to the full hand-derived formula
  (`(13×6 + 5×2 + 1 + 1 + 27×2 + 5)×10 + (2 + 4×9 + 3 + 1×9) = 1490 + 50 = 1540`). Confirmed there's
  no separate roof cap above the top floor, so there's no "stair core clips the roof" risk to check
  for. Screenshot: `dev/shot_3f_full_elevation.png` — the full 10-floor elevation.

### 20.7 Final parameter values

| Parameter | Value | Note |
|---|---|---|
| `UnitWidth` | 1400cm | 3A: doubled from 700 |
| `FloorHeight` | 450cm | 3A: 1.5× from 300 |
| `FloorCount` | 10 | 3F: doubled from 5 |
| `LandingDepth` | 440cm | 3C: recomputed from 80 |
| `StepsPerFlight` | 12 | 3A: recomputed from 8 |
| `ElevatorCoreWidth` (new) | 300cm | 3D |
| Gate opening width (not a graph param) | 250cm | 3E |

All other parameters (`UnitsPerSide`, `CoreWidth`, `CorridorWidth`, `UnitDepth`, `DoorWidth`,
`WallThickness`, `ParapetHeight`, `StairRiser`) are unchanged. **Worth repeating**: these values
were also recorded on the graphs' User Parameters for documentation, but the actual geometry is
still baked as literal coordinates in each `Create Points` node — changing a parameter slider alone
won't move anything. The next time any of these dimensions need to change, reuse the verified
formulas in `dev/phase3_model.py` and follow the same process (check live values → re-derive via
the formula → `UpdateNode`).

### 20.8 What's next

All six milestones are complete, verified, and saved to disk. Per the handoff's completion rule, no
further work was auto-started. Full material/styling match to the reference photos, real elevator
car/door assets, and real gate styling are all left out of scope for this primitives-only round —
manual next steps for the user to direct once they've reviewed the result in-editor.

---

## 21. Phase 4: Six Stair/Floor Bugfixes, New Front Windows (BP_Glass), Door Infill

The user walked through the Phase 3 result in-editor and sent back 8 screenshots marked up in red —
6 corrections to what was there, plus 2 new additions. Three genuinely ambiguous points (what
"center" means for the door-offset fix, which direction the window reposition should go, and how
exactly to close off the space above the door) were resolved with AskUserQuestion before writing
the handoff. Eight milestones (4A–4H) were worked in order, and once again the whole phase finished
in a **single round** of the autonomous loop (about 35 minutes, $15.03).

### 21.1 Milestone 4A — Both stair cores had no corridor rail at all

Live data confirmed each unit's own rail (3B) correctly stops flush at the unit/core boundary — but
the core (stairwell) itself, across its full 500cm frontage, **never had a rail to begin with**.
That's what the "looks disconnected" feedback was actually pointing at. One rail box was added to
`CoreLocalTemplate`, spanning the full core width, which fixed both cores on every floor at once.
Upper floors also had a gap in the corridor floor right in front of the stair opening, filled by a
new `CoreVoidCorridorFill_Upper` (ground floor already covered by the existing
`StairwellSlab_Ground`). Point count 1540→1578, an exact formula match.

### 21.2 Milestone 4B — No landing floor at the back of the stairs (Flight A)

Coordinate comparison confirmed `Main:StairwellSlab_Upper`'s existing "arrival platform" patch only
covered Flight B's column, never Flight A's — exactly the "front has it, back doesn't, feels
unstable" symptom the user flagged. A mirrored patch was added on Flight A's own column. Point
count 1578→1596.

### 21.3 Milestone 4C — Widen the corridor ×1.5

`CorridorWidth`: 180cm → 270cm. Every node depending on it was recomputed (unit floor/rail, both
end-core lobby slabs, the elevator-core lobby slab, the gate/filler rail, and even 4A's new
upper-floor fill). Per the handoff's request, the shift in section 17's building-depth ratio (980cm
→ 1070cm) was noted but not acted on further, since the stair's own dimensions weren't touched.
Point count unchanged (1596 — repositioning only).

### 21.4 Milestone 4D — Offset each unit's entrance door 30% from its own center

AskUserQuestion first confirmed "center" means each unit's own frontage center, not the building's.
Offset = `0.3 × (UnitWidth/2 − DoorWidth/2)` = 195cm. Because the unit template is mirrored for the
opposite side, a single template-space offset direction was verified algebraically to move every
unit's door the same way relative to that unit's own distance from the building center — either
direction would have been equally valid structurally, but "toward each unit's own nearest core" was
picked for how it reads. The door-flanking wall segments were recomputed (845cm/455cm), both
comfortably clear of the side walls. Point count unchanged (1596).

### 21.5 Milestone 4E — Elevator core was missing its ground-floor slab

Investigation showed the elevator core's lobby-side slab was already present every floor — the
actual gap was that the elevator core never got the ground-floor-only full fill the two stair cores
get (`StairwellSlab_Ground`, which closes off the stair-void side at ground level only). The
elevator shaft side is intentionally open every floor by design (3D), so it isn't identical to the
stair cores' case, but it was still missing that one ground-floor exception. Added
`Main:ElevatorCoreSlab_Ground` to fix it. Point count 1596→1597.

### 21.6 Milestone 4F — Reposition the back-wall window near the ceiling

AskUserQuestion confirmed "move the window up near the ceiling" was the right reading. The window
moved from sill/top 90/210cm to **305/425cm** (120cm opening height kept, 25cm clearance under the
450cm ceiling). The trim (4 pieces), vertical trim bars, and the AC unit (moved to z=270, keeping
its 35cm gap under the sill) were all recomputed to follow the window to its new spot. This change
does not apply to 4G's new front windows — those are a separate design. Point count unchanged
(1597).

### 21.7 Milestone 4G — New: two front (corridor-side) windows using the real BP_Glass asset

For the first time in this project, an actual asset was spawned instead of a Cube placeholder.
`BP_Glass` was inspected first — it inherits from `BP_Breakable_Base` and carries a
`GeometryCollectionComponent` (not a plain static mesh), so it needed PCG's **Spawn Actor** node
rather than the Static Mesh Spawner used everywhere else. A temporary instance was spawned to
measure its collision box (~192×8×160cm) and then deleted, and that measurement drove the fit scale
for each opening. Openings are 150×120cm (reusing the original centered scheme, not 4F's
repositioned one — that's deliberate, they're separate designs), two per unit
(x=-350, x=+400, confirmed clear of 4D's offset door). Verified via
`Main:SpawnFrontWindowGlass` (120 points = 6 units × 10 floors × 2 windows) and `find_actors`
confirming 120 real `BP_Glass_C` actors in the level. Total blockout point count 1597→1957.

### 21.8 Milestone 4H — Fill in above the door opening

AskUserQuestion confirmed "the same treatment as the windows — open only up to door height, wall
above that" was the right approach. The door opening is now capped at 210cm, with a lintel/infill
from there to the 450cm ceiling — computed against 4D's new (offset) door position, since the
handoff required this milestone to run after 4D. Point count 1957→2017.

### 21.9 Verification

All eight milestones regenerated with `ExecuteGraphInstance` → 0 messages, and every point count
matched its hand-derived formula exactly. Confirmed visually via screenshots: the core rail now
runs unbroken into the unit rail (4A), the door is capped like a window with real glass actors
visible on both sides (4H), and a wide elevation shows the corridor visibly wider with windows
regularly placed near the ceiling on every floor (4C). All four graph assets and the level are
saved (`is_dirty` false). Per the handoff's completion rule, no further work was auto-started.

---

## References (Sources)

- [Procedural Content Generation Overview — Epic official docs (5.8)](https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-overview?lang=en-US)
- [Procedural Content Generation Framework Node Reference — Epic official docs (5.8)](https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-framework-node-reference-in-unreal-engine)
- [Procedural Content Generation (PCG) Biome Core and Sample Plugins Reference Guide — Epic official docs (5.8)](https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-pcg-biome-core-and-sample-plugins-reference-guide-in-unreal-engine)
- [Procedural Room Generation with Splines and PCG — Epic Community Tutorial](https://dev.epicgames.com/community/learning/tutorials/eZVR/procedural-room-generation-with-splines-and-pcg-in-unreal-engine)
- [Electric Dreams Environment — PCG Sample Project (Epic)](https://www.unrealengine.com/electric-dreams-environment)
- [How to use Loop Subgraphs in PCG? — Epic Developer Community Forums](https://forums.unrealengine.com/t/how-to-use-loop-subgraphs-in-pcg/1349454)
- [PCG: Presets and Loops — Medium (Iri Shinsoj)](https://medium.com/@shinsoj/pcg-presets-and-loops-dae144397e6f)
- [PCG Instanced Static Mesh not updating Nav Mesh — Epic Developer Community Forums](https://forums.unrealengine.com/t/pcg-instanced-static-mesh-not-updating-nav-mesh/2667327)
- [Navigation Mesh Resolutions User Guide — Epic official docs (5.8)](https://dev.epicgames.com/documentation/unreal-engine/navigation-mesh-resolutions-user-guide)
- [Corridor-type vs. stairwell-type apartment structure comparison — Houseinfo (Korean)](https://houseinfo.kr/blog/0085-apartment-structure-comparison/)
- [Corridor-type vs. stairwell-type apartment features and trade-offs — Wonymoney (Korean)](https://wonymoney.co.kr/real-estate/%EB%B3%B5%EB%8F%84%EC%8B%9D-%EA%B3%84%EB%8B%A8%EC%8B%9D-%EC%95%84%ED%8C%8C%ED%8A%B8-%ED%8A%B9%EC%A7%95%EA%B3%BC-%EC%9E%A5%EB%8B%A8%EC%A0%90/)
