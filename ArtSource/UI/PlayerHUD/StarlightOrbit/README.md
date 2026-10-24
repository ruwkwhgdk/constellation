# Starlight Orbit HUD — v3 implementation

2026-10-13. Approved reference: ../Concepts/2026-10-13/hp-stamina-A-v3-star-feedback.png.

## Applied

- WBP_PlayerHUD now derives from UStarlightPlayerHUDWidget. Only original HPProgressBar and StaminaProgressBar are collapsed; other authored HUD content/graphs remain intact.
- Native layered Slate art: independently colored faceted star, fixed orbit, subdued existing RegionTitle/T_RegionNebula texture, navy empty tracks, coral HP and teal ST fills. No warning text or diamond icon.
- 560 × 120 Slate layout, bottom-center aligned (updated 2026-10-14), with editable symmetric horizontal padding 40 and bottom padding 28. HP 400 × 17; ST 360 × 12, aligned starts. UMG viewport DPI applies.
- Actual active pawn Ac_Stats current/max values take precedence. CombatAbilitySystem fallback supports native combat pawns. No resource values, costs, regeneration rules, input mode or pause rules are changed.
- Low HP: editable threshold 25%, editable 2-second red pulse. Actual accepted damage: 0.15-second hold plus 0.6-second loss-trail interpolation. Startup, healing and direct stat edits do not invent damage trails.
- Actual stamina rejection: 0.35-second orange response, two cycles ±2.5 Slate star-only horizontal shake. Fixed orbit and gauges; retriggers do not stack; 0.15-second cooldown. Restores gold/low-HP red. Empty ST retains navy track with grey edge.
- Legacy heroine IA_Dash rejected branch reports insufficient-stamina sprint attempts only. Other existing legacy actions have no stamina cost checks; none were invented.
- Native action and dodge rejection events cover zero and positive-but-insufficient amounts, and exclude other blocking conditions.
- Shared Ac_Stats Calculate Damage reports owner damage after OnHPChanged, covering transformed characters. Existing heroine notification is idempotent (pending boolean); it cannot stack trails. Widget destruction/rebinding removes native event subscriptions.

## Verification

- Development Editor C++ build successful.
- Automation: Constellation.StarlightHUD.ResourcesAndFeedback; Constellation.CombatCore.StaminaRejected.Action; Constellation.CombatCore.StaminaRejected.Dodge.
- tools/verify-starlight-hud-pie.py passed using saved assets in Template_Default: actual BPI_Damageable TakeDamage, actual Enhanced Input IA_Dash rejection, low-HP recovery, actual Execute Transform montage/possession, and transformed shared damage trail. See pie-result.json.
- Native tests additionally cover non-stamina blockers, positive residual insufficiency, cooldown/debounce, unchanged resource amounts, rebinding and event cleanup.
- Captures are actual 1280×720 editor PIE screenshots. Animation movement was checked over separate frames; no video exported. Additional ultrawide/DPI and dark production-level visual review remains a manual art QA item.
- PIE fixture changes are transient and use PropertyAccessChangeNotifyMode.NEVER to prevent editor reconstruction. Existing hit-stun/transform input changes are allowed during their own phases; the HUD itself does not modify them.
- Existing unrelated missing Carry animation dependency warnings appear in the editor logs; no changes were made to those assets.

## Maintenance

Source: Source/Constellation/StarlightPlayerHUDWidget.{h,cpp}. Native rejection hooks: CombatAbilitySystem / CombatDodge. Editor migration: PlayerHUDStyleEditorLibrary and tools/apply-starlight-hud.py. Migration backs up original assets under Saved/PlayerHUD before first modification. Logs/tests: Saved/PlayerHUD.

2026-10-14: Removed HP/ST text labels at user request; gauge geometry and bottom-center placement retained.
