# AI 전투 데이터 제작 도구 — v1 기록

> 최신 제작은 [전투 제작실 안내](2026-10-05-combat-author-guide.md)를 사용한다. 아래는 schema_version=1 초기 CLI 방식의 기록이다. 현재는 브라우저 편집, 플레이어 스킬/궁극기, 다수 적과 플레이 조정값의 새 버전 생성이 지원된다.

## 기획자가 할 수 있는 일
JSON 한 파일로 기존 슬라임 공격의 피해·비용·속도·쿨다운, 공격 선택 조건, 감지·추적·복귀 수치를 조합하고 별도의 플레이 시험장을 생성한다. C++나 블루프린트 그래프 수정 없이 같은 유형의 두 번째 적을 시험하는 것이 이번 범위다.

생성 예제: CombatRecipes/SlimeScout_v1.json.
생성 위치: /Game/Constellation/Review/CombatRecipes/SlimeScout_v1/.
일반 공격 피해12·배속1.1, 강공격 피해22·배속0.7. 원래 슬라임과 다른 조합을 독립된 액션 데이터로 저장했다.

전용 에디터 화면, 자유로운 새 몬스터 모델 교체, 스킬/궁극기 제작, 본편 배치 도구는 아직 없다. 현재는 기존 슬라임 모델과 기존 전투 몽타주를 사용하는 JSON 제작 흐름이다.

## 사용 순서
프로젝트 루트의 PowerShell에서 실행한다. 현재 샘플 v1은 이미 생성되어 있으므로 수정 실험은 JSON을 복사하고 id를 SlimeScout_v2처럼 새 이름으로 바꾼다.

~~~powershell
# 저장 없이 자산·수치·연결 검사 및 생성 목록 확인
./tools/build-combat-recipe.ps1 -Recipe CombatRecipes/SlimeScout_v2.json

# 검사에 성공한 JSON으로 새 버전 생성
./tools/build-combat-recipe.ps1 -Recipe CombatRecipes/SlimeScout_v2.json -Apply

# 전용 시험장에서 플레이
./tools/play-combat-recipe.ps1 -Id SlimeScout_v2

# 이미 생성된 샘플
./tools/play-combat-recipe.ps1
~~~

생성기는 별도 Unreal commandlet 프로세스로 실행한다. 에디터에서 같은 자산을 수정 중이라면 먼저 저장하여 디스크의 최신 데이터를 입력으로 사용한다. 스크립트는 현재 열린 에디터의 저장되지 않은 변경을 읽을 수 없다.

Apply도 검증을 다시 수행한다. 동일 id의 폴더가 있으면 미리보기와 생성 모두 중단한다. 수정은 새 id로 만들거나 Unreal Details에서 생성 에셋을 직접 편집한다. 기존 버전·원본·맵을 자동 덮어쓰지 않는다.

결과: Saved/CombatAudit/recipe-result.json.
로그: Saved/Logs/Combat-recipe-preview.log 또는 Combat-recipe-apply.log.
오류는 actions.Light.damage처럼 수정 위치를 표시한다. 경고는 생성은 가능하지만 반복 제한 등으로 전투가 멈출 수 있는 조건을 알려준다.

## AI에 전달할 요청 예시
> CombatRecipes/SlimeScout_v1.json과 docs/2026-10-04-combat-recipe-authoring.md를 읽고, SlimeScout_v2 JSON을 작성해 줘. 가벼운 공격은 자주, 강공격은 긴 회수 뒤에 사용하도록 조절해 줘. 기존 몽타주만 참조하고 새 애니메이션을 만들지 마. 기존 id를 덮어쓰지 말고 미리보기 검사를 실행해 오류와 경고를 수정한 뒤 새 시험장을 생성해 줘. 실제 플레이에서 확인한 결과와 미확인 사항을 구분해 줘.

새 애니메이션이 필요하면 combat-animation-backlog 문서에 목적·타이밍·연결 조건을 추가한다. 이 도구는 애니메이션 자체나 타격 노티파이를 수정하지 않는다.

## JSON 규칙
필수 최상위 키는 schema_version(1), id, mesh, actions, patterns, encounter다. 알 수 없는 키는 오타로 판단하여 거부한다. 숫자 위치에 true/false를 사용하거나 NaN/무한대를 넣을 수 없다.

id는 영문자로 시작하는 영문·숫자·밑줄1~48자다. None은 사용할 수 없다. 액션/패턴 ID는 각각 대소문자를 무시해 중복 검사한다. 액션 ID Patterns와 Encounter는 자동 생성 에셋 이름이라 예약되어 있다. 패턴의 action 참조는 액션 ID 철자를 그대로 사용한다.

- mesh: 현재는 슬라임 SKM_Slime_Normal 경로. 시험장 템플릿의 모델·이동/대기 클립과 일치해야 한다.
- actions: 1~32개. id, source(기존 CombatActionDefinition의 /Game/... 패키지 경로), 선택 values 객체.
- patterns: 1~32개. id, action은 필수. 그 외 생략 시 아래 기본값.
- encounter: 빈 객체도 가능. 아래 교전 기본값을 사용한다.

### 공격 values
| 키 | 의미 | 허용 |
|---|---|---|
| damage | 타격 피해 | 0 이상 |
| stamina_cost | SP 비용 | 0~100 |
| cooldown | 재사용 대기 초 | 0 이상 |
| play_rate | 몽타주 배속 | 0.01~100 |
| reach | 전방 판정 거리 cm | 양수 |
| radius | 판정 구 반지름 cm | 양수 |

생략한 값은 source에서 복제한다. 값 상한은 일반 수치1,000,000이다. 이는 입력 오류 방지용 허용 범위이며 권장 밸런스 범위가 아니다. 배속은 1 부근에서 작은 폭으로 조절하고 플레이로 검토한다.

source는 유효한 타격창이 있는 전투 액션이어야 한다. 플레이어 콤보의 NextAction 연결이 있는 액션은 이번 몬스터 도구에서 받지 않는다. 몽타주 스켈레톤은 mesh 스켈레톤과 정확히 같아야 한다. 호환 스켈레톤 확장은 아직 지원하지 않는다.

생성 액션은 독립 복사본이지만 몽타주는 원본을 참조한다. 생성 액션의 숫자를 바꾸어도 원본 액션 숫자는 바뀌지 않는다. 공유 몽타주를 직접 편집하면 그것을 쓰는 다른 액션에도 영향을 주므로 모션 개정은 별도 버전을 만들어 연결한다.

### 패턴 기본값
min_distance=0, max_distance=180, max_angle=80, require_sight=true, weight=1, max_consecutive=1.
weight=0이면 비활성. max_consecutive=0이면 연속 사용 무제한. 활성 패턴이 하나뿐인데 반복 제한이 있으면 사용 후 무한 대기할 수 있어 경고한다.

### 교전 기본값
detect_radius=800, lose_radius=1100, leash_radius=700, attack_distance=140, move_speed=220,
think_interval=0.2, lost_sight_time=3, home_tolerance=50, retry_delay=1, retry_cooldown=3,
stuck_timeout=2, max_move_failures=3, restore_on_return=true.

거리 단위는 cm, 시간은 초다. 이동 속도220은 몬스터 전용이다. 플레이어 기본500cm/s와 카메라 값은 복제 시험장에서 유지한다.

최소 하나의 활성 패턴이 [attack_distance-20, attack_distance] 접근 정지 구간 전체를 커버해야 한다. 예를 들어140에서 정지하는데 모든 공격의 최대 거리가100이면 생성 전에 오류다. 이 검사는 후보 거리 연결을 검사하며 실제 타격 성공·전조 가독성·난이도를 보장하지 않는다. 다른 조건/자원/쿨다운 때문에 일시 대기가 발생할 수 있다.

## 생성 결과와 실패 처리
- DA_Light 등: 입력 actions별 복제 액션.
- DA_Patterns: 생성 액션만 참조하는 패턴 프로필.
- DA_Encounter: 입력 교전 설정.
- L_Preview: 기존 내비게이션 시험장을 복제하고 위 데이터를 연결한 전용 맵.

완전한 사전 검사 후 생성한다. 저장장치 오류 등 생성 도중 예외가 발생하면 생성된 경로를 결과 파일에 남기고 중단한다. 여러 패키지 저장은 원자적 트랜잭션이 아니므로 일부 출력이 남을 수 있다. 자동 삭제/덮어쓰기는 하지 않는다. 이때 오류 원인을 해결하고 새 id로 재시도한다.

보고서의 normalized는 생략된 기본값과 경고를 포함한 검토 자료이며, 원본 JSON 형식과 동일한 재입력 파일이 아니다. 반복 편집은 CombatRecipes의 원본 JSON을 기준으로 한다.

## 구현과 검증
- tools/combat_recipe.py: 엔진 밖에서도 실행 가능한 엄격한 입력 검증.
- tools/import-combat-recipe.py: Unreal 자산/스켈레톤 검사, 새 패키지 생성, 시험장 연결.
- CombatLabEditorLibrary.GetCombatAssetError: 기존 런타임 검증 규칙을 Python에 노출.
- Python 검증 테스트13개 및 기존 전투 자동 테스트28개 통과.
- 예제 실제 생성 성공. 저장 에셋을 다시 읽어 수치·패턴 참조·맵 연결과 플레이어 기본값 확인.
- 누락 source, 스켈레톤 불일치, 기존 버전 덮어쓰기를 생성 전에 차단하는 통합 시험 통과.
- 생성된 L_Preview 실제 게임 검증 통과: 추적·공격·공격 취소·복귀 회복, 장애물 우회 Y268.97cm. 모션의 시각 품질이나 최종 밸런스를 승인한 결과는 아니다.
- 원본 액션2개·패턴·교전 프로필·시험장 파일 SHA256이 생성 전후 동일함을 확인.

증거: Saved/Logs/Combat-recipe-*.log, Saved/CombatAudit/recipe-result.json, recipe-verification.json, recipe-play.json.

다음 단계에서는 이 제작 흐름에 에디터에서 선택한 전투 데이터의 검증·내보내기와 수동 변경 비교를 붙여, JSON과 에셋을 오가며 반복 수정할 때의 불일치를 줄일 수 있다.

## 2차: 에디터 수정 값 내보내기와 비교
tools/export-combat-recipe.ps1은 생성된 버전의 **디스크에 저장된** 액션·패턴·교전 프로필과 시험장 연결을 읽어 새 입력 JSON을 만든다. 에디터에서 Details 값을 변경했다면 먼저 Save All을 실행한다. 현재 도구는 선택한 에디터 객체나 저장되지 않은 실시간 값을 직접 읽지 않는다.

~~~powershell
./tools/export-combat-recipe.ps1 -Id SlimeScout_v2 -NewId SlimeScout_v3 -Baseline CombatRecipes/SlimeScout_v2.json
~~~

출력은 CombatRecipes/SlimeScout_v3.json과 Saved/CombatAudit/recipe-export-result.json이다. 같은 JSON 파일 또는 생성 버전이 이미 있으면 덮어쓰지 않고 중단한다. 다른 새 NewId를 지정해 다시 실행한다. 비교 없이 내보내려면 -Baseline ''을 지정한다.

내보낸 JSON은 바로 build-combat-recipe.ps1의 입력으로 사용할 수 있다. 모든 액션 수치를 명시하고 source는 현재 생성된 액션을 참조한다. 따라서 현재 액션이 사용하는 몽타주를 다음 버전에서도 유지한다. 이전 버전은 다음 버전의 복제 입력이므로 임의 삭제하지 않는다.

비교 보고서:
- changes: actions.Light.values.damage처럼 변경 위치, before, after를 표시한다.
- animation_reference_changes: 기준 액션과 현재 액션의 몽타주 경로 변경.
- warnings: 반복 제한 등 기존 기획 검증 경고.
- comparison_basis: 기준 값의 해석 방법.

버전 id와 복제 source 경로는 수치 변경에서 제외한다. 액션·패턴 배열은 ID로 비교하므로 배열 순서 변경은 표시하지 않는다. 실수는 Unreal의32비트 저장 정밀도로 비교하여 0.7과0.699999988 같은 직렬화 차이를 제외한다. 몽타주 내부 키프레임·노티파이 변경이나 맵 지형/카메라/캐릭터 배치의 차이는 이 도구의 비교 범위가 아니다.

기준 JSON에 액션 값이 생략되어 있으면 **지금 저장된 source 값**으로 해석한다. 최초 생성 당시 기본값의 이력을 소급 복원하지 않는다. 이후에는 모든 값이 명시된 내보내기 JSON을 기준으로 관리하면 이 모호함을 줄일 수 있다.

내보내기에서도 생성기의 사전 검증을 재사용한다. 시험장의 프로필 연결 오류, 외부 액션 참조, 스켈레톤 또는 템플릿 모델/이동 클립 불일치, 지원하지 않는 콤보 연결은 출력 전에 차단한다.

### 2차 검증
- 비교 단위 테스트6개와 기존 JSON 입력 테스트13개 통과.
- SlimeScout_v1을 JSON으로 내보내 SlimeScout_v2 에셋·시험장을 생성했고, 저장 수치와 패턴을 다시 읽어 차이0건 확인.
- 에디터 메모리에서 Light 피해를12→15로 변경했을 때 정확히 해당 항목1건만 감지. 원본에는 저장하지 않고 복구.
- 기존 버전/JSON 보존 및 생성기 호환성 검사 강제 실행을 통합 검증.
- 이번 변경은 제작용 Python/PowerShell에 한정하며 전투 런타임 C++ 변경은 없음.

검증 기록: Saved/Logs/Combat-recipe-export-verify.log, Saved/CombatAudit/recipe-export-verification.json.

현재 납품 상태: v1·v2 에셋/시험장과 다음 편집용 CombatRecipes/SlimeScout_v3.json이 준비되어 있다. 위 내보내기 예시를 새로 실행할 때는 아직 존재하지 않는 NewId(예: SlimeScout_v4)를 사용한다. v3는 JSON만 준비했으며 생성기는 아직 적용하지 않았다.

## 3차: 선택 몬스터의 저장 전 설정 검사
언리얼 에디터의 레벨 뷰포트 또는 World Outliner에서 전투 시험장의 몬스터 하나를 선택하고 **Tools → Combat · 선택 몬스터 검사**를 실행한다. 결과 창에 오류와 참고 사항이 함께 표시되며 Output Log에도 COMBAT_AUTHORING_VALIDATION으로 남는다.

검사 대상은 Training Enemy가 켜진 CombatLabCharacter다. 본편의 기존 다른 몬스터 BP를 자동 변환하거나 검사하는 기능은 아니다. 여러 액터를 선택했거나 플레이어를 선택했다면 대상 안내가 나온다. PIE 실행 중에는 메뉴가 비활성화된다.

검사 범위:
- Encounter Profile / Pattern Profile 누락 및 유효성.
- 활성 공격 패턴, 접근 정지 거리와 공격 거리의 연결.
- 각 공격의 몽타주·타격창 검증, 메시와의 스켈레톤 일치.
- 현재 최대 SP100으로 사용할 수 없는 공격 비용.
- 이번 제작 도구가 지원하지 않는 NextAction 콤보 연결.
- 대기/이동 애니메이션 누락·스켈레톤 불일치와 이동 모션 기준 속도.
- 유일한 패턴의 연속 사용 제한으로 생길 수 있는 대기 경고.

이 메뉴는 **현재 메모리의 저장 전 변경**도 검사한다. 자동 저장이나 값 수정은 하지 않는다. 검사 후 저장하고 기존 내보내기 도구를 실행하면 JSON에도 해당 변경을 반영할 수 있다. 경로 이동·타격 성공·전투 감각은 실제 플레이 검증이 별도로 필요하다.

JSON 생성/내보내기 메뉴까지 통합한 제작 창은 아직 없으며, 이번 메뉴는 선택 몬스터 데이터 검사에 한정한다.

### 3차 검증 결과
- 최신 CombatEditor 모듈 컴파일·링크 완료.
- 최신 DLL로 전투 자동 테스트29/29 통과. Tools 메뉴 항목 등록, 정상 설정, 잘못된 사거리/비용, 비활성 패턴, 스켈레톤 불일치, 플레이어/빈 선택, 여러 공격의 동시 오류 수집을 확인했다.
- 기존 JSON 입력·비교 테스트19/19 통과.
- 메뉴 클릭과 결과 창의 실제 화면 배치는 수동 검수하지 않았다.
- 최종 전체 프로젝트 빌드는 동시 작업 중인 SceneDirectorSchoolMigration.cpp의 델리게이트 호출 컴파일 오류로 미통과. 전투 모듈 링크 후 -SkipBuild로 최신 전투 테스트를 실행했다. 다른 작업의 소스는 수정하지 않았다.

근거: Saved/Logs/Combat-build.log, Combat-tests.log.

## 4차: AI 전달용 검사 보고서 저장
선택 몬스터의 문제를 AI에 전달하려면 **Tools → Combat · 검사 보고서 저장**을 실행한다. 메뉴는 현재 선택한 CombatLabCharacter 몬스터 하나의 메모리 상태를 읽는다. 저장 전 수치 변경도 포함하며 자산을 자동 저장하거나 수정하지 않는다. PIE에서는 비활성화된다.

보고서는 Saved/CombatAudit/CharacterReports/Combat-<고유 ID>.json에 저장한다. 메뉴 결과 창과 Output Log의 COMBAT_REPORT에서 경로를 확인할 수 있다. 기존 보고서는 덮어쓰지 않는다. 파일은 로컬에만 저장되며 다른 AI나 서비스에 자동 전송하지 않는다.

포함 정보:
- 검사 시각(UTC), 액터 라벨·경로, 검사 통과 여부(valid).
- 오류·참고 사항 전체 목록.
- 메시·대기/이동 애니메이션·프로필·공격·몽타주 경로와 각 패키지의 미저장 변경 표시(package_dirty).
- 교전 설정, 패턴별 거리·각도·가중치·연속 제한과 공격 수치/입력창.
- 유효하지 않은 NaN/Infinity 값은 명시적인 문자열로 기록하여 JSON 파일 자체는 읽을 수 있게 유지.

보고서 저장 성공은 전투 설정이 정상이라는 뜻이 아니다. 잘못된 설정도 valid=false와 errors에 기록하여 AI가 원인을 확인하도록 한다. 액터가 선택되지 않았거나 플레이어를 선택했다면 파일을 쓰지 않고 안내한다.

AI 요청 예시:
> 이 검사 보고서의 errors를 읽고 해당 몬스터 설정을 수정해 줘. 보고서는 저장 전 에디터 값일 수 있으므로 실제 자산과 먼저 대조해 줘. 기존 전투 의도를 보존하고, 필요한 애니메이션은 새로 제작하지 말고 전달 목록에 기록해 줘. 수정 후 동일 몬스터를 다시 검사해 결과를 알려줘.

이 파일은 진단 보고서이며 제작 입력 JSON이 아니다. build-combat-recipe.ps1에 직접 넣지 않는다. 몽타주 내부 키프레임/노티파이 전체나 경로 이동·게임플레이 결과를 기록하는 기능도 아니다.

이전 3차 기록의 전체 빌드 제한은 이번 단계에서 해소되었다. 검증은 최신 로그 기준으로 아래 결과를 확인한다.

### 4차 검증 결과
- Development Editor 전체 빌드 성공. 이전 연출 모듈로 인한 빌드 제한 해소.
- 전투 자동 테스트30/30, JSON 입력·비교 테스트19/19 통과.
- 보고서 메뉴 등록, 잘못된 설정의 저장, 저장 전 수치 포착, 반복 저장 시 경로 분리, 빈 선택 거부, 라벨 특수문자 및 NaN 직렬화 검증.
- 실제 SlimeScout_v2 시험장에서 보고서 저장 후 JSON 재독해 성공: valid=true, 패턴2개, 몬스터 이동속도220, 생성 버전 내부 액션 참조 확인.
- 메뉴 결과 창의 실제 화면 배치는 수동 검수하지 않았다.

근거: Saved/Logs/Combat-build.log, Combat-tests.log, Combat-character-report-verify.log, Saved/CombatAudit/character-report-verification.json.

## 5차: 제작한 몬스터의 자동 플레이 검사
JSON 생성과 데이터 검사를 마친 뒤 아래 명령으로 표준 시험장의 실제 게임을 자동 실행한다.

~~~powershell
./tools/test-combat-recipe-play.ps1 -Id SlimeScout_v2
~~~

실행마다 Saved/CombatAudit/PlayRuns/<실행 ID>/에 result.json, game.log, console.log, stderr.log를 만든다. 이전 실행의 성공 파일을 재사용하지 않으며 해당 프로세스의 로그에서 결과가 정확히1개인지 확인한다. 정상 종료만으로 성공 처리하지 않고 세부 검사 값과 장애물 우회 거리도 확인한다. 실패한 명령은 오류 종료하고 보고서 경로를 출력한다.

현재 표준 시나리오:
1. 시작점에서 플레이어를 발견하고 추적.
2. 낮은 장애물을 옆으로 우회(최대 Y 이동200cm 초과).
3. 몬스터의 공격 시작 확인.
4. 플레이어를 시작점+850cm로 옮겨 교전 이탈 유도.
5. 공격 취소, 시작점50cm 이내 복귀, HP100 회복 확인.

시나리오는 추적 초기에 몬스터에게 피해10을 주어 회복도 검사한다. 플레이어 입력 전체나 실제 공격 명중을 시험하는 시나리오는 아니다. 기존 -CombatEncounterReview 구현을 그대로 사용하며18게임초 안에 관찰한 결과를 기록한다. -TimeoutSeconds는 프로세스 전체의 실제 시간 제한(기본180초)이며 시나리오18초를 늘리는 옵션이 아니다. 시간 초과 시 이 도구가 시작한 검사 프로세스만 종료한다.

**적용 범위:** 현재 생성기의 기본 장애물·배치와 기본 감지/교전 범위를 유지한 슬라임 시험장 회귀 검사다. 감지 거리를 시작 거리보다 줄이거나, LeashRadius를850 이상으로 늘리거나, HomeTolerance를50보다 크게 설정하거나, RestoreOnReturn을 끄거나, 이동/공격을 지나치게 느리게 만들면 유효한 기획도 이 표준 시나리오에서는 실패할 수 있다. failure는 자동으로 버그 판정을 내린 결과가 아니라 시나리오의 미완료 항목이다. 그런 설정은 별도 시나리오 또는 수동 플레이로 검증한다.

결과 읽기:
- chased: 추적 상태를 관찰했는지.
- attacked: 공격 시작을 관찰했는지.
- return_cancelled_action: 복귀 중 공격이 종료된 상태였는지.
- returned_and_restored: 시작점 복귀와 체력 회복을 관찰했는지.
- detour_y: 장애물 우회 시 최대 Y 좌표 크기.
- failure: 결과 누락/중복, 비정상 종료, 치명적 로그, 미완료 단계 등.
- run_id, recipe_id, map, started_utc, finished_utc, log: 재현 대상과 실행 근거.

검증 결과: 판정 회귀 테스트10개 통과. SlimeScout_v2 실제 게임에서 추적·우회·공격 시작·복귀 및 회복 모두 통과, detour_y=269.53cm. 전투 런타임은 변경하지 않았다.

## 6차: 프로필을 따르는 플레이 검사
자동 플레이의 장애물·초기 배치는 유지하되 이탈/복귀 판정을 몬스터의 실제 Encounter Profile에 맞추었다.

- 플레이어 이탈 위치: 몬스터 시작점 + LeashRadius + max(300cm, HomeTolerance×2).
- 복귀 완료 오차: HomeTolerance.
- RestoreOnReturn=true: HP100 회복 확인.
- RestoreOnReturn=false: 검사에서 피해10을 받은 뒤의 HP가 복귀 후 유지되는지 확인.
- 공격 취소: 같은 실행 ID의 실제 Cancelled 이벤트가 Returning 상태에서 발생해야 통과한다. 자연 종료를 취소로 취급하지 않는다.
- 이탈 직후 시험용 플레이어 이동을 멈춰 작은 시험장 바깥에서 낙하하지 않게 한다. 이 동작은 자동 검사 플래그를 켠 경우에만 실행한다.

느린 몬스터는 게임 내 관찰 시간을 늘려 실행할 수 있다.

~~~powershell
./tools/test-combat-recipe-play.ps1 -Id SlimeScout_ProfileReview -ScenarioSeconds 30 -TimeoutSeconds 180
~~~

ScenarioSeconds는5~120게임초(기본18), TimeoutSeconds는 프로세스 시작부터의 실제 시간 제한이다. 로딩 시간과 낮은 프레임 속도를 고려해 실제 시간 제한을 충분히 둔다.

결과 schema_version=2:
- returned: 복귀 완료.
- recovery_policy_matched: 프로필에 따른 회복 또는 체력 유지 일치.
- scenario_valid / scenario_reason: 시작 배치가 이 시나리오에 맞는지와 맞지 않는 이유.
- exit_distance, home_tolerance, restore_on_return, expected_health, actual_health, scenario_seconds: 판정에 사용한 값.
- chased, attacked, return_cancelled_action, detour_y: 기존 관찰 항목.

기존 returned_and_restored 필드는 새 결과에서 사용하지 않는다. 판정 함수는 과거 로그를 읽을 수 있지만 현재 실행기는 schema2를 요구하여 오래된 DLL 결과가 통과하지 않도록 한다. 코드 변경 후에는 에디터 빌드를 갱신해야 한다.

**남은 범위 제한:** 시작점의 대상이 감지/교전 거리 안에 있고 공격 거리 밖에 있어야 한다. 적은 한 마리여야 하며 기본 장애물과 NavMesh 배치를 전제로 한다. 감지 범위에 맞춰 시험장 지형·시작 위치를 자동 재배치하지 않는다. 모든 공격의 명중·피격 품질이나 임의 맵을 보장하는 검사는 아니다.

추가 시험 자산 SlimeScout_ProfileReview: LeashRadius950, HomeTolerance90, RestoreOnReturn=false, MoveSpeed160. 기존 고정 시나리오에서 실패를 재현한 뒤 검사 개선에 사용한다. 기존 v1/v2 설정은 보존한다.

### 6차 최종 검증 결과 — 패키징 종료 후 재개 완료
이전 작업에서는 학교 맵 패키징이 CombatRuntime DLL을 사용하여 링크가 보류되었다. 패키징 종료 후 새 DLL 빌드와 실행 검증을 완료했다.

- Development Editor 전체 빌드 성공, 전투 자동 테스트30/30 통과.
- 결과 판정 테스트15/15 통과. 이전 JSON 입력·비교19개 통과 기록은 유지되며 이번 재개 작업에서는 해당 도구를 수정하지 않았다.
- 기본 프로필과 변경 프로필 모두 실제 게임에서 추적·장애물 우회·공격 시작·동일 실행의 실제 취소·복귀·회복 정책 일치 통과.

| 시험 버전 | 관찰 시간 | 이탈 거리 | 복귀 오차 | 회복 정책 | 실제 복귀 후 HP | 우회 Y |
|---|---:|---:|---:|---|---:|---:|
| SlimeScout_v2 | 18초 | 1,000cm | 50cm | HP100 회복 | 100 | 269.02cm |
| SlimeScout_ProfileReview | 30초 | 1,250cm | 90cm | 피해 후 HP 유지 | 90 | 267.18cm |

변경 프로필의 기존 고정 시나리오 실패 기록은 Saved/CombatAudit/PlayRuns/8043dfbbf3134d3e9586b81f4bce059b/result.json에 남아 있다. 수정 후 성공 결과:
- 기본: Saved/CombatAudit/PlayRuns/4ad48a1183fc45d7a951ca0f49c82622/result.json.
- 변경: Saved/CombatAudit/PlayRuns/0c8bdff4e9ef492097e06d9427ef017e/result.json.

빌드/회귀 근거: Saved/Logs/Combat-build.log, Combat-tests.log. 이 결과는 위 두 시험장의 자동 교전 검증이며, 앞서 명시한 초기 배치·단일 몬스터·장애물 시나리오 범위 제한은 유지한다.

## 2026-10-05: Windows PowerShell 5.1 종료 코드 오판 수정
모든 테스트가 성공했는데 “Missing successful tests:” 뒤에 이름 없이 실패하던 문제를 수정했다. 원래 로그에는30개 성공 및 엔진 종료 상태0이 기록되어 있었지만, Windows PowerShell 5.1의 Start-Process/리디렉션 조합에서 ExitCode가 null로 읽혔다.

tools/combat-process.ps1에서 대기 전에 프로세스 핸들을 확보하고 종료 코드를 읽도록 공통 처리했다. null을 성공으로 취급하지 않으며, 테스트 실패/치명적 로그 검사도 유지한다. test-combat.ps1과 test-combat-recipe-play.ps1에 적용했다.

검증:
- 기존 방식: Windows PowerShell5.1에서 정상 종료 프로세스의 ExitCode=null 재현.
- 수정 방식: Windows PowerShell5.1 및 PowerShell7 각각 종료0·종료7·시간 초과 회귀3개 통과.
- Windows PowerShell5.1에서 실제 전투30개 및 플레이 결과 판정15개 통과.
- 전투 런타임 C++ 변경 없음. PowerShell 업그레이드 없이 기존 명령을 사용할 수 있다.
- Windows PowerShell5.1에서 SlimeScout_v2 실제 자동 플레이 통과. 결과: Saved/CombatAudit/PlayRuns/acf706250de249849404175ae59ba003/result.json.

## 2026-10-05: 인게임 전투 워크벤치
사용법: docs/2026-10-05-combat-workbench.md.
프로젝트 루트 Play-Combat.cmd 더블클릭 → F1 조정 → 적용 후 전투 재시작.
HP/SP 상한, 이동·회피·공격·몬스터 교전/패턴 수치를 런타임 복사본에서 조정한다.
원본 자산은 유지하며 프리셋은 Saved/CombatTuning에 별도 저장한다.
