# Dialogue — Quiet Nebula + Star

2026-10-11 · 사용자 제공 D 시안의 게임 적용본.

## 적용

- 게임/연출 미리보기 공용 `SDirectorDialogue`: 청흑색 벽화 질감, 가는 금색 캡슐 테두리, 양끝 장식, 이름표, 하단 별·삼각형 표시.
- 기존 HUD의 `WBP_Dialogue`: 동일 리소스로 교체. 기존 Name/Description/NextButton 식별자와 이벤트 그래프 보존. 대사창 전체 클릭 영역으로 기존 다음 진행 이벤트 호출.
- 이름/대사는 텍스처에 포함하지 않는다. 한글은 엔진 Roboto 합성 폰트 및 폴백으로 표시한다.
- 선택지 리소스와 대화 진행 규칙은 유지. 베이지색 시안 배경과 상단 D 제목은 게임 리소스에 포함하지 않는다.

## 리소스

`T_Dialogue_QuietNebulaAtlas.png`는 ImageGen으로 제작한 1536×1024 RGBA 원본이다. 생성 후 이미지를 재도색하지 않고 각 부분을 UV로 분리하여 사용한다.

| 부분 | 픽셀 영역 (최소 → 최대) |
|---|---|
| 대화 배경 | (32,185) → (1504,504) |
| 이름표 | (35,562) → (552,675) |
| 진행 표시 | (648,682) → (888,934) |

게임 에셋: `/Game/Constellation/UI/Dialogue/T_Dialogue_QuietNebulaAtlas`.
UI 그룹, UI 압축, sRGB, mipmap 없음. 기존 리소스는 다른 사용처와 복구를 위해 보존한다.

## 수정 및 재적용

- `tools/import-dialogue-quiet-nebula.py`: atlas import.
- `tools/apply-dialogue-quiet-nebula.py`: 구형 WBP 교체. 원본 백업은 `Saved/DialogueRestyle/WBP_Dialogue.before.uasset`에 한 번 저장한다. 그래프 동일성을 검사한 뒤 저장한다.
- `DialogueStyleEditorLibrary.cpp`: 구형 UMG의 위치와 폰트 및 UV 설정. 공유 글꼴 테이블을 변경하지 않고 전용 스타일 테이블을 위젯 패키지에 저장한다.
- `SDirectorDialogue.cpp`: 공용 Slate 대화창의 레이아웃과 UV. 다른 커스텀 텍스처를 지정한 경우 기존 브러시 설정 유지.

## 검증

Editor Development 빌드 성공. `Constellation.SceneDirector.DialogueUI`, `ConversationRuntime`, `ConversationSchedule` 통과. 저장한 구형 위젯의 atlas UV 및 한글 캡처 확인. 이벤트 그래프 교체 전후 일치.

`tools/verify-dialogue-quiet-nebula-pie.py`는 별도 테스트 프로세스의 Entry 맵에서 임시 대화 연출을 만들어 실제 PIE 표시/입력 대기/다음 진행을 확인한다. 맵과 진행 데이터는 저장하지 않는다. 실행 시 `-UserDir=<project>/Saved/DialogueRestyle/PIE`를 사용한다. 전체 스토리 플레이스루 및 Shipping 패키징은 미검증.

시각 확인용 캡처는 `legacy-dialogue-review.png` 및 `dialogue-game.png`. 검증 로그는 프로젝트 `Saved/DialogueRestyle/`에 있다.
