# Fall animation integration

Approved scope: apply the reviewed Normal_AB Garment07, Weak_C Garment06 and Severe_D Garment04 to the current heroine. Preserve body poses, fingers, existing morphs/materials and fall damage thresholds. Strong landing returns through the previously approved get-up animation (user confirmed this turn).

1. Read current player/animation graphs and mesh metadata. Back up only assets and source files that will change; do not clean build directories.
2. Export reviewed bone tracks and clothing curves using the existing 94-bone coordinate conversion. Merge new clothing shapes into a staging source without losing existing shapes; validate material-slot and shape inventories before replacing the game mesh.
3. Separate airborne loops, landing phases and the strong prone/get-up transition. Remove review-only world drop trajectories. Keep runtime capsule movement authoritative. Validate contact frames and seams before enabling playback.
4. Connect playback to PlayerFallComponent lifecycle without changing damage/height thresholds. Preserve input-lock ownership, abort on suspension, clear owned animation on reset, and release only the matching landing generation. Use bounded completion/watchdog handling.
5. Build incrementally only when no competing build is active. Extend existing fall lifecycle checks for animation completion/cancellation. Import assets and reload in a fresh engine process.
6. Run the actual heroine in PIE with normal/weak/strong drops, input recovery, repeat falls and interruption. Capture full-body and hand close views at normal/slow speed. Inspect intermediate poses, contact and garments; fix in scope issues and rerun affected checks.
7. Save review videos and a manifest separating Blender, imported sequence, runtime and unverified cases. Do not claim game verification from sequence preview or data equality.

Delivery workspace: FallLanding_Heroine01/UnrealApply01 under this chat's visualization root.
