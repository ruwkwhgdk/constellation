# WBP_GetItem Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a centered `WBP_GetItem` popup that shows a chest's item icon, wire it into
`BP_Chest`'s Interact event through the project's existing `BP_HUD` UI-manager pattern, and let a
Confirm button close it and hand input back to gameplay.

**Architecture:** All work happens through the `mcp__unreal-mcp` toolset against the live Unreal
Editor — there are no source text files to edit. Widget structure/properties go through
`UMGToolSet` + `ObjectTools`; Blueprint graphs go through `BlueprintTools`, mostly via its
S-expression DSL (`read_graph_dsl` / `write_graph_dsl` — call `get_graph_dsl_docs()` if you need
the syntax reference again). `BP_HUD` already implements a "central UI manager" pattern used by
`WBP_Choice`/`WBP_Dialogue`/`WBP_Tutorial`; this plan extends it with one new function instead of
inventing a parallel mechanism.

**Tech Stack:** Unreal Engine Blueprints (UMG + Blueprint graphs), authored via the
`mcp__unreal-mcp` MCP toolset (`editor_toolset.toolsets.blueprint.BlueprintTools`,
`editor_toolset.toolsets.object.ObjectTools`, `UMGToolSet.UMGToolSet`).

## Global Constraints

- Blueprint-only. No C++ changes.
- `WBP_GetItem` lives at `Content/Blueprints/Widget/WBP_GetItem.uasset` (parent class
  `/Script/UMG.UserWidget`).
- `Background` covers exactly 50% of the viewport's width and height, centered, at any
  resolution — i.e. `CanvasPanelSlot.layoutData.anchors` = min `(0.25, 0.25)`, max
  `(0.75, 0.75)`, with `offsets` all `0`.
- Every popup in this project closes by calling the `BPI_UIManager` interface function
  `ReportUIFinished` on the HUD (see `WBP_Choice`/`WBP_Dialogue`'s `OnClicked` handlers) — do not
  invent a different close mechanism.
- `Ref_ActiveUI` on `BP_HUD` is generically typed `UserWidget`; reuse it for `WBP_GetItem` rather
  than adding a new `Ref_*` variable, matching how `EventRequestShowChoiceUI` reuses it.
- Before calling `set_properties` on any newly-returned widget/slot, call
  `ObjectTools.list_properties` on it first if the exact property name isn't already given
  verbatim in a task below — property names cannot be guessed (this is the UMG toolset's own
  documented workflow).
- Before writing any DSL node whose exact type ID or pin order isn't already given verbatim in a
  task below, call `find_node_types` (with a `type_id_filter` substring, not natural language) and
  `get_node_type_pins` first. Do not guess pin order — it varies per node and guessing wrong
  silently miswires the graph.
- After any `write_graph_dsl` call, call `read_graph_dsl` on the same graph immediately after to
  confirm it matches what was intended, then `compile_blueprint` and check for errors before
  moving on.

---

## Task 1: Build the WBP_GetItem widget

**Files:**
- Create: `Content/Blueprints/Widget/WBP_GetItem.uasset`

**Interfaces:**
- Produces: a `SetItemTexture(NewTexture: Texture2D)` public function on `WBP_GetItem` — Task 2
  calls this to push the chest's icon into the popup after creating it.
- Produces: the widget's own Confirm-and-close behavior (self-contained; no other task depends on
  its internals beyond the function above).

- [ ] **Step 1: Create the widget blueprint**

```
UMGToolSet.CreateWidgetBlueprint(
  folderPath: "/Game/Blueprints/Widget",
  assetName: "WBP_GetItem",
  parentClass: { refPath: "/Script/UMG.UserWidget" }
)
```
Keep the returned `widgetBlueprint` ref — every following step in this task needs it.

- [ ] **Step 2: Build the widget tree**

Use `UMGToolSet.AddWidget(widgetBlueprint, widgetClass, widgetDisplayName, parentWidget)` for
each, in this order (a child's `parentWidget` is the ref returned by its parent's `AddWidget`
call):

| Widget class | Display name | Parent |
|---|---|---|
| `/Script/UMG.CanvasPanel` | `RootCanvas` | *(none — becomes root)* |
| `/Script/UMG.Border` | `Background` | `RootCanvas` |
| `/Script/UMG.VerticalBox` | `ContentBox` | `RootCanvas` |
| `/Script/UMG.Image` | `ItemImage` | `ContentBox` |
| `/Script/UMG.Button` | `ConfirmButton` | `ContentBox` |
| `/Script/UMG.TextBlock` | `ConfirmText` | `ConfirmButton` |

`Background` and `ContentBox` are siblings under `RootCanvas`, not nested — `ContentBox` is
positioned to sit on top of `Background`'s area (this is the same pattern `WBP_Dialogue` already
uses for its own `Background` Image + `VerticalBox`).

- [ ] **Step 3: Center Background at 50% width/height**

`AddWidget` returns each widget's `slot` (a `CanvasPanelSlot` for both `Background` and
`ContentBox`, since their parent is the `CanvasPanel`). Call:
```
ObjectTools.set_properties(BackgroundSlot, {
  "layoutData": {
    "offsets": { "left": 0, "top": 0, "right": 0, "bottom": 0 },
    "anchors": { "minimum": {"x": 0.25, "y": 0.25}, "maximum": {"x": 0.75, "y": 0.75} },
    "alignment": {"x": 0, "y": 0}
  }
})
```
Apply the **exact same call** to `ContentBox`'s slot so it overlaps `Background` exactly.

- [ ] **Step 4: Give Background a flat semi-transparent panel color**

There's no existing "popup panel" texture in `Content/Resources/UI` to reuse, so tint the
`Border`'s default box brush instead (same flat-color approach `WBP_Dialogue`'s `NextButton`
already uses via `BackgroundColor`):
```
ObjectTools.set_properties(Background, {
  "brushColor": { "r": 0, "g": 0, "b": 0, "a": 0.75 }
})
```

- [ ] **Step 5: Lay out ItemImage and ConfirmButton inside ContentBox**

`AddWidget` returned each of their `slot`s (both `VerticalBoxSlot`, since their parent is
`ContentBox`). Call `ObjectTools.list_properties` on `ItemImage`'s slot to get the exact field
names (expect something shaped like `WBP_Choice`'s `HorizontalBoxSlot` output —
`horizontalAlignment` / `verticalAlignment` / `size.sizeRule` / `padding`), then set both slots to
center their content horizontally with reasonable spacing, e.g.:
```
ObjectTools.set_properties(ItemImageSlot, {
  "horizontalAlignment": "HAlign_Center",
  "padding": {"left": 0, "top": 40, "right": 0, "bottom": 24}
})
ObjectTools.set_properties(ConfirmButtonSlot, {
  "horizontalAlignment": "HAlign_Center",
  "padding": {"left": 0, "top": 0, "right": 0, "bottom": 40}
})
```
Confirm the actual field names via `list_properties` first — don't assume the names above are
exactly right.

- [ ] **Step 6: Set the Confirm button's label**

```
ObjectTools.set_properties(ConfirmText, { "text": "Confirm" })
```

- [ ] **Step 7: Compile and verify the tree**

```
UMGToolSet.CompileWidgetBlueprint(widgetBlueprint)
UMGToolSet.GetWidgetDescription(widgetBlueprint)
```
Expected: no compile errors; the description shows `RootCanvas > Background` (Border, 50%/50%
centered anchors) and `RootCanvas > ContentBox > (ItemImage, ConfirmButton > ConfirmText)`.

- [ ] **Step 8: Add the ItemTexture variable**

```
BlueprintTools.add_object_variable(
  blueprint: widgetBlueprint_as_Blueprint_ref,
  name: "ItemTexture",
  object_class: { refPath: "/Script/Engine.Texture2D" }
)
BlueprintTools.set_variable_instance_editable(widgetBlueprint, "ItemTexture", true)
```
Default value is left unset (`None`) — this is the "leave it empty for now" requirement.

Note: `WidgetBlueprint` refs and the underlying `Blueprint` refs used by `BlueprintTools` point at
the same asset; if a call rejects the `WidgetBlueprint`-flavored ref, re-fetch it via
`BlueprintTools`' own blueprint-lookup path (e.g. by asset path string) rather than guessing.

- [ ] **Step 9: Make ItemImage and ConfirmButton graph-accessible**

```
UMGToolSet.ToggleWidgetAsVariable(widgetBlueprint, ItemImage, bIsVariable: true)
UMGToolSet.ToggleWidgetAsVariable(widgetBlueprint, ConfirmButton, bIsVariable: true)
```
(Matches how `WBP_Choice`'s buttons and text blocks are all `bIsVariable: true` so they can be
referenced from `EventGraph`.)

- [ ] **Step 10: Add and implement `SetItemTexture(NewTexture: Texture2D)`**

```
graph = BlueprintTools.add_function_graph(blueprint, "SetItemTexture")
BlueprintTools.add_object_function_param(
  graph, param_name: "NewTexture",
  object_class: { refPath: "/Script/Engine.Texture2D" }, input_param: true
)
```
Before writing the body, discover the Image brush-setter node:
```
BlueprintTools.find_node_types(graph, type_id_filter: "SetBrush", context_pins: [])
BlueprintTools.get_node_type_pins(graph, type_id: <the match found above>)
```
Then write the body (adjust the setter node's type ID / pin names to whatever the discovery step
above actually returned — the shape below is the intended logic, not a literal final call):
```lisp
(fn SetItemTexture (NewTexture)
  (Variables|Default|SetItemTexture NewTexture)
  (bind brush (Widget|Brush|MakeBrushFromTexture :Texture NewTexture :Width 0 :Height 0))
  (<discovered-SetBrush-node> brush (Variables|WBP_GetItem|GetItemImage)))
```
Write it with `BlueprintTools.write_graph_dsl(graph, <script above>)`, then
`BlueprintTools.read_graph_dsl(graph)` to confirm it matches, then
`BlueprintTools.compile_blueprint(widgetBlueprint_as_Blueprint_ref)`.

- [ ] **Step 11: Bind and implement ConfirmButton's OnClicked**

```
UMGToolSet.BindToEventProperty(
  widgetBlueprint,
  eventName: "OnClicked",
  propertyName: "ConfirmButton",
  propertyClass: { refPath: "/Script/UMG.Button" }
)
```
This creates an `OnClicked(ConfirmButton)` event node in the widget's `EventGraph`. Read the
current `EventGraph` DSL first (`read_graph_dsl` — it will just show the empty event header),
then write the full graph back with the body filled in:
```lisp
(event OnClicked(ConfirmButton)
  (bind pc (Game|GetPlayerController 0))
  (bind hudBase (HUD|GetHUD :self pc))
  (|ReportUIFinished :self hudBase :IsRemoveUIFinished true)
  (Input|SetInputMode_GameOnly :PlayerController pc :bFlushInput false)
  (|SetbShowMouseCursor :bShowMouseCursor false :self pc))
```
`(Game|GetPlayerController 0)`, `(HUD|GetHUD :self pc)`, `(|ReportUIFinished ...)`,
`(Input|SetInputMode_GameOnly ...)` and `(|SetbShowMouseCursor ...)` are all confirmed node
types/pin shapes (copied from `BP_HUD` and `WBP_Choice`'s own real graphs plus a direct
`get_node_type_pins` check) — use them verbatim.

- [ ] **Step 12: Compile, save, and verify**

```
BlueprintTools.compile_blueprint(widgetBlueprint_as_Blueprint_ref)
AssetTools.save_asset(widgetBlueprint)
BlueprintTools.read_graph_dsl(EventGraph)   # confirm OnClicked(ConfirmButton) body matches
```
Expected: compiles with no errors; `read_graph_dsl` shows both `SetItemTexture` (as a `fn`) and
`OnClicked(ConfirmButton)` with the bodies above.

---

## Task 2: Wire BP_HUD to show WBP_GetItem

**Files:**
- Modify: `Content/Blueprints/System/BP_HUD.uasset`

**Interfaces:**
- Consumes: `WBP_GetItem`'s `SetItemTexture(NewTexture: Texture2D)` from Task 1, and the existing
  `Ref_ActiveUI` (UserWidget), `UI Order` (int) member variables already on `BP_HUD`.
- Produces: `RequestShowGetItemUI(ItemTexture: Texture2D)` — a public function on `BP_HUD` that
  Task 3 calls from `BP_Chest`.

- [ ] **Step 1: Add the function and its parameter**

```
graph = BlueprintTools.add_function_graph(BP_HUD_blueprint, "RequestShowGetItemUI")
BlueprintTools.add_object_function_param(
  graph, param_name: "ItemTexture",
  object_class: { refPath: "/Script/Engine.Texture2D" }, input_param: true
)
```

- [ ] **Step 2: Write the function body**

Mirrors `EventRequestShowChoiceUI`'s shape exactly (remove any active UI, create the widget, push
data in, track it, show it, switch input mode):
```lisp
(fn RequestShowGetItemUI (ItemTexture)
  (bind activeUI (|GetRef_ActiveUI))
  (Utilities|IsValid activeUI
    (:"Is Valid"
      (Widget|RemoveFromParent activeUI))
    (:"Is Not Valid"))
  (bind pc (Game|GetPlayerController 0))
  (bind newWidget (UserInterface|CreateWidget "/Game/Blueprints/Widget/WBP_GetItem.WBP_GetItem_C" pc))
  (Class|WBP_GetItem|SetItemTexture ItemTexture newWidget)
  (|SetRef_ActiveUI newWidget)
  (UserInterface|Viewport|AddToViewport newWidget (Variables|Default|GetUIOrder))
  (Input|SetInputModeUIOnly :PlayerController pc)
  (|SetbShowMouseCursor :bShowMouseCursor true :self pc))
```
Before writing, confirm `Class|WBP_GetItem|SetItemTexture`'s exact pin order with
`find_node_types(graph, type_id_filter: "SetItemTexture", context_pins: [])` then
`get_node_type_pins` — Task 1 just created that function, so this is its first use anywhere;
don't assume the arg-then-target order shown above without checking (the codebase has both
target-first examples, like `ReportUIFinished`, and arg-then-target-last examples, like
`SetFadeAlpha` — it varies per node and must be confirmed, not guessed).

`Widget|RemoveFromParent`, `Utilities|IsValid`, `UserInterface|CreateWidget`,
`UserInterface|Viewport|AddToViewport`, `Input|SetInputModeUIOnly`, and `|SetbShowMouseCursor` are
all confirmed node types/pin shapes copied from `BP_HUD`'s own existing
`EventRequestShowChoiceUI` — use them verbatim.

- [ ] **Step 3: Compile, save, verify**

```
BlueprintTools.compile_blueprint(BP_HUD_blueprint)
AssetTools.save_asset(BP_HUD_blueprint)
BlueprintTools.read_graph_dsl(graph)   # confirm the fn body matches Step 2
```
Expected: compiles with no errors.

---

## Task 3: Wire BP_Chest to request the popup

**Files:**
- Modify: `Content/Blueprints/Actor/Common/BP_Chest.uasset`

**Interfaces:**
- Consumes: `BP_HUD`'s `RequestShowGetItemUI(ItemTexture: Texture2D)` from Task 2.

- [ ] **Step 1: Add the Item variable**

```
BlueprintTools.add_object_variable(
  blueprint: BP_Chest_blueprint,
  name: "Item",
  object_class: { refPath: "/Script/Engine.Texture2D" }
)
BlueprintTools.set_variable_instance_editable(BP_Chest_blueprint, "Item", true)
```
Default left unset (`None`) — every existing chest instance in every level keeps working
unchanged; nothing currently sets `Item`.

- [ ] **Step 2: Read the current EventGraph DSL**

```
BlueprintTools.read_graph_dsl({ refPath: "/Game/Blueprints/Actor/Common/BP_Chest.BP_Chest:EventGraph" })
```
This returns the full existing graph (`EventBeginPlay`, `EventInteract`, `Custom|PlayOpenAnimation`)
— keep it, you're about to write the whole graph back with one addition.

- [ ] **Step 3: Append the popup call to EventInteract's not-yet-opened branch**

Take the DSL read in Step 2 and change only the `EventInteract` event, from:
```lisp
(event EventInteract (Interactor HitComponent)
  (if (not (Variables|Default|GetIsOpened))
    (Variables|Default|SetIsOpened true)
    (Item|AddDummyItemTo 1)
    (Chest|MarkChestOpened 0)
    (CallFunction|PlayOpenAnimation)))
```
to:
```lisp
(event EventInteract (Interactor HitComponent)
  (if (not (Variables|Default|GetIsOpened))
    (Variables|Default|SetIsOpened true)
    (Item|AddDummyItemTo 1)
    (Chest|MarkChestOpened 0)
    (CallFunction|PlayOpenAnimation)
    (bind pc (Game|GetPlayerController 0))
    (bind hud (HUD|GetHUD :self pc))
    (bind hudTyped (Utilities|Casting|CastToBP_HUD :Object hud)
      (:then
        (Class|BP_HUD|RequestShowGetItemUI (Variables|Default|GetItem) hudTyped))
      (:CastFailed))))
```
Leave `EventBeginPlay` and `Custom|PlayOpenAnimation` exactly as read in Step 2 — write the whole
graph back with `write_graph_dsl`, not just the changed event, since `write_graph_dsl` populates
the graph it's given and the other events must stay present.

Before writing, confirm `Class|BP_HUD|RequestShowGetItemUI`'s exact pin order the same way as
Task 2 Step 2 (it's a brand new call site for a function that was itself brand new in Task 2).
`Utilities|Casting|CastToBP_HUD` and `HUD|GetHUD` are already confirmed (`AsBP HUD` is the cast's
typed output pin, `:self` is `HUD|GetHUD`'s input) — use them verbatim.

- [ ] **Step 4: Compile, save, verify**

```
BlueprintTools.compile_blueprint(BP_Chest_blueprint)
AssetTools.save_asset(BP_Chest_blueprint)
BlueprintTools.list_variables(BP_Chest_blueprint)   # expect: IsOpened, Item
BlueprintTools.read_graph_dsl(EventGraph)           # confirm EventInteract matches Step 3
```
Expected: compiles with no errors; `Item` appears alongside the existing `IsOpened`.

---

## Task 4: Manual PIE verification

No automated test harness reliably drives this kind of UI + gameplay interaction in PIE (see the
`pie_input_simulation_limits` project note). This task is a manual playtest, run through
`EditorAppToolset`'s PIE controls (or by hand in the editor) against a level containing at least
one unopened `BP_Chest`.

- [ ] **Step 1: Start PIE and interact with an unopened chest**

Expected: `WBP_GetItem` appears centered on screen, covering ~50% of the viewport's width and
height, with an empty image area (no texture assigned) and a visible "Confirm" button below it.

- [ ] **Step 2: Confirm input mode switched**

Expected: the mouse cursor is visible and character movement/interaction input stops responding
while the popup is on screen.

- [ ] **Step 3: Click Confirm**

Expected: the popup disappears, the mouse cursor is hidden again, and movement input responds
immediately.

- [ ] **Step 4: Confirm the chest's existing behavior is unchanged**

Expected: the chest stays opened (`IsOpened` true), its lid-open animation played once, and
interacting with it again does nothing (no second popup, no second dummy-item grant).

- [ ] **Step 5: Confirm the image binding actually reads the variable**

In the editor, set one placed chest instance's `Item` to any texture, re-run PIE, and interact
with that chest. Expected: `WBP_GetItem`'s image area now shows that texture, confirming
`SetItemTexture` → `MakeBrushFromTexture` → the Image widget's brush is wired correctly (even
though it ships empty by default on every chest that doesn't set one).

- [ ] **Step 6: Stop PIE**

If all five checks above pass, the feature is complete. If any fails, use
`EditorToolset.LogsToolset` to check the Output Log for Blueprint runtime errors (most likely a
node wired in Task 1–3 with the wrong pin) before changing anything.
