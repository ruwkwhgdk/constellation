# Jump ability acquisition implementation

Goal: Run the approved eight-beat acquisition scene on the existing jump star interaction in AbandonedSchool.
Architecture: SceneDirector graph owns timing/camera/narration. A scoped JumpAcquisitionStage owns character pose/absorption and commits the existing ability/quest flow. Existing acquisition UI receives an explicit cinematic presentation lease, pauses world time, and returns through white. Existing star BP gets a binding-first route; other instances retain their original path.
Tech stack: Unreal 5.8 C++, SceneDirector, editor Python, existing heroine rig and ability UI.
Spec: ArtSource/JumpAbility/Storyboard/2026-10-18-v01/Storyboard_Direction_v01.txt (approved).

- [x] Discover live star and original interaction flow; star_object_jump at (-13700,-2450,-800), BP_Star_Object.
- [x] Add scoped cinematic UI presentation and test cancel/duplicate/input ownership.
- [x] Add graph-driven stage and compatible anatomical arm/head pose driver, absorption visual.
- [x] Add idempotent binding-first BP hook; author graph, narration row, binding, stage.
- [x] Build without clean; compile/reload assets; real interaction, cancel/retry and UI handoff validation.
- [x] Capture actual game video and review camera/pose; document remaining visual limitations.

Execution ledger
- Shared checkout explicitly requested for real map integration; no worktree conversion or unrelated commits. Do not touch Intermediate or active character animation work.
- Existing ability UI refuses busy scene events. A narrowly owned presentation lease is needed; ordinary queued UI behavior remains unchanged.
- Existing idle pose feeds a temporary post-process IK correction. No .blend, mesh, skin weights, or ABP changes. Carry's interleaved twist bones must be preserved.
- Only this jump star routes into the graph. Original dialogue/tutorial/jump callbacks must not execute in parallel.
- Record validation under Saved/JumpAcquisition; backups before any asset write.

Implementation notes (2026-10-18)
- Graph: /Game/SceneDirector/School/DA_JumpAcquisition, EventKey JumpAcquisition, 34 nodes.
- Map: /Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool; star_object_jump -> JumpAcquisition_Interaction -> JumpAcquisition_Stage.
- String row: DT_SequenceStringData / AbandonedSchool_JumpAcquisition_Obtained.
- Ability UI retains its original reading gate and text. The scene leases its overlay, pauses world time, then restores only its own input/pause state.
- Existing Ac_Ability Unlock Ability grants jump at the final graph action; UI enqueue is suppressed only during this commit. Quest delegate and tutorial toast follow success.
- The continuous CameraSwitch overlaps non-activating CameraMove nodes. This preserves the shot across Wait, paused UI, and click dialogue without changing the shared compiler's linear-graph behavior.
- Character motion uses temporary post-process anatomical arm IK and head aiming over the existing idle ABP. No animation source/model/rig changes. This is procedural pose work, not a newly authored facial/body animation clip.
- Absorption uses shrinking original star, gold instanced motes flowing toward the upper chest, response light, and white transitions. It does not currently use a per-pixel edge-dissolve shader.
- Review04 real interaction: all beats reached, UI displayed, jump flag set, input/pause restored. Final wider framing captured separately in Review05.
- Build8: succeeded. Saved asset verification passed. Tests-final: 3/3 native automation tests passed.
- User steering: reaching-arm animation quality will be handled in a separate production task. Keep this pose provisional; do not spend further time polishing the procedural reach. Replace Reach/Contact/Surprise pose driving when the approved animation is delivered.
- Cancellation regression: stopping while the ability UI owns pause destroyed the runner before the stage listener ran. Restore now resolves the pending-kill runner during the same broadcast to release the UI lease. Build9 succeeded; Lifecycle02 confirmed UI/pause/input restoration, then hit a Python-only hidden-property accessor error (fixed in Lifecycle03).

- Final actual-game capture: Saved/JumpAcquisition/Review05/JumpAcquisition_InGame.mp4. All eight phases, continuous cinematic camera, UI, jump flag and restored input/pause asserted. MP4 decode check passed. The preview is silent; UI hold time is preserved using capture timestamps.
- Lifecycle03 completed cancellation -> restoration -> interaction retry -> successful grant, then the optional simulated-revisit probe could not write the read-only Completed property. That probe was removed; actual map reload/save persistence is not claimed as tested.
- Remaining visual work explicitly deferred by user: replacement authored reach animation. Procedural hand/head poses remain as integration placeholders; face morph performance has not been authored.
- Lifecycle04 final validation passed: cancel/retry, completed, jump_unlocked, input_restored. Shared editor released at 20:45 KST; no editor/build processes remained.
