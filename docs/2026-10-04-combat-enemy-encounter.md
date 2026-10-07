# 몬스터 감지·추적·복귀

## 이번 단계
기존 공격 패턴 선택에 감지 → NavMesh 접근 → 공격 거리 정지 → 시야 상실 시 마지막 위치 탐색 → 교전 포기 → 시작 위치 복귀를 연결했다. 기존 L_CombatCore는 유지하고 장애물 우회 시험용 L_CombatEncounter를 추가했다.

현재 단일 플레이어 시험장용 공통 구현이다. 플레이어0을 0.2초 간격으로 관찰하고 Visibility 충돌 채널로 시야를 검사한다. AI Perception의 청각·피격 공유, 다수 목표 선택, 보스 페이즈, 집단 공격 허가, 후퇴·측면 이동은 아직 없다.

## 시험 방법
- tools/play-combat-encounter.ps1 실행 또는 /Game/Constellation/Review/CombatCore/L_CombatEncounter 맵에서 플레이한다.
- WASD 이동, 마우스 시점, Tab 잠금, LMB 공격, Space 회피, RMB 취소, R 전체 시험 초기화.
- 낮은 장애물 너머의 슬라임이 옆으로 돌아 접근하고 Light/Heavy를 선택한다.
- 시작점에서 너무 멀리 유인하거나 시야를 충분히 오래 끊으면 돌아간다. 복귀 중에는 새 공격을 시작하지 않는다.
- 정상 복귀 시 HP/SP와 액션 쿨다운, 연속 패턴 이력을 초기화한다. 사망한 몬스터는 자동 부활하지 않는다.
- 몬스터 머리 위에 접근·탐색·복귀·경로 실패 상태와 기존 패턴 판단 이유가 표시된다.

플레이어 속도500cm/s와 기존 카메라 값은 그대로다. 아래220cm/s는 몬스터의 이동 속도다.

## 기획자 편집
/Game/Constellation/Review/CombatCore/DA_SlimeEncounter를 열어 수정한다. 몬스터의 Encounter Profile에 연결한다. 공격 종류와 피해·전조 타이밍은 기존 DA_SlimePatterns 및 각 CombatActionDefinition에서 수정한다.

| 속성 | 기본값 | 의미 |
|---|---:|---|
| Detect Radius | 800cm | 최초 발견 거리. 시야와 시작점 기준 교전 범위도 만족해야 함 |
| Lose Radius | 1100cm | 몬스터와 대상 사이 거리가 이 값을 넘으면 추적 포기 |
| Leash Radius | 700cm | 몬스터 또는 대상이 시작점에서 이 거리보다 멀어지면 복귀 |
| Attack Distance | 140cm | 수평 중심 거리 기준 접근을 멈추고 패턴 선택을 허용 |
| Move Speed | 220cm/s | 이 프로필을 사용하는 적의 이동 속도 |
| Think Interval | 0.2초 | 감지·상태 판단 간격. 실행 시작 때 적용 |
| Lost Sight Time | 3초 | 마지막 시야 확보 뒤 탐색 유지 시간 |
| Home Tolerance | 50cm | 시작점 복귀 완료 허용 오차 |
| Retry Delay | 1초 | 경로 재요청 최소 간격 |
| Retry Cooldown | 3초 | 복귀 후 재발견 및 복귀 경로 실패 후 대기 시간 |
| Stuck Timeout | 2초 | 이동 진척이 없을 때 해당 경로를 포기하는 시간 |
| Max Move Failures | 3회 | 추적 경로 연속 실패 허용 횟수 |
| Restore On Return | true | 복귀 완료 시 HP/SP100 및 액션 쿨다운 초기화 |

Detect Radius보다 Leash Radius가 작으므로 기본값의 최초 발견은 시작점 기준700cm 안쪽으로 제한된다. Attack Distance는 패턴의 유효 거리와 맞춰야 한다. 예를 들어 사거리100cm 패턴만 사용하는데140cm에서 멈추면 공격 후보가 없어 대기한다. 각 공격의 거리/시야/자원/쿨다운 검사는 별도로 유지한다.

경로 요청은 부분 경로를 허용하지 않는다. 이동 실패가 누적되면 추적을 포기한다. 복귀 경로도 막히면 대기 후 재시도하며 순간이동시키지 않는다. 이동 중 목표가 바뀌어 경로를 다시 계산하더라도 정지 시간 판정은 초기화하지 않는다.

## 제작·연결
- UCombatEncounterProfile: 기획 데이터와 유효성 검사.
- UCombatEnemyAgent: 목표 관찰, 경로 이동, 복귀 및 회복 상태.
- 기존 BTTask_CombatAction: 공격 가능한 상태에서만 패턴 선택. 새 교전 시작 시 연속 사용 이력 초기화.
- tools/setup-combat-encounter.py: 별도 맵 복제, 기본 프로필, 장애물, NavMesh 생성. 기존 프로필 수치는 덮어쓰지 않음.
- tools/verify-combat-encounter.py: 저장 에셋 및 기존 시험장/플레이어 설정 읽기 전용 검증.

에디터 자동 생성에서는 자산 컴파일이 끝난 뒤 비동기 로딩용 내비게이션 잠금을 해제하고 빌드한다. 이는 지정된 시험장 생성 함수에만 적용한다. 실제 프로젝트 레벨로 확대할 때는 레벨별 NavMesh 범위와 충돌을 별도로 검증해야 한다.

## 애니메이션
새 모션은 제작하지 않았다. 슬라임 이동은 기존 AS_Slime_Move를 재사용한다. 220cm/s 이동·곡선 우회·공격 진입의 시각 품질은 별도 모션 검수 대상이며, 필요한 전달 사항은 combat-animation-backlog 문서에 추가했다.

## 검증 결과
- Development Editor 전체 빌드 성공.
- 전투 자동 테스트28/28 통과: 기존 이동/카메라·선입력·SP·피격·회피·패턴 검증과 감지/사망/시야 상실/내비 없는 경우의 제한 재시도 포함.
- 저장 에셋 검증 통과: 기존/신규 시험장의 플레이어500cm/s, 카메라 기본값, 패턴·몽타주·프로필 연결 확인.
- 실제 게임 자동 검증: 감지·접근, 장애물 우회 최대 Y268.84cm, 공격, 교전 범위 이탈에 따른 취소, 시작점 복귀 및 체력100 회복 모두 통과.
- 복귀 완료 위치 X75.259 Y31.676은 시작 위치X100 Y0에서50cm 이내.
- 실제 검증은 추적 초기에 체력을 미리 감소시킨 뒤, 이후 공격 도중 대상을 교전 범위 밖으로 이동시킨다. 피격 취소와 복귀 취소를 혼동하지 않는다.

근거: Saved/Logs/Combat-build.log, Combat-tests.log, Combat-encounter-setup.log, Combat-encounter-play.log, Combat-encounter-verify.log 및 Saved/CombatAudit/20261004/encounter-review.json.

다음 단계는 기획 데이터 묶음을 생성·검증하는 작업 흐름이다. 몬스터별 패턴/교전 프로필의 연결과 잘못된 사거리 조합 등을 에디터에서 검증하고, AI가 작성한 전투 데이터를 안전하게 반복 수정하는 기반으로 확장한다.

후속 구현: JSON 기반 생성 전 검사·새 버전 전투 에셋·전용 시험장 생성은 [AI 전투 데이터 제작 도구](2026-10-04-combat-recipe-authoring.md)에 정리했다.
