# Interaction prompt

The heroine previews the action that pressing the current interaction key can perform. The prompt sits at screen anchor (0.60, 0.55), with a separate key label and the supplied Figma background. It consumes no pointer or keyboard input. No ellipsis or arrow is added.

## Content

- Source PNG: `ArtSource/UI/InteractionPrompt/T_InteractionPrompt_Background.png` (user-provided Figma export, retained unchanged).
- Texture: `/Game/Constellation/UI/Art/T_InteractionPrompt_Background`, UI group, no mipmaps, RGBA UI compression.
- Player: `/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine`, `InteractionPrompt` component.
- Enum: `EInteractionAction` in `Source/Constellation/InteractionPromptComponent.h`.
- Layout: `Source/Constellation/InteractionPromptWidget.cpp`.

The component stores the texture reference and editable ordered class rules directly in the saved player Blueprint. Rules match derived classes, with more specific classes first. New object behavior can be configured through these rules without adding labels to the widget.

| Action | Label | Existing object/state |
|---|---|---|
| PickUp | 들기 | Usable `HoldableComponent` in the actual carry sweep; includes furniture |
| PutDown | 내려놓기 | Carrying with valid floor, clearance and release path |
| CancelAim | 조준 취소 | Aiming while carrying |
| Open / Close | 열기 / 닫기 | School door `IsOpen` |
| Open | 열기 | Unopened chest / locker; gate |
| Read | 읽기 | Book |
| Climb / Descend | 오르기 / 내려가기 | Ladder; hit component tagged `LadderTop` selects descent |
| Activate / Deactivate | 켜기 / 끄기 | Active switch, according to `bIsOn` |
| Collect | 획득하기 | Sword and star objects |
| Play | 연주하기 | Grand piano |
| Restore | 회복하기 | Girl statue |
| Reset | 원위치로 돌리기 | Reset kiosk |
| Inspect | 조사하기 | Star sequence objects, including combat/transform subclasses |
| Interact | 상호작용 | Generic interactable base / position-gated base |
| None | Hidden | No executable action |

The inventory found 17 `BPI_Interact` Blueprint classes under `/Game/Constellation`; 15 ordered rules cover these via inheritance. Carryable objects use their existing component instead of class-name rules. Automatically collected objects and push/combat-only props are not advertised as F interactions.

## Availability and input

Carry selection reuses `FindInteractionItem` in the actual input handler. The generic trace matches the existing `Ac_Interact` graph: Hips socket, 120 cm forward, 45 cm sphere, Interact channel, simple collision. UI queries are read-only. Completed chests/lockers, inactive switches, one-shot sequence objects and required overlap regions follow their existing state fields. Hidden actors, action transitions, input-blocked states, UI-only input mode and pause hide the prompt.

The key label queries the local Enhanced Input mapping for `IA_Interact`. It displays F with the current mapping, follows remapping, and hides if explicitly unbound. The component ticks during pause to clear stale UI. The widget is removed when the player component ends play.

## Reproduction and verification

- `tools/audit-interaction-prompts.py`: read-only interface inventory and graph export.
- `tools/setup-interaction-prompt.py`: imports the managed PNG and installs/updates the component, preserving a pre-change player backup in Saved.
- `tools/verify-interaction-prompt.py`: reloads component settings, class coverage and texture hard dependency.
- Unreal automation filter: `Constellation.`; focused tests: `Constellation.InteractionPrompt`.
- `tools/review-interaction-prompt.py`: run in `L_Carry_Review` PIE with `-RenderOffscreen`; checks actual input, display lifecycle, pause and key remapping. Screenshots and reports: `Saved/InteractionPromptReview`.

Do not infer a packaged build result from editor tests. Existing invalid DodgeTimeline curve and plugin dependency warnings are outside this UI change.

## Verified 2026-10-03

- ConstellationEditor Development build succeeded.
- Project automation: 10 tests passed, 0 failed (3 tests have existing warnings).
- Saved-player PIE review: 19 checks passed, including pre-input display, target identity, actual pickup/place, aiming cancel, pause/resume, F-to-G remapping and unbound-key hiding.
- Reload check: exactly one component, all 17 inventoried classes covered, and a hard texture dependency in the asset registry.
- Visual review: `prompt-pickup.png` and `prompt-putdown.png` show the supplied background, Korean labels, separate F key, and no arrow/ellipsis.
- Actual AbandonedSchool PIE: 9 checks passed, including the existing chair, pause/resume, G remapping, unbound input and blocked movement. The offscreen test dismisses the opening movement tutorial and enters game input mode before positioning the player. Visible cursor alone is not treated as an input block. Screenshots: `school-prompt-pickup.png`, `school-prompt-remapped.png`.

## 기획자용 상호작용 문구 편집

콘텐츠 브라우저에서 /Game/Constellation/Gameplay/Interaction/Data/ST_InteractionActions 를 연다.
PickUp(들기), PutDown(내려놓기), Open(열기) 등 16개 키의 **Source String**을 수정하고 저장한다.
키는 EInteractionAction 이름과 연결되므로 유지한다. None은 문구가 없다.
코드 컴파일 없이 수정할 수 있으며 PIE로 결과를 확인한다.

BP_Player_Heroine의 InteractionPrompt 컴포넌트 → Interaction / Action Strings가 이 에셋을 직접 참조한다.
문구 조회는 FText::FromStringTable을 사용하므로 String Table의 번역을 사용할 수 있다.
테이블 미지정, 키 누락 또는 빈 문구는 해당 안내를 숨긴다.
상호작용 키(F 등)는 입력 바인딩에서 조회하며 이 String Table에 포함되지 않는다.

기존 NSLOCTEXT 문구 정의는 제거했다. 최초 문구 보존용 CSV는 ArtSource/Gameplay/Interaction/initial-action-strings.csv이며,
실제 수정 기준은 엔진의 ST_InteractionActions이다. tools/setup-interaction-strings.py는 테이블이 이미 있으면 문구를 덮어쓰지 않는다.
tools/verify-interaction-strings.py는 최초 16개 문구 이관 확인용으로, 이후 의도적인 기획 편집 시 원본과 달라지는 것은 정상이다.

2026-10-03 문자열 이전 검증: 빌드 성공. 별도 프로세스 재로딩에서 16개 문구와 플레이어 연결 확인. 상호작용 자동 검사 3개 통과(1개 경고 포함). 그래픽 플레이 검사는 에디터 시작 중 컴퓨터 멈춤으로 완료하지 못했으며, 이전 캡처를 새 검증 결과로 사용하지 않는다. 보고서: Saved/InteractionPromptReview/strings-reload.json 및 StringTests/index.json.
