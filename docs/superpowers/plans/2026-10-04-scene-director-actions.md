# 등록형 블루프린트 액션 구현 계획

목표: 기획자가 오른쪽에 Key/BP를 등록하고 게임 액션 노드에서 Key, 대상 NPC, ID, 수량을 입력하여 선택한 경로에서 게임 기능을 호출한다.
사용자 지정 다음 작업으로 현재 작업 공간에서 직접 구현한다. 게임 모듈 의존 없이 Blueprintable UObject의 동기 Execute 함수로 프로젝트 API에 연결한다.

## 규칙
- 동기 함수만 지원. Delay/비동기 완료 대기는 후속 범위.
- 생성/스크럽/미리보기는 실행하지 않음. 게임/PIE만 호출.
- 미선택 경로, 선택 대기 뒤는 호출하지 않으며 분기 재생성에도 한 번만 호출.
- 실패는 LastError와 실행 이력에 기록하고 연출을 종료해 입력/카메라 복구.
- 이미 수행한 게임 상태 변경은 롤백하지 않음. 새 재생의 중복 보상 방지는 게임 API 책임.
- 빈/중복 Key, 추상 클래스, 미등록 액션, 선행 NPC 누락 검사. Key rename 전파.
- 중지/재진입, 큰 Tick, 중첩 분기, 실패 후 후속 실행 차단 검증.

## 작업
- [x] 인터페이스/파라미터, 등록 목록, 컴파일 검증과 경로 복사.
- [x] 실행기 한 번 호출/실패/재진입 방어 및 실행 이력.
- [x] 메뉴/노드 제목/오른쪽 목록/Key 선택/이름 변경.
- [x] 실제 BP 예제, 그래프와 맵 저장 및 프로젝트 API 연결 사용법.
- [x] 런타임/편집기 회귀, Editor/Shipping 빌드, 렌더링 검증.


## 완료 검증 (2026-10-04)
- Editor Development 빌드 성공. 자동화 40개 전체 통과 (`Saved/Logs/SceneDirector-tests.log`).
- Shipping 빌드 성공 (`Saved/Logs/Actions-shipping-build.log`). Cook/패키징된 게임 실행은 미검증.
- ActionBlueprint: 저장한 실제 BP Execute 호출과 양쪽 선택 결과의 NPC 태그 변경 확인. 새 프로세스에서 애셋 재사용도 확인.
- ActionRuntime: 선택 대기/미선택 경로 차단, 중첩 결정 재생성 시 한 번 실행, 새 인스턴스 격리, 동기 실패/중지/재진입 차단, 액션만 있는 그래프, 새 세션 재실행 확인.
- ActionValidation: 미등록/중복/추상 BP/대상 NPC 오류, 실패 시 이전 생성물 보존, Key 변경과 그래프 왕복 확인. 컴파일 중 실행되지 않음.
- 실제 렌더링 EditorSmoke 성공. 액션 Key 선택 UI, 노드, 카메라와 대사 미리보기 확인 (`Saved/SceneDirector-actions-editor.png`).
- `tools/setup-scene-director-actions.py`로 DA_Actions/L_Actions, BP_ActionSetNPCTag/BP_ActionAcceptQuest 저장 완료.
- QuestSubsystem 연결 BP는 컴파일/저장만 검증했으며 실제 퀘스트 수락 및 저장 데이터 변경은 실행하지 않음. 재화 지급 BP는 이번에 생성하지 않음.
- 별도 코드 리뷰에서 확인된 결함 없음. 지적된 중첩/인스턴스 격리 검증 보완 후 전체 테스트 재통과.
