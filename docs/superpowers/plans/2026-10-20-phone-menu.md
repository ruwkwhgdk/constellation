# Phone menu implementation plan

> **For agentic workers:** Use superpowers:executing-plans. Track steps below.

**Goal:** Approved Esc phone draw, close camera, placeholder menu and safe return; deliver animation video before engine import.

**Architecture:** A dedicated character component owns finite state, prop, camera and input capture. A native UMG/Slate widget owns placeholder UI. Animation events are generation checked, with watchdog recovery; absent approved animation assets fail closed.

**Tech Stack:** UE 5.8 C++, Enhanced Input, UMG/Slate, Blender 5.2.1 via guarded launcher.

**Spec:** ../specs/2026-10-20-phone-menu-design.md (approved 2026-10-20).

## Global constraints

- 2026-10-21 user correction: use existing FREE commercially usable animation sources, following the previous Mixamo workflow. Stop hand-authored draw/stow experiments. Candidate01–10 are retired, not approval candidates. See ArtSource/Heroine_Tripo_Review/PhoneMenu01/CURRENT.md.

- Preserve shared checkout and all Intermediate directories. No competing build, Clean or Rebuild.
- User selected CarryPickupD01/Attempt06/Heroine_Pickup_Chair.blend; preserve source.
- New animation must be shown as video and approved before Unreal import.
- Inspect actual rig and Blueprint names. Preserve mesh, UV, weights, shapes, materials and skeleton.
- In this working session implement inline in the shared checkout, with feature files isolated by name. Do not commit other chats' changes.

## Review focus

- Early/held Esc: one pending close, no reopen or duplicate widget.
- Missed animation events: bounded timeout returns control.
- External pause/camera/input ownership: never release another system's state.
- Destruction/possession change: cleanup without resurrecting old camera.
- Hand grip and transition deformation: actual saved-model video, close/front/side, no numeric-only approval.

## Task 1: Read-only integration and character audit

- [x] Save current heroine/controller graph, component defaults and inputs in Saved/PhoneMenu.
- [x] Inspect specified blend; run audit and snapshot with observed rig/mesh names.
- [x] Resolve pocket location from actual clothing and provide review if no usable pocket exists.

## Task 2: Lifecycle and runtime component

Files: Source/Constellation/PhoneMenuState.h, PhoneMenuComponent.h/.cpp, Tests/PhoneMenuStateTests.cpp, tools/test-phone-menu.cmd.

Interfaces: State::RequestOpen, RequestClose, Ready, Drawn, CameraReady, Stowed, Tick, Abort; token protects stale events. UPhoneMenuComponent::ToggleMenu, NotifyPhoneEvent, CancelMenu, BlocksGameplay.

- [x] Write native tests for order, early close, held input, missing signal, stale generation, repeated cycles.
- [x] Run test and observe missing implementation failure.
- [x] Implement state and run native suite.
- [x] Add component that requires configured approved montage and socket; construct cube without collision; derive camera from actor; sweep for obstacles.
- [x] Capture gameplay keys with owned input preprocessor during transition; consume UI input without leaking gameplay. Keep default engine input mode intact for exact restoration.
- [x] Pair only own movement/look locks and pause; restore only camera still owned; restore HUD visibility and focus.

## Task 3: Placeholder UI

Files: Source/Constellation/PhoneMenuWidget.h/.cpp.

Interfaces: SetCloseHandler, FocusFirst; six selectable buttons and status.

- [x] Implement right-side 45% responsive panel, six buttons in 2x3, keyboard focus and close.
- [x] Add engine automation for component fail-closed and destruction/cleanup; validate runtime and widget compile with incremental build when available.
- [x] Do not activate incomplete animation on gameplay Blueprint; stage setup instructions for post-approval.

## Task 4: Animation candidate and visual review

Files: ArtSource/Heroine_Tripo_Review/PhoneMenu01 (new work only), Checks/PhoneMenu_20261020.

- [ ] Create separate draw/hold/stow candidate from approved source. Preserve original actions and base character data.
- [ ] Match arm chain, thumb opposition, finger wrap to cube; retain body proportions.
- [x] Save and reopen, audit/snapshot/compare. Latest: OneHandReview04, equal_captured_fields.
- [x] Render saved candidate to front, side and hand close footage; deliver normal-speed MP4 and a viewer with half-speed/frame controls.
- [ ] Complete user visual review, proposed menu camera footage and final loop/blend boundary review.
- [ ] Correct large bends/intersections before presenting as an approval candidate.
- [x] Deliver video and await animation approval. User approved Cube08 on 2026-10-21, accepting the remaining minor hand/phone alignment issue.

## Task 5: After animation approval

- [x] Import only approved animations, configure events and component on current heroine. Draw/Hold/Stow and the 285-frame prop track saved; events follow the actual montage cursor.
- [ ] Verify saved/reloaded assets and Standalone Esc/UI/return, 10 cycles, rejection states, interruption, aspect ratios and nearby walls.
- [ ] Report data/visual/engine checks separately. Video approval received; engine validation remains pending.

## Execution record

- User approved spec and selected maintained source. No additional plan approval needed.
- Existing live Blender and Unreal sessions remain untouched.
- 2026-10-21: User retained one-hand portrait grip and free existing motion requirement. Downloaded five official Mixamo sources. Edited Talking On A Cell Phone draw/stow and Texting hold, with two 12-frame source crossfades; no newly authored draw/stow poses or reversed stow.
- Latest review: `ArtSource/Heroine_Tripo_Review/PhoneMenu01/OneHandReview04/Heroine_Mixamo_OneHand_Cube08.blend`, 285 frames at 30fps. Delivery video has front/side/hand close views. Character-proportion retargeting and measured 5.5cm garment clearance adjustment preserve source wrist orientation and finger poses.
- Saved/reopened mesh data compare is equal; current key continuity has no sign flips. Specified hand/holding-body vertex tests found no penetration above 0.5mm. These are scoped data checks, not full contact or visual approval. Original draw/stow uses the rear hip, not the cardigan front pocket.
- Awaiting user video review. No phone animation imported or activated in Unreal; menu camera/UI/runtime checks remain pending.
- 2026-10-21 later: user approved proceeding with Cube08 while acknowledging minor phone/hand alignment error. Prior approval-wait record above is superseded.
- UnrealApply01: three sequences/montages saved and separately reloaded. 26,978 bone transforms checked; max error 0.000935cm / 0.001054 degrees. PhoneMenu added to current BP_Player_Heroine through the live editor after a separate-process save encountered its file lock. Original NPC unsaved work preserved.
- Runtime checks exposed a stopped-but-active final montage preventing the second opening. Cleanup now checks Montage_IsActive. Capture stalls exposed a wall-time watchdog false cancellation; animation watchdog now refreshes only on actual montage progress. Build suffix2026 succeeded; final repeated runtime check is in progress.
- User cannot close the original editor now. Keep it running. Base DLL deployment/full original-project restart verification is deferred; do not repeat the close request.
- Final suffix2027 build succeeded. Independent code review findings (Tab navigation and controller rebinding) were fixed and reviewed again. Pure state assertions passed again. Isolated PIE `Runtime_20261021_020141` passed 10 cycles, actual Enhanced Input action opening, Slate Esc closing, pause/camera/input/cursor restoration and Enter/Tab button selection. This is not a packaged-game or physical Esc key-down opening test.
- Camera saved to the actual player Blueprint at local (30,-25,35), rotation (-52,130,0), FOV65. The close camera exposes the accepted existing hand/phone misalignment. A new matching-angle render from the approved saved Blender file reproduces it; no new grip animation was authored. Full visual acceptance, wall/aspect/interruption runtime coverage and original-editor restart remain outstanding.


- 2026-10-21 base deployment completed after user closed the editor. Added requested backtick menu mapping; console moved to F10. Normal incremental build and original-project automation passed. Restarted editor loaded the unsuffixed DLL and passed 10 Slate-backtick open/close cycles plus fresh-snapshot Enter/Tab UI checks. Evidence: BaseRuntime_20261021_042205/result.json and Saved/PhoneMenu/BaseDeployment01. Previous NPC review map restored; editor remains open. Original restart deferral is resolved.
