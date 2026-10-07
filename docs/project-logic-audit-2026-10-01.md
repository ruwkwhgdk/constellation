# 프로젝트 코드·블루프린트 검사 — 2026-10-01

## 현재 상태

재현된 네이티브 코드 오류와 블루프린트 4개, 샘플 맵 1개의 오류를 수정하여 저장했다. 사용자가 에디터를 종료한 뒤 파일 잠금이 해제되어 원본 에셋 저장에 성공했다. **회피 곡선은 사용자의 명시적 선택에 따라 보류했다.**

전체 에셋의 목록·컴파일 검사를 수행했지만, 모든 게임플레이 경로의 논리적 정확성을 입증한 것은 아니다. 아래 미해결 항목과 실제 플레이 검증이 남아 있다.

## 조사 범위

- `/Game` 블루프린트 222개: 일반 201, 위젯 17, 애니메이션 3, Control Rig 1.
- 그래프 563개, 노드 6,464개 추출; orphan pin 0개. 레벨 그래프는 별도 검사.
- 맵 27개: 최종 레벨 블루프린트 없음 19개, 컴파일 성공 8개, 오류 0개. 최초 검사에서 오류가 있던 샘플 맵도 수정했다.
- 프로젝트 런타임 C++, 에디터 플러그인, 설정, 기존 테스트 검토. 로직 검토는 저장·퀘스트·UI·이동·AI 실패 경로에 집중.
- Python 398개 구문 검사. 과거 아트 제작 스크립트를 모두 실행하거나 모든 로직을 검증한 것은 아님.

## 적용한 코드 수정

| 영역 | 오류와 수정 |
|---|---|
| 재화·퀘스트 저장 | 서로 다른 캐시가 같은 슬롯을 덮어쓰면서 상대 시스템의 최신 값을 잃음. 저장 직전 디스크 내용을 읽고 자기 소유 필드만 갱신. 읽기·쓰기 실패 로그 추가. |
| 재화 | StarCoin/DummyItem 지급, StarCoin 소비 즉시 저장. 정수 덧셈 오버플로를 방지. Gold의 기존 세션 한정 정책은 유지. |
| 퀘스트 | InnerProgress 저장·복원 및 퀘스트 로그 UI 갱신. 큰 진행도 증분의 정수 오버플로 방지. |
| 콜백 | 블루프린트 콜백이 퀘스트 맵을 바꾸는 경우의 참조 무효화 방지. 해금 조건에서 데이터베이스를 재등록할 때 동일 퀘스트가 무한 재진입하지 않도록 평가 중 집합 추가. |
| 퀘스트 마커 | 카메라 뒤에서 투영이 실패했을 때 미초기화 좌표를 사용하던 문제 수정. 클립 공간 방향으로 가장자리 위치 계산, 유효하지 않은 값은 숨김. |
| 슬라임 등반 | 첫 표면 탐색 실패 시 원점으로 이동하던 복원 위치 초기화. 샘플 수 0 방지. 음수 점수에서 발산·음수가 되던 후보 가중치 수정. |
| 튜토리얼 | Dismiss 없이 위젯이 제거될 때 입력 모드·커서 복구. 지연 포커스 타이머 취소. 교체된 이전 위젯이 새 프롬프트 입력을 해제하지 않도록 처리. |

## 저장한 블루프린트·레벨 수정

`tools/apply-reviewed-blueprint-repairs.py`가 원본 백업, 수정 전 해시 확인, 컴파일, 저장, 재실행 시 변경 0건 확인을 수행한다. 복제본 검사는 `tools/preview-blueprint-repairs.py`로 재현할 수 있다.

| 에셋 | 준비된 수정 | 복제본 결과 |
|---|---|---|
| BP_QuestProgressTrigger | 퀘스트 진행 함수가 실패해도 일회성 트리거를 소모하던 2개 경로에 성공 여부 분기 추가 | 오류 0 / 경고 0 |
| BTT_Attack | 캐스팅 실패 시 FinishExecute(false) 호출 | 오류 0 / 경고 0 |
| BTT_GetNextPatrolPoint | 캐스팅 실패 2개 경로에서 FinishExecute(false). 배열 인덱스 검사 후에만 위치 조회. 잘못된 인덱스는 0으로 되돌린 뒤 실패하여 다음 시도에서 복구 | 오류 0 / 경고 0 |
| BTS_CheckDistance | 대상 액터 캐스팅 실패 시 공격 거리 블랙보드 값을 false로 해제 | 오류 0 / 경고 0 |
| LCaves_Will_Chambers_Contribution_Showcase | 런타임에 남은 에디터 전용 Play 호출과 끊어진 액터 리터럴 제거. 기존 시네마틱 모드 설정은 유지 | 오류 0 / 경고 0 |

백업은 `Saved/ProjectAudit/20261001/backups/`에 있다. 수정 전후 해시와 저장 기록은 applied-blueprint-repairs.json, showcase-repair.json에 보존했다. 새 프로세스에서 재로드·컴파일·추가 변경 0건 확인 결과는 saved-verification.json에 기록한다. 샘플 맵 저장 과정에서 함께 재직렬화된 BuiltData는 HEAD의 원본 LFS 데이터로 복원하고 SHA-256 일치를 확인하여 조명 데이터 변경을 제외했다.

## 미해결·추가 검증 항목

1. **사용자 요청으로 보류:** `BP_Player_Heroine`의 `DodgeTimeline` / `DodgeTrack` CurveFloat 포인터가 None이다. 기존 리소스 이동 기록을 임시 적용하여 자동 저장본 8개를 읽었지만 모두 같은 곡선이 누락되어 있었다. 원래 곡선 값을 복구하지 못했으며 임의의 회피 거리·속도를 추가하지 않았다. 곡선 엔진 경고는 남는다. 역사 자료는 historical-timelines.json 참조.
2. 기존 세이브 파일의 마이그레이션은 실물 파일로 시험하지 않았다. 새 `InnerProgress` 필드는 기본값 0으로 선언했고 신규 형식 저장·재로드는 시험했다. 사용자 저장 파일은 건드리지 않았다.
3. 실제 뷰포트의 입력 포커스, 카메라 뒤 마커, 슬라임 접촉·모서리 이동, 적 AI 실패 복구를 PIE에서 확인해야 한다. Shipping 빌드·패키징·전체 맵 플레이 검증은 수행하지 않았다.

## 검증 기록

- 최초 저장 회귀 테스트: 수정 전 13개 assertion 실패를 재현.
- 해금 콜백 재진입: 평가 횟수 기대 1 / 실제 4로 실패를 재현한 뒤 수정.
- Editor Development 빌드: 성공. 최신 로그 `Saved/Logs/AuditBuild-final.log`. 에디터 종료 후 일반 모듈 DLL도 최신 코드로 빌드했다.
- Unreal 자동화 테스트: 최종 6개 전부 성공, 프로세스 종료 코드 0. `Saved/Logs/AuditTests-review-final.log` 참조.
- 기존 Python unittest 14개 성공.
- 독립 C++ SubwayStreamingGateTests, SubwayTravelGateTests 모두 실패 0.
- 블루프린트 allowlist 컴파일: 222개, 컴파일 오류 0 / 경고 0 / 로드 실패 0 (`AuditBlueprints-saved-final.log`). 마지막 순찰 복구 보강은 저장 후 별도 재로드 컴파일로 추가 검증. null 회피 곡선 엔진 경고는 별도 보류 항목이다.
- 맵 27개 레벨 스크립트 최종 검사: 오류 0 / 경고 0 (`AuditLevels-saved-final.log`).
- 독립 코드 리뷰 후 저장 테스트의 null 로드 검증, 퀘스트 재진입, 실패한 순찰 인덱스 복구를 보강했다. 최종 추가 리뷰에서 차단할 문제가 없음을 확인했다. `GetLevelScriptBlueprint(true)`는 엔진 헤더의 `bDontCreate` 의미를 확인하여 유지했다.

상세 산출물은 `Saved/ProjectAudit/20261001/`의 inventory.json, compact-graphs.json, level-results.json, repair-preview.json, python-syntax.json 및 그래프 덤프에 있다. Saved 아래 자료는 Git 추적 대상이 아니다. 재검사 도구는 tools 아래 소스에 보존했다.
