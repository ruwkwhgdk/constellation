# Unreal 어빌리티 획득 UI 적용

2026-10-09. 승인된 벽화 시안을 실제 `Ac_Ability`의 신규 획득 흐름에 연결했다.

## 실행 및 미리보기

에디터에서 게임 실행 후 점프·전투 기술·변신을 처음 해금하면 자동 재생된다. 진행 중인 SceneEvent와 시네마틱이 끝난 후 표시한다. 이미 열린 어빌리티를 다시 해금하거나 잠글 때는 재생하지 않는다.

개발 빌드의 게임 콘솔에서 진행 데이터를 변경하지 않고 확인할 수 있다.

- `AbilityUI.Preview 0 0` — α CrB, 첫 점프 획득
- `AbilityUI.Preview 1 1` — β CrB, 알파 보유
- `AbilityUI.Preview 2 3` — γ CrB, 알파·베타 보유
- `AbilityUI.Preview 1 4` — 베타 획득, 감마만 보유한 비순차 상태

처음 6.2초는 입력으로 닫히지 않는다. 이후 새 키 입력이나 마우스 클릭으로 0.7초 동안 페이드 아웃한다. 연출 중 게임은 일시정지하며 종료 시 이동/시점 제한, 커서, 포커스, 일시정지를 복원한다. 진입 전에 누른 게임 입력도 정리한다.

## 리소스와 수정 위치

- `Content/Constellation/UI/AbilityAcquisition/DA_AbilityAcquisition.uasset`: 배경·문양·별·연결선·설명 테이블·효과음 묶음.
- 같은 폴더의 UI 텍스처 35개와 합성 효과음 4개. 효과음은 시안용 임시 리소스이며 교체 가능하다.
- 설명은 기존 `DT_SequenceStringData`의 Jump / Combat / Metamorphosis 행을 그대로 참조한다.
- `Source/Constellation/AbilityAcquisitionWidget.cpp`: 렌더링과 타임라인.
- `Source/Constellation/AbilityAcquisitionSubsystem.cpp`: 획득 큐, 입력, 복귀 처리.
- `ArtSource/UI/AbilityAcquisition/export-unreal.cjs`: 승인된 HTML canvas를 개별 PNG 레이어로 내보내기.
- `tools/setup-ability-acquisition.py`: 에셋 재생성 및 3개 해금 훅 설치. 이미 설치된 훅은 중복 추가하지 않는다.

그리스 문자를 잘못 매핑하는 기존 Hylia 폰트 대신 엔진 기본 합성 폰트를 사용했다. 웹 시안의 serif 글꼴과는 서체 차이가 있으며, 별자리/벽화 레이어는 승인된 원본에서 추출했다. 나머지 4개 별 슬롯은 미획득 상태로 남아 있다.

## 검증 범위

Editor Development 빌드, `Constellation.AbilityAcquisition` 자동화 테스트 2개, 실제 Unreal standalone의 1920×1080 캡처와 복귀 검사를 수행한다. 자동화는 실제 Ac_Ability Unlock Ability 함수를 호출하여 세 훅, 중복 해금, 비순차 해금, 잠금 처리와 원래 해금 플래그 보존을 확인한다.

Standalone 점검은 `-AbilityUIReview -AbilityUISlot=2`에서만 활성화되며 이동 키를 누른 상태를 재현한다. 결과는 별도 UserDir 아래 `Saved/AbilityAcquisition/standalone-result.txt`에 기록한다. 패키징된 Shipping 실행 및 전체 스토리 플레이스루는 이번 검증 범위에 포함하지 않았다.

최종 실행 캡처: `unreal-gamma.png`.
빌드/자동화/실행 로그: 프로젝트 `Saved/Logs/Ability-build.log`, `Ability-tests.log`, `Ability-visual.log`.

## 검토 기록

- 입력 해제 이벤트가 UI에 소비되어 이전 이동 키가 남는 문제: 재현 실패 결과 확인 후 진입/복귀 시 FlushPressedKeys로 수정, 동일 실행 검사로 재검증.
- Python 설치 반환값: UE 5.8 실제 바인딩은 성공 시 str, 실패 시 None임을 확인했다. tuple 검사 제안은 적용하지 않고 기존 None 검사 유지 및 두 번째 호출에도 동일 검사 추가.
- 변경은 로컬 작업 파일에 유지하며 기존 다른 작업은 포함하거나 커밋하지 않았다.
