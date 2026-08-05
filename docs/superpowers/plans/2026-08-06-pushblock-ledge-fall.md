# BP_PushBlock Ledge-Fall Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `BP_PushBlock` fall (instead of floating) when pushed off a ledge, and make the
player's pushing state end the instant that happens.

**Architecture:** Blueprint-only change to `Content/Blueprints/Actor/Common/BP_PushBlock.uasset`,
made through the Unreal Editor's live Blueprint graph via the `unreal-mcp` server's
`editor_toolset.toolsets.blueprint.BlueprintTools` toolset (the "Blueprint DSL" tools:
`read_graph_dsl` / `write_graph_dsl` / `add_variable` / `add_function_graph` /
`add_function_param` / `compile_blueprint`). No C++ is touched. Two new member variables track
fall state, three new functions encapsulate the new logic, and `EventGraph` is rewritten to call
them.

**Tech Stack:** Unreal Engine Blueprint (visual scripting), edited via the `mcp__unreal-mcp`
MCP server's Blueprint Graph DSL (an S-expression scripting syntax that compiles to Blueprint
graph nodes — see `get_graph_dsl_docs` on `editor_toolset.toolsets.blueprint.BlueprintTools`
for the full grammar reference).

## Global Constraints

- No C++/native code — every change is made by editing `BP_PushBlock`'s Blueprint graphs.
- Reuse the existing `FloorBumpTolerance` variable for the ground-check trace distance — do not
  add a separate tolerance variable.
- Do not duplicate the "end the push" sequence (`SetIsPushed false` → `Ac_Push::EndPush` →
  `SetPushingPlayer none`) — factor it into the new `Stop Pushing` function and call it from both
  places that need it.
- All MCP tool calls below use `toolset_name: "editor_toolset.toolsets.blueprint.BlueprintTools"`
  unless otherwise noted (asset load/save calls use
  `"editor_toolset.toolsets.asset.AssetTools"`).
- The Blueprint asset reference for every step is
  `{"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock"}`.

---

### Task 1: Add the two new member variables

**Files:**
- Modify (via MCP, not a text edit): `Content/Blueprints/Actor/Common/BP_PushBlock.uasset`

**Interfaces:**
- Produces: member variable `FallSpeed` (float, default `0.0`) — accumulated downward speed
  while airborne.
- Produces: member variable `IsFalling` (bool, default `false`) — true while the block's pivot
  has no floor under it.

- [ ] **Step 1: Add `FallSpeed`**

Call `mcp__unreal-mcp__call_tool`:
```json
{
  "tool_name": "add_variable",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "blueprint": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock"},
    "name": "FallSpeed",
    "type_name": "float"
  }
}
```

- [ ] **Step 2: Add `IsFalling`**

Call `mcp__unreal-mcp__call_tool`:
```json
{
  "tool_name": "add_variable",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "blueprint": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock"},
    "name": "IsFalling",
    "type_name": "bool"
  }
}
```

- [ ] **Step 3: Verify**

Call `list_variables` with the same `blueprint` argument. Confirm the result now includes
`PushingPlayer`, `PushDirection`, `IsPushed`, `PushDirectionCheckLimit`, `PushMarginRatio`,
`Mass`, `FloorBumpTolerance`, `FallSpeed`, `IsFalling`.

- [ ] **Step 4: Commit is not applicable here** — Blueprint state lives in the editor's in-memory
  asset until Task 6 saves it. Do not run `git commit` until Task 6 completes and the asset is
  saved to disk.

---

### Task 2: Add the `Is Grounded` function

**Files:**
- Modify (via MCP): `Content/Blueprints/Actor/Common/BP_PushBlock.uasset`

**Interfaces:**
- Consumes: member variable `FloorBumpTolerance` (float, pre-existing).
- Produces: function `Is Grounded` — DSL call id `CallFunction|IsGrounded`, no params, returns
  bool (output pin named `bGrounded`). Used by Task 5.

- [ ] **Step 1: Create the function graph**

Call `add_function_graph`:
```json
{
  "tool_name": "add_function_graph",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "blueprint": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock"},
    "graph_name": "Is Grounded"
  }
}
```
This returns a graph ref, e.g.
`{"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock:Is Grounded"}`. Use that
exact ref for the next two steps.

- [ ] **Step 2: Add the bool return param**

Call `add_function_param`:
```json
{
  "tool_name": "add_function_param",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "graph": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock:Is Grounded"},
    "param_name": "bGrounded",
    "param_type": "bool",
    "input_param": false
  }
}
```

- [ ] **Step 3: Write the function body**

Call `write_graph_dsl`:
```json
{
  "tool_name": "write_graph_dsl",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "graph": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock:Is Grounded"},
    "code": "(fn IsGrounded ()\n  (bind loc (Transformation|GetActorLocation))\n  (bind tol (Variables|Default|GetFloorBumpTolerance))\n  (bind offset (Math|Vector|MakeVector 0.0 0.0 (- tol)))\n  (bind endLoc (Math|Vector|vector+vector loc offset))\n  (bind (_outhit _hit) (Collision|LineTraceByChannel :Start loc :End endLoc :TraceChannel \"TraceTypeQuery1\" :bIgnoreSelf true))\n  (return _hit))"
  }
}
```
This traces straight down from the actor's pivot (`GetActorLocation`) by `FloorBumpTolerance` on
the default `Visibility` channel, ignoring the block's own collision, and returns whether
anything was hit.

- [ ] **Step 4: Verify**

Call `read_graph_dsl` on the same graph ref and confirm the returned script matches the intent
above (one `fn IsGrounded` with a line trace and a `return`).

---

### Task 3: Add the `Get Effective Gravity Z` function

**Files:**
- Modify (via MCP): `Content/Blueprints/Actor/Common/BP_PushBlock.uasset`

**Interfaces:**
- Produces: function `Get Effective Gravity Z` — DSL call id `CallFunction|GetEffectiveGravityZ`,
  no params, returns float (output pin named `GravityZ`). Used by Task 5.

- [ ] **Step 1: Create the function graph**

```json
{
  "tool_name": "add_function_graph",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "blueprint": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock"},
    "graph_name": "Get Effective Gravity Z"
  }
}
```

- [ ] **Step 2: Add the float return param**

```json
{
  "tool_name": "add_function_param",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "graph": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock:Get Effective Gravity Z"},
    "param_name": "GravityZ",
    "param_type": "float",
    "input_param": false
  }
}
```

- [ ] **Step 3: Write the function body**

```json
{
  "tool_name": "write_graph_dsl",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "graph": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock:Get Effective Gravity Z"},
    "code": "(fn GetEffectiveGravityZ ()\n  (bind ws (Utilities|World|GetWorldSettings self))\n  (bind overridden (|GetbGlobalGravitySet ws))\n  (if overridden\n    (return (|GetGlobalGravityZ ws))\n    (else\n      (return -980.0))))"
  }
}
```
This reads the level's `WorldSettings`: if gravity is overridden (`bGlobalGravitySet`), it
returns `GlobalGravityZ`; otherwise it returns Unreal's standard default, `-980.0` (this project
does not override gravity anywhere in `Config/`, so `-980.0` is what's actually in effect today).

- [ ] **Step 4: Verify**

Call `read_graph_dsl` on the graph ref and confirm it round-trips the logic above.

---

### Task 4: Add the `Stop Pushing` function

**Files:**
- Modify (via MCP): `Content/Blueprints/Actor/Common/BP_PushBlock.uasset`

**Interfaces:**
- Consumes: member variables `PushingPlayer`, `IsPushed` (pre-existing); the project's
  `Ac_Push::EndPush` custom event (pre-existing, called the same way the current `EventGraph`
  already calls it).
- Produces: function `Stop Pushing` — DSL call id `CallFunction|StopPushing`, no params, no
  return value. Used by Task 5 in two places.

- [ ] **Step 1: Create the function graph**

```json
{
  "tool_name": "add_function_graph",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "blueprint": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock"},
    "graph_name": "Stop Pushing"
  }
}
```
No `add_function_param` call is needed — this function takes no inputs and returns nothing.

- [ ] **Step 2: Write the function body**

```json
{
  "tool_name": "write_graph_dsl",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "graph": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock:Stop Pushing"},
    "code": "(fn StopPushing ()\n  (bind pushingPlayer (Variables|Default|GetPushingPlayer))\n  (bind acPush (|GetAc_Push pushingPlayer))\n  (Variables|Default|SetIsPushed false)\n  (Class|AcPush|EndPush acPush)\n  (Variables|Default|SetPushingPlayer 0))"
  }
}
```
This is exactly the "end the push" sequence that already exists inline in today's `EventTick`
(when the player stops holding the push direction), extracted so it can be reused.

- [ ] **Step 3: Verify**

Call `read_graph_dsl` on the graph ref and confirm it matches.

---

### Task 5: Rewrite `EventGraph`

**Files:**
- Modify (via MCP): `Content/Blueprints/Actor/Common/BP_PushBlock.uasset`

**Interfaces:**
- Consumes: `CallFunction|IsGrounded` (Task 2), `CallFunction|GetEffectiveGravityZ` (Task 3),
  `CallFunction|StopPushing` (Task 4), variables `FallSpeed`/`IsFalling` (Task 1), plus all
  pre-existing variables/functions (`IsPushed`, `PushDirection`, `PushingPlayer`,
  `FloorBumpTolerance`, `IsPushPositionValid`, `GetDirectionalAxis`, `IsKeepPushDirection`,
  `Ac_Push::DoPush`, `Ac_Push::GetPushSpeedResult`).
- Produces: the final `EventHit` and `EventTick` behavior described in the design spec.

This task must run **after** Tasks 1–4 so the functions/variables it calls already exist —
`write_graph_dsl` will fail to resolve `CallFunction|IsGrounded` etc. otherwise.

- [ ] **Step 1: Read the current EventGraph as a sanity baseline**

Call `read_graph_dsl` with
`{"graph": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock:EventGraph"}}`
and confirm it still matches the original two-event script (no manual edits happened since
brainstorming). If it doesn't match, stop and investigate before proceeding.

- [ ] **Step 2: Write the replacement EventGraph**

Call `write_graph_dsl`:
```json
{
  "tool_name": "write_graph_dsl",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "graph": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock:EventGraph"},
    "code": "(event Collision|EventHit (MyComp Other OtherComp bSelfMoved HitLocation HitNormal NormalImpulse Hit)\n  (bind _asbp_player_heroine (Utilities|Casting|CastToBP_Player_Heroine Other))\n  (if (and (not (Variables|Default|GetIsPushed)) (not (Variables|Default|GetIsFalling)))\n    (Variables|Default|SetPushingPlayer _asbp_player_heroine)\n    (bind _ispushpositionvalid (CallFunction|IsPushPositionValid HitLocation HitNormal))\n    (if _ispushpositionvalid\n      (bind _outvector (CallFunction|GetDirectionalAxis HitNormal))\n      (Variables|Default|SetIsPushed true)\n      (bind _output_get (Variables|Default|SetPushDirection _outvector))\n      (Class|AcPush|DoPush (Variables|Default|GetPushingPlayer) self _output_get HitLocation))))\n\n(event EventTick (DeltaSeconds)\n  (bind _grounded (CallFunction|IsGrounded))\n  (if _grounded\n    (Variables|Default|SetFallSpeed 0.0)\n    (Variables|Default|SetIsFalling false)\n    (if (Variables|Default|GetIsPushed)\n      (bind _floorbumptolerance (Variables|Default|GetFloorBumpTolerance))\n      (bind _upoffset (Math|Vector|MakeVector 0.0 0.0 _floorbumptolerance))\n      (bind _pushingplayer (Variables|Default|GetPushingPlayer))\n      (bind _ac_push (|GetAc_Push _pushingplayer))\n      (bind _iskeep (CallFunction|IsKeepPushDirection))\n      (if _iskeep\n        (bind _pushspeedresult (Class|AcPush|GetPushSpeedResult _ac_push self))\n        (Transformation|AddActorWorldOffset _upoffset true)\n        (Transformation|AddActorWorldOffset (Math|Vector|vector*vector (Math|Vector|vector*vector (Math|Vector|Normalize (Variables|Default|GetPushDirection)) DeltaSeconds) _pushspeedresult) true)\n        (Transformation|AddActorWorldOffset (Math|Vector|vector*vector _upoffset \"-1, -1, -1\") true)\n        (else\n          (CallFunction|StopPushing)))))\n    (else\n      (if (Variables|Default|GetIsPushed)\n        (CallFunction|StopPushing))\n      (Variables|Default|SetIsFalling true)\n      (bind _gravityz (CallFunction|GetEffectiveGravityZ))\n      (bind _newfallspeed (+ (Variables|Default|GetFallSpeed) (* _gravityz DeltaSeconds)))\n      (Variables|Default|SetFallSpeed _newfallspeed)\n      (Transformation|AddActorWorldOffset (Math|Vector|MakeVector 0.0 0.0 (* _newfallspeed DeltaSeconds)) true))))"
  }
}
```

- [ ] **Step 3: Verify by reading it back**

Call `read_graph_dsl` on `EventGraph` again. Confirm:
- `EventHit`'s outer `if` condition now checks both `not IsPushed` and `not IsFalling`.
- `EventTick` now starts with `CallFunction|IsGrounded` and branches into a grounded path
  (containing the original step-up/move/step-down push logic, now calling
  `CallFunction|StopPushing` when the player releases the push direction) and an ungrounded path
  (calling `CallFunction|StopPushing` if a push was active, then accumulating `FallSpeed` via
  `CallFunction|GetEffectiveGravityZ` and applying it as a swept vertical offset).

---

### Task 6: Compile and save

**Files:**
- Modify (via MCP): `Content/Blueprints/Actor/Common/BP_PushBlock.uasset`

- [ ] **Step 1: Compile**

Call `compile_blueprint`:
```json
{
  "tool_name": "compile_blueprint",
  "toolset_name": "editor_toolset.toolsets.blueprint.BlueprintTools",
  "arguments": {
    "blueprint": {"refPath": "/Game/Blueprints/Actor/Common/BP_PushBlock.BP_PushBlock"},
    "warnings_as_errors": true
  }
}
```
If this raises any error or warning, stop and fix it before continuing — do not proceed to save
a Blueprint that doesn't compile cleanly.

- [ ] **Step 2: Save the asset to disk**

Call `save_assets` (toolset `editor_toolset.toolsets.asset.AssetTools`):
```json
{
  "tool_name": "save_assets",
  "toolset_name": "editor_toolset.toolsets.asset.AssetTools",
  "arguments": {
    "asset_paths": ["/Game/Blueprints/Actor/Common/BP_PushBlock"]
  }
}
```
Confirm it returns `true`.

- [ ] **Step 3: Confirm the .uasset changed on disk**

Run: `git status --porcelain Content/Blueprints/Actor/Common/BP_PushBlock.uasset`
Expected: the file shows as modified.

- [ ] **Step 4: Commit**

```bash
git add Content/Blueprints/Actor/Common/BP_PushBlock.uasset
git commit -m "feat: BP_PushBlock falls off ledges and ends the player's push state

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 7: Manual PIE verification

No automated test can reliably drive this gameplay interaction in PIE (Slate input simulation
can't reliably trigger movement/collision-driven gameplay actions — see project memory on PIE
input simulation limits). This task is a manual playtest checklist to run in the editor.

- [ ] **Step 1: Play in Editor** in a level containing a `BP_PushBlock` instance next to a ledge
  (the test level added in a previous session, or any level with one placed near a drop).

- [ ] **Step 2: Push the block off the ledge.** Confirm it falls (not floats) and lands on the
  floor below, coming to rest instead of clipping through it.

- [ ] **Step 3: Confirm the player's push state ends immediately** when the block goes over the
  edge — push animation stops, walk speed returns to normal, camera/orientation control returns
  to the player — without needing to release the input direction first.

- [ ] **Step 4: Try to push the falling block sideways while it's still in the air.** Confirm it
  does not start a new push (no `DoPush` reaction) until after it lands.

- [ ] **Step 5: After it lands, push it again on flat ground.** Confirm ordinary pushing still
  works exactly as before (moves smoothly, still steps over small floor bumps).

- [ ] **Step 6: Report the outcome** (pass/fail per step above) back in the conversation. Any
  failure here means returning to Task 5 to adjust the `EventGraph` logic, recompiling, and
  re-testing — not editing the design document.
