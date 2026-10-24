# Furniture pickup implementation plan
User-approved design: character stays still; object moves and rotates to the fitted pickup pose before the two-hand animation. Preserve approved Hold/Throw and character appearance.
Goal: grounded two-hand pickup with sleeve clearance, continuous prop contact, collision-checked alignment, and runtime comparison videos.
Architecture: optional per-item Pickup montage + mesh-space ground pose. CarryComponent aligns the prop while PickingUp, then starts montage; contact enables existing lift interpolation. Add only a pickup cuff morph to the mesh. Existing small-item behavior remains.
Tech: Unreal 5.8 C++, Python asset controller, Blender 5.2.1 guarded CLI.
- [ ] Test fitted alignment changes object without moving character; cancellation restores simulation; obstacles prevent alignment. Run red before behavior.
- [ ] Add optional profile data and implement alignment with swept path checks and incremental rotation checks. Reset on abort; do not bypass collision safety.
- [ ] Import separate Pickup sequences/montages and cuff morph; preserve materials, old morphs, Hold/Throw.
- [ ] Verify clips and contact notify after reload; run Carry tests and actual PIE aligned pickup/hold/walk/throw, plus obstructed alignment.
- [ ] Save before/after videos and precise remaining limitations. No shutdown while unfinished.
No Clean/Rebuild or Intermediate deletion; check competing builds/editor before build/import.
