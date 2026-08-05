# BP_PushBlock: Fall when pushed off a ledge

## Problem

`BP_PushBlock` (`Content/Blueprints/Actor/Common/BP_PushBlock.uasset`) can currently be pushed
past the edge of a floor and will hang in mid-air instead of falling. Nothing in its Tick logic
checks whether there is still ground under the actor's pivot.

## Scope

Blueprint-only change. No C++/native code is added or modified — everything below is implemented
via the existing Blueprint graphs on `BP_PushBlock` (functions, variables, `EventGraph`), edited
through the Unreal Editor's Blueprint graph.

## Current behavior (verified by reading the existing graphs)

- `EventHit`: casts the colliding actor to the player, validates the hit position/direction via
  `IsPushPositionValid`, then calls `Ac_Push::DoPush` on the player. `DoPush` sets the player's
  `Ac_Push::IsPushing = true`, slows their walk speed, locks orientation to the push direction,
  and repositions the player against the block.
- `EventTick` (only while `IsPushed`): if the player is still holding the push direction
  (`IsKeepPushDirection`), moves the block by stepping up `FloorBumpTolerance` (default 3 units),
  moving horizontally by `PushSpeed * DeltaSeconds` along `PushDirection`, then stepping back down
  by `FloorBumpTolerance` — a "step over small floor bumps" trick, not real floor detection. If the
  player stops holding the direction, it calls `Ac_Push::EndPush` (this is what ends the player's
  pushing state) and clears `IsPushed`.

## Design

### New member variables on `BP_PushBlock`
- `FallSpeed` (float, default `0.0`) — accumulated downward speed while airborne.
- `IsFalling` (bool, default `false`) — true while the block has no floor under its pivot.

No new variable is added for the ground-check distance — it reuses the existing
`FloorBumpTolerance`, since that already represents "how much vertical slack still counts as
grounded" for this actor.

### New functions on `BP_PushBlock`

**`IsGrounded()` → bool**
Line-traces straight down from the actor's pivot (`GetActorLocation`) by `FloorBumpTolerance`,
on the default `Visibility` trace channel, ignoring self. Returns whether the trace hit
something.

**`GetEffectiveGravityZ()` → float**
Returns the constant `-980.0` (Unreal's standard default gravity). The original design read
`WorldSettings.GlobalGravityZ` dynamically, but that node requires an actual `UWorld` reference
as its target and this project's Blueprint node set has no reflected way to obtain one from an
Actor — confirmed by testing that `connect_pins` genuinely rejects wiring an Actor Self-reference
into that pin, not merely a DSL syntax issue. Since this project does not override gravity
anywhere in `Config/`, the constant is the value actually in effect; the function stays a named,
single-purpose wrapper so a future per-level override could be added here later without touching
`EventTick`.

**`StopPushing()`**
Factors out the existing "end the push" sequence so it isn't duplicated:
`SetIsPushed(false)` → `Ac_Push::EndPush` on the pushing player's push component →
`SetPushingPlayer(none)`.

### `EventTick` (restructured)

```
grounded = IsGrounded()

if grounded:
    FallSpeed = 0
    IsFalling = false
    if IsPushed:
        <existing step-up / move-horizontal / step-down push logic, unchanged>
        <on IsKeepPushDirection == false: call StopPushing()>
else:
    if IsPushed:
        StopPushing()
    IsFalling = true
    FallSpeed += GetEffectiveGravityZ() * DeltaSeconds
    AddActorWorldOffset( (0, 0, FallSpeed * DeltaSeconds), sweep = true )
```

The swept vertical offset means the block naturally stops the instant it lands on a floor below —
no separate landing/snap logic is needed. Once grounded again, `FallSpeed` resets to 0 and
`IsFalling` clears on the very next tick.

### `EventHit` (one added guard)

A new push only starts if the block is neither already pushed **nor currently falling**:

```
if not IsPushed and not IsFalling:
    <existing push-start logic, unchanged>
```

This stops a player from shoving a block sideways while it's mid-drop. Once it lands, `IsFalling`
clears and it becomes pushable again as normal.

## Requirement mapping

- "can still be pushed off a ledge, but must fall" → handled by the ungrounded branch of
  `EventTick`, using swept gravity-driven movement.
- "player's pushing state must end" → `StopPushing()` is called the same tick the block becomes
  ungrounded while a push was active, which calls `Ac_Push::EndPush` — the same call already used
  to end pushing when the player releases the direction.
- "pivot not on the ground / floating" → `IsGrounded()` traces from the actor's pivot
  (`GetActorLocation`), matching the pivot-based phrasing of the requirement exactly.

## Testing

No automated test harness reliably drives this kind of gameplay movement in PIE. Verification is
a manual PIE playtest:
1. Push a block off a ledge → it falls and lands on the floor below instead of floating.
2. The player's push animation/state ends the instant the block goes over the edge.
3. The block becomes pushable again once it lands.
4. Normal pushing on flat ground is unchanged (including the existing floor-bump-tolerance
   stepping behavior).
