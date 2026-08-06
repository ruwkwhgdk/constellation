# WBP_GetItem: item acquisition popup for BP_Chest

## Problem

Interacting with an unopened `BP_Chest` currently has no visible "you got an item" moment — its
`Interact` event just flips `IsOpened`, calls a placeholder `Item::AddDummyItemTo`, marks the
chest opened, and plays the lid-open animation. There is no UI showing what was acquired.

## Scope

Blueprint-only change across three existing/new assets:
- `Content/Blueprints/Widget/WBP_GetItem.uasset` (new)
- `Content/Blueprints/System/BP_HUD.uasset` (add one custom event)
- `Content/Blueprints/Actor/Common/BP_Chest.uasset` (add one variable, extend `Interact`)

No C++/native code is added or modified.

## Current behavior (verified by reading the existing graphs)

- `BP_Chest` (parent `BP_Interactable_Base`) has one own variable, `IsOpened`, and its
  `EventInteract` is:
  ```
  if not IsOpened:
      SetIsOpened(true)
      Item::AddDummyItemTo(1)
      Chest::MarkChestOpened(0)
      PlayOpenAnimation()
  ```
  There is no per-chest "which item" data yet.
- This project already routes every other popup through a central manager, `BP_HUD`
  (implements `BPI_UIManager`):
  - `EventRequestShowChoiceUI(ChoiceData)` — the closest existing precedent for a one-off,
    non-cutscene-native popup: if `Ref_ActiveUI` is valid, removes it; creates the widget; stores
    it in `Ref_ActiveUI`; adds to viewport at `UI Order` (100); calls
    `Input::SetInputModeUIOnly` and shows the mouse cursor.
  - `EventReportUIFinished(IsRemoveUIFinished)` — removes `Ref_ActiveUI` from its parent and
    fires the `OnUIFinished` dispatcher, when `IsRemoveUIFinished` is true. It does **not**
    restore input mode; for `WBP_Choice`/`WBP_Dialogue` that's fine because those are only shown
    from inside a Level Sequence, which manages input mode itself around playback.
  - Every closable popup widget's own "close" button calls the `BPI_UIManager` interface function
    `ReportUIFinished(HUD, true)` on `HUD::GetHUD(GetPlayerController(0))` — e.g.
    `WBP_Dialogue`'s `NextButton` and each of `WBP_Choice`'s three choice buttons.
  - `Ref_ActiveUI` is typed as the generic `UserWidget`, so it can hold any popup widget, not just
    `WBP_Choice`/`WBP_Dialogue`.

## Design

### `WBP_GetItem` (new widget blueprint)

Widget tree:
- `CanvasPanel` (root)
  - `Background` (`Border`): anchored to screen center with both min/max anchors at
    `(0.25, 0.25)`–`(0.75, 0.75)` and zero offsets, so it always renders at exactly 50% of the
    viewport's width and height, centered, at any resolution. Flat semi-transparent dark fill
    (no existing texture asset in `Resources/UI` fits a generic item-popup panel, so this follows
    the same flat-color approach `WBP_Dialogue`'s `NextButton` already uses).
    - `ItemImage` (`Image`), centered inside `Background`. Its `Brush` is driven by a bound
      function (`GetItemImageBrush`) that runs "Make Brush from Texture" on a new widget variable
      `ItemImage` (`Texture2D`, **Instance Editable + Expose on Spawn**, default `None`). Left
      unset by default, so it renders empty until a caller supplies a texture — satisfies "leave
      it empty for now."
    - `ConfirmButton` (`Button`), below `ItemImage`, with a child `TextBlock` reading "Confirm".

`ConfirmButton`'s `OnClicked`:
```
BPIUIManager::ReportUIFinished(HUD::GetHUD(GetPlayerController(0)), true)
Input::SetInputModeGameOnly(GetPlayerController(0))
GetPlayerController(0)::SetShowMouseCursor(false)
```
The first line reuses the exact same close contract every other popup in this project already
uses. The last two lines are needed here specifically because — unlike `WBP_Choice`/
`WBP_Dialogue` — this popup is shown from a plain gameplay interaction, not from inside a Level
Sequence, so nothing else will restore input mode afterward.

### `BP_HUD` (extend the existing UI manager)

New custom event, `EventRequestShowGetItemUI(ItemImage: Texture2D)`, mirroring
`EventRequestShowChoiceUI`:
```
if IsValid(Ref_ActiveUI):
    RemoveFromParent(Ref_ActiveUI)
NewWidget = CreateWidget(WBP_GetItem, GetPlayerController(0), ItemImage)   # Expose-on-Spawn pin
Ref_ActiveUI = NewWidget
AddToViewport(Ref_ActiveUI, UI Order)
Input::SetInputModeUIOnly(GetPlayerController(0))
GetPlayerController(0)::SetShowMouseCursor(true)
```
`EventReportUIFinished` is unchanged — it already removes whatever is in `Ref_ActiveUI`, which
covers `WBP_GetItem` too since that variable is generically typed.

### `BP_Chest`

- New variable `Item` (`Texture2D`, Instance Editable), default `None` — the icon for whatever
  this chest contains. Left unassigned for now; will be set per-chest-instance once real item
  data exists.
- `EventInteract`, appended to the end of the existing "not yet opened" branch (existing calls
  unchanged):
  ```
  ...
  PlayOpenAnimation()
  BP_HUD::EventRequestShowGetItemUI(GetHUD() as BP_HUD, Item)
  ```

## As shipped (differs from the design above)

Implementation surfaced a few tooling constraints that changed the mechanism without changing the
requirement each piece satisfies:

- **`WBP_GetItem` widget tree:** `Background` and a new `ContentBox` (`VerticalBox`, holding
  `ItemImage` and `ConfirmButton`) are siblings under `RootCanvas`, both anchored to the same
  50%/50% centered region, rather than `ItemImage`/`ConfirmButton` nesting inside `Background`
  (a `Border` only supports one child). `ContentBox` visually sits on top of `Background`,
  matching the sibling-panel pattern `WBP_Dialogue` already uses for its own background+content.
- **Image binding:** no expose-on-spawn/bound-function pair. `WBP_GetItem` instead exposes a
  plain public function `SetItemTexture(NewTexture: Texture2D)` — sets the `ItemTexture` member
  variable and pushes the texture into `ItemImage` via `Appearance::SetBrushFromTexture` (the
  same one-node pattern `WBP_Tutorial` already uses elsewhere in this project). `BP_HUD` calls it
  explicitly after `CreateWidget`, rather than the widget pulling the value itself.
- **`BP_HUD`'s new entry point is a function, not a custom event:** `RequestShowGetItemUI
  (ItemTexture: Texture2D)`, calling a small helper `ShowGetItemWidget(ItemTexture)` that does the
  actual create/track/show sequence. `RequestShowGetItemUI` calls the helper from *both* the
  `Ref_ActiveUI`-valid and -invalid branches (unlike `EventRequestShowChoiceUI`, which only acts
  in the valid branch and is a no-op otherwise) — necessary because a chest interaction, unlike a
  dialogue-chained choice, is typically the *first* popup shown, so `Ref_ActiveUI` starts `None`.
- **`BP_Chest`'s call site:** `Class|BPHUD|RequestShowGetItemUI(hudTyped, Item)` — same cast-then-call
  shape as designed, just written directly onto the existing `EventInteract` graph via surgical
  node/pin edits rather than a full-graph DSL rewrite, since the chest's Timeline node
  (`Custom|PlayOpenAnimation`) can't be reconstructed from the available tooling.

## Requirement mapping

- "UI displayed in the center of the screen" → `Background`'s anchors are centered with equal
  min/max margins on both axes.
- "background area taking up 50% of the screen's width and height" → `Background` anchor min
  `(0.25, 0.25)`, max `(0.75, 0.75)`, zero offsets.
- "item image ... fetched from the item variable of BP_Chest; leave it empty for now" → `BP_Chest`
  gets a new `Item` (Texture2D) variable, passed through `BP_HUD` into `WBP_GetItem`'s
  Expose-on-Spawn `ItemImage`, left as `None`.
- "Confirm button below the image, closes the UI when clicked" → `ConfirmButton` below
  `ItemImage`; `OnClicked` reports UI finished (removes the widget) and restores gameplay input.
- "appears when interacting with an unopened BP_Chest" → `EventInteract`'s not-yet-opened branch
  calls `BP_HUD::EventRequestShowGetItemUI`.

## Testing

No automated test harness reliably drives this kind of UI + gameplay interaction in PIE (see
`pie_input_simulation_limits` project note). Verification is a manual PIE playtest:
1. Walk up to an unopened `BP_Chest` and interact → `WBP_GetItem` appears centered, at ~50% of
   the screen's width/height, with an empty image area and a visible "Confirm" button.
2. Mouse cursor appears and gameplay input stops responding while the popup is shown.
3. Clicking Confirm closes the popup, the cursor disappears, and gameplay input (movement) works
   again immediately.
4. The chest's existing behavior (opens once, plays its lid animation, `IsOpened` stays true,
   re-interacting does nothing) is unchanged.
5. Setting a chest instance's `Item` to a texture and re-triggering shows that texture in the
   popup, confirming the binding actually reads the variable (even though it ships empty by
   default).
