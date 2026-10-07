# Scene Director 구현 기록

기준 계획: docs/2026-10-03-sequencer-designer-tool-plan.md

사용자 보완: 기획자 1명이 AI를 개발 파트너로 활용해 제작·유지보수한다. 전문 개발자 상주를 전제하지 않는다. 기존 작업일 추정은 사람 개발 기준 참고값이며 AI 작업의 소요 시간을 약속하지 않는다.

실행 결정: 사용자의 진행 지시에 따라 이 세션에서 구현한다. 기존 로컬 미커밋 콘텐츠를 보존하고 신규 플러그인에 분리한다. 별도 worktree로 현재 콘텐츠를 복제하지 않는다.

## 순서

- [x] 원본 에셋과 검증·컴파일: 순환, 누락 BP, 잘못된 역할, 음수 시간, 고아 노드, 재생성 중복을 Unreal Automation으로 확인한다.
- [x] 실제 시퀀스 생성: Spawnable, 위치 트랙, 카메라 컷, 지정 길이를 생성한다. 실패 시 마지막 정상 결과 보존.
- [x] 그래프 에디터: 노드 추가·연결, 속성, 위치 캡처, 검증·생성, 시퀀서 열기, 샘플 생성, 저장·Undo/Redo.
- [x] 런타임 실행 Actor: 시작·중지·종료 정리와 카메라 복구, Blueprint 호출.
- [x] 빌드·자동화 테스트·사용 가이드 및 AI 수정 지침.

첫 배포 범위는 Start/NPC/Camera/Wait/End로 연결된 연출이다. 애니메이션, 기존 시퀀스 삽입, 게임 액션, 분기·병렬은 후속 기능으로 명시한다. UI가 제공하지 않는 기능을 제공한다고 표시하지 않는다.

파일 위치: Plugins/ConstellationSceneDirector/Source/SceneDirectorRuntime에는 에셋과 실행 Actor, SceneDirectorEditor에는 컴파일러·그래프·툴킷·팩토리·테스트를 둔다.

검증은 설치 UE 5.8의 ConstellationEditor 빌드와 Constellation.SceneDirector 자동화 테스트로 수행한다. 최종 사용자에게 남은 실행·시각 검증을 구분해 보고한다.

## 검증 결과

- UE 5.8.0 ConstellationEditor Development 빌드 성공.
- Constellation Win64 Shipping 빌드 성공. Cook/Stage/패키지 실행은 미검증.
- Constellation.SceneDirector 자동화 테스트 7개 통과: 생성·재생성, 실제 편집기와 임베디드 미리보기, 그래프 왕복, 잘못된 입력, 노드 이동 Undo/Redo, 런타임 수명, 정상 그래프.
- 런타임 수명 테스트는 20회 시작·중지, 실제 NPC 바인딩 생성·제거, 원래 카메라 복구, 재생 시간 경과 후 자연 종료를 확인.
- 별도 렌더링 프로세스에서 EditorSmoke 통과. Saved/SceneDirector-editor.png를 시각 확인. 작은 창에서 잘리던 버튼을 줄바꿈하도록 수정.
- 새 Unreal 프로세스에서 저장된 예제 그래프·내장 Level Sequence·BP 메시 재로딩 통과. Saved/SceneDirector-reload.json에 결과 저장.
- 독립 코드 리뷰에서 지적된 이동 Undo/Redo 유실을 회귀 테스트로 재현 후 수정하고 재검토 완료.
- 미리보기 통합 테스트가 포착한 SpawnRegister 누락을 LevelSequenceEditor의 표준 등록 방식으로 수정.
- 자연 종료 테스트 월드는 InitializeActorsForPlay가 필요하다. 초기화 전 월드는 AActor::ProcessEvent가 종료 이벤트를 차단하므로, 단순 CreateWorld로는 실제 게임의 이벤트 전달을 재현할 수 없다.

## 알려진 외부 제약

Development 게임 타깃은 기존 Source/Constellation/CarryDataTests.cpp 및 InteractionStringsTests.cpp의 FStringTable::SetSourceString 인자 개수 오류로 빌드 실패했다. 이 기능과 무관한 기존 파일은 수정하지 않았다. Shipping 타깃은 성공했다.

## 인수인계

사용 가이드: Plugins/ConstellationSceneDirector/README.ko.md
예제: /Game/SceneDirector/Examples/DA_FirstScene 및 L_FirstScene
테스트: tools/test-scene-director.ps1

현재 완료는 첫 사용 가능한 기반 버전이다. 원래 계획의 기존 시퀀스 삽입·등록형 BP 액션·애니메이션·이동·분기·병렬까지 완료한 것은 아니다. 다음 구현은 예제의 실제 NPC 교체 검증과 등록형 액션/기존 시퀀스 재사용을 우선한다.
