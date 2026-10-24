# Sword acquisition integration plan

**Goal:** Replace item-UI placeholders with the existing item widget, unlock combat after narration, restore controls, then show the existing attack toast. Approved animation clips connect later.
**Architecture:** A graph-driven SwordAcquisitionStage and action use the newly delivered shared ItemAcquisitionSubsystem, Ac_Ability unlock API, and TutorialPromptWidget. An owned scene UI request blocks graph playback until dismissal. SceneDirector owns camera/input restoration; stage preserves and disables pawn gameplay input until scene completion. No new inventory or save framework: existing combat ability state is authoritative, as in the old sword pickup.
**Tech stack:** Unreal 5.8 C++, SceneDirector assets, background Python installation and PIE checks.
**Spec:** ArtSource/SwordAcquisition/Storyboard/2026-10-21-v01/Storyboard_Direction_v01.txt; user 2026-10-21 explicitly authorizes functional integration while animations are pending.

Constraints: background execution only; no Intermediate cleanup or competing builds. Continue in the current shared checkout to retain installed engine assets and existing unfinished event work. Back up touched binary packages before saving; do not commit unrelated shared work.

- [x] Inspect existing sword/UI Blueprint schemas, texture, interaction and combat input gate.
- [x] Write and run a failing background installed-contract test (missing sword stage/graph).
- [x] Implement scoped stage/action with blocking real item UI, cancellation cleanup, narration-gated combat unlock, duplicate prevention, post-restoration attack toast using current input mapping.
- [x] Install a saved SceneDirector graph and sword-only route; remove the sword instance's star. Preserve other stars and existing map actors.
- [x] Build incrementally; background PIE test cancellation/retry, UI wait/dismiss, combat flag ordering, input restoration, toast timing and duplicate interaction. Capture actual UI/toast frames.
- [x] Review scoped changes and record verification/animation limitations.

Review focus: cancelling at UI must not unlock; held confirmation must not attack; repeated interaction must not replay; pre-existing input locks must not be reset; no toast before controls return. Pending animation means pose and hand/weapon contact remain unverified. QTE outcome injection is a test aid, not swipe verification.

Ruling: user has already approved the storyboard and requested implementation, so no additional design/plan approval gate is needed. Existing item UI appearance is reused; animation timing placeholders remain explicit in the graph.

Ruling: shared ItemAcquisitionSubsystem/SceneAction arrived during this task. Replace the initial WBP_GetItem instance callback approach with the new shared presentation/input lifecycle, leaving other chat's implementation unchanged. DA_RustySword contains real sword sprite, name and neutral descriptive text; no invented stats.

Review P1 reproduced: Constellation.SwordAcquisition.InputOwnership failed because movement/look locks did not disable pawn attack input. Preserve Pawn::InputEnabled and disable through completion; restore only the originally enabled state. RED log: Saved/Logs/SwordInputRed.log.

Review P2 requires checking Unreal Python's bool+out-string binding rather than assuming a Python bool return. Installer records API doc, successful return type/value and null-input failure value before saving.

Review P2 resolved: observed `str | None` binding makes the installer success assertion correct; reviewer withdrew P2.

Actual PIE found a separate attack gate: the current Ac_Ability and player Blueprint use IsAttackUnlocked / NewEnumerator3 in addition to legacy IsCombatUnlocked. Commit now grants both via existing Unlock Ability entry points, without granting Dodge. The attack-only branch has no duplicate ability-UI hook. Fresh engine exports are under Saved/SwordAcquisition/AttackInspection. Runs 221825 and 222423 reproduced the missing attack execution before this fix.

Native input ownership test fixture now initializes its world before exercising dynamic actor callbacks. Without InitializeActorsForPlay, AActor::ProcessEvent intentionally skipped the completion callback, causing a fixture-only cancellation assertion failure. Real PIE cancellation already passed. Final InputOwnership (including no attack grant on cancellation) passes in Saved_SwordAutomation20261021/Logs/SwordIntegrationGreen04.log. Shared ItemAcquisition five tests and GrantWithoutDuplicateUI pass in SwordIntegrationGreen02.log.

Visual review caught a separate SceneDirector defect: dialogue after a QTE branch updated state but had no screen widget. PlayDirector had only inspected ActiveCues (the initial branch prefix). The widget creation condition now also inspects RuntimeSource->Steps, matching the full authored graph. The widget stays collapsed while dialogue is empty. Read-only review accepted the change. The pre-fix visual evidence is FunctionalReview-20261021-223018/frame-00152.png; do not present that earlier video as final.

Final verification: FunctionalReview-20261021-223521/result.json has no error; cancellation/retry, control-before-toast, duplicate suppression, blocked attack during camera return, and actual GP_AM_Sword_Attack_Horizontal playback all pass. Saved map hash was unchanged by PIE. Actual dialogue display confirmed in frame-00155.png. UI and toast also captured. Final movie: SwordAcquisition_FunctionalPreview.mp4 in that directory; fully decoded with ffmpeg without errors. Related QTE/dialogue regression suite: 13/13 success in Saved_SwordAutomation20261021/Logs/SwordDialogueRegression.log. Installed graph contract passes. Animation remains pending; physical swipe is not claimed as verified. No new inventory/save persistence was added.
