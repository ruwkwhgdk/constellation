# 몬스터 도넛 전조 VFX 인계

작성: 2026-10-27 · 작성 담당: VFX 채팅 · 상태: **표현/API 구현. 기존 자동 검사 28개 통과(15개 경고 포함). 검정 고리의 재질 연결 수정 완료. 저장본 그래프 검사 통과, 본 게임 재검사 화면에서 노랑/빨강 확인.**

이 문서는 VFX 담당이 유지하며 ‘플레이어 공격 시스템 구현’ 담당은 읽기 참조합니다. 기준은 `docs/superpowers/specs/2026-10-26-light-heavy-attack-design.md` 15절입니다.

## 확정 표현과 후보 구분

준비는 노란색, 실행은 붉은색이며 가운데가 비어 있는 원형 고리입니다. 색은 같은 공격의 단계이고 가드 가능 여부나 퍼펙트 성공을 의미하지 않습니다. 기존 궤적·명중·피격 효과를 대체하지 않습니다.

부착 위치, 카메라 지향, 맥동, 발광 변화와 아래 수치는 **시각 검수 후보**입니다. 참고 이미지의 십자 광선·전면 화면 발광은 구현하지 않았습니다. 고리의 중심은 투명도 트릭이 아니라 삼각형이 없는 구멍입니다. 깊이 검사를 사용하며 벽 뒤의 적을 강제로 보여주지 않습니다. 주목·피해·가드·패링 판정은 이 컴포넌트에 없습니다.

## 자산과 코드

- 재질: `/Game/Constellation/VFX/Telegraph/M_MonsterTelegraph.M_MonsterTelegraph`.
- 표현 컴포넌트: `/Script/ConstellationVFX.ConstellationMonsterTelegraphComponent` (`UConstellationMonsterTelegraphComponent`).
- 헤더: `Plugins/ConstellationVFX/Source/ConstellationVFX/Public/ConstellationMonsterTelegraphComponent.h`.
- 재질 원본 생성 스크립트: 형제 Art 저장소 `ArtSource/VFX/MonsterTelegraph/create_material.py`. 새 자산을 한 번 생성하며 기존 자산은 덮어쓰지 않습니다.
- 고리: 반지름/두께에 따라 생성되는 96분할 절차적 메시. 기본 388 정점, 576 삼각형. 중앙 면 없음. 별도 텍스처·Niagara 의존 없음.
- 재질은 Unlit/Opaque/Two-sided. `PhaseColor` (Vector), `Brightness` (Scalar)를 사용합니다. 컴포넌트가 노랑/빨강 의미를 유지하도록 값을 관리합니다. 재질 직접 조작 대신 아래 API를 사용합니다.

## 실제 API 계약

`EMonsterTelegraphPhase` (Blueprint enum): `Hidden`, `Preparation`, `Execution`.

| 함수 | 반환 | 의미 |
|---|---|---|
| `Configure(const FMonsterTelegraphSettings& NewSettings)` | bool | 전체 설정을 원자적으로 적용. 유효하지 않으면 false, 이전 설정 유지 |
| `SetAnchor(USceneComponent* Target, FName Socket, FVector LocalOffset)` | bool | 같은 소유자의 컴포넌트/소켓에 부착. 소켓 없음, 다른 소유자, 순환 부착, 비정상 좌표는 거절 |
| `BeginTelegraph(int64 AttackId)` | bool | 새 실행의 노란 준비 시작. 이전 표시를 대체 |
| `SetPhase(int64 AttackId, EMonsterTelegraphPhase NewPhase)` | bool | 현재 실행만 변경. Preparation→Execution, 또는 Hidden으로 종료 |
| `StopTelegraph(int64 AttackId)` | bool | 현재 실행과 일치할 때 즉시 숨김. 잔상 종료 없음 |
| `StopAllTelegraphs()` | void | 사망·그로기·재시작·전체 취소 등에서 무조건 숨기고 tick 중지 |
| `GetPhase()` / `GetAttackId()` / `IsShowingTelegraph()` | enum / int64 / bool | 현재 표현 상태 조회 |

**실행 ID:** 0은 무효입니다. 이 컴포넌트의 생존 기간 동안 증가하는 양의 `int64` 값을 사용합니다. 같은 활성 ID의 Begin은 멱등이며 실행을 노랑으로 되돌리거나 발광을 재시작하지 않습니다. 중단된 ID 및 그보다 오래된 ID는 다시 시작할 수 없습니다. StopAll도 마지막 ID를 보존합니다. 재시작 때 게임 전투 ID가 1로 초기화된다면 별도의 증가하는 VFX serial을 사용하거나 컴포넌트를 재생성하세요. 오래된 SetPhase/Stop은 false를 반환하여 다음 공격을 건드리지 않습니다.

실행→준비 역전환은 거절합니다. 연속 공격의 다음 준비는 새로운 ID로 시작해야 합니다. 무엇을 새로운 공격 실행으로 볼지는 연동 담당의 실제 패턴 단계 기준으로 결정합니다.

외부 전환이 없으면 노란 준비는 시간이 지나도 그대로입니다. 붉은 실행도 종료 호출까지 유지됩니다. 맥동/짧은 밝기 변화는 표시만 바꾸고 단계·피해·공격 시간을 변경하지 않습니다. 게임 pause/배속은 컴포넌트가 받는 게임 delta를 따릅니다.

## 설정 타입과 기본값

`FMonsterTelegraphSettings`는 BlueprintType 구조체이며 컴포넌트의 `Settings`에서 확인하고 `Configure`로 런타임 변경합니다.

| 실제 필드 | 타입 | 기본값 | 허용 범위 / 의미 |
|---|---|---:|---|
| Radius | float | 60 | 4–500cm. 고리 밴드 중심 반지름 |
| Thickness | float | 8 | 1–Radius×0.8cm. 안쪽 구멍은 항상 남음 |
| OutlineWidth | float | 1.5 | 0–Thickness×0.35cm. 안팎 어두운 테두리 폭 |
| Brightness | float | 1 | 0.1–4. 고리 발광 배율 |
| bFaceCamera | bool | true | 첫 로컬 플레이어 카메라를 향하는 후보 방향 |
| CameraOffset | float | 20 | -100–100cm. 카메라 지향일 때 부착점에서 카메라 쪽으로 이동 |
| PreparationPulseAmount | float | 0.06 | 0–0.15. 준비 상태의 크기 맥동 비율. 0이면 비활성 |
| PreparationPulseHz | float | 1.2 | 0–4Hz. 0이면 맥동 없음 |
| ExecutionFlashBoost | float | 0.25 | 0–1. 실행 진입 순간의 추가 밝기. 0이면 비활성 |
| ExecutionFlashDuration | float | 0.12 | 0–1초. 추가 밝기가 기본 밝기로 복귀하는 시간. 단계 종료 시간이 아님 |

모든 float는 NaN/Infinity를 거절합니다. 크기는 소유자 스케일에 중복 곱하지 않는 월드 cm 기준이며 맥동이 추가 적용됩니다. `bFaceCamera=false`이면 컴포넌트 방향을 따르는 XY 평면 고리(법선 local Z)이고 CameraOffset은 적용하지 않습니다. 부착 위치·고정 방향은 기존 SceneComponent 상대 변환으로도 편집할 수 있습니다.

현재 색상 값(Linear): Preparation `(1,.82,.01,1)`, Execution `(1,.012,.004,1)`. 색 의미는 확정이나 구체 RGB/밝기는 시각 검수 대상입니다.

## 연동 예시와 정리

```cpp
auto* Cue = NewObject<UConstellationMonsterTelegraphComponent>(Enemy);
Enemy->AddInstanceComponent(Cue);
Cue->RegisterComponent();
Cue->SetAnchor(EnemyMesh, NAME_None, FVector(0, 0, 45)); // 후보 위치, 적별 검수
Cue->Configure(Profile);
const int64 VisualId = ++EnemyVisualSerial;
Cue->BeginTelegraph(VisualId); // 실제 준비 진입
// 실제 실행 진입 이벤트에서만:
Cue->SetPhase(VisualId, EMonsterTelegraphPhase::Execution);
// 실행 종료/회수/해당 공격 취소:
Cue->StopTelegraph(VisualId);
// 사망/그로기/전체 리셋:
Cue->StopAllTelegraphs();
```

각 bool 반환을 확인해 누락 자산·유효하지 않은 프로필·소켓·ID를 연결 검증에서 보고해 주세요. 피격이 실제 공격을 중단한 경우만 Stop을 호출합니다. 피격 후에도 공격이 유지된다면 현재 단계를 유지합니다. 준비 취소는 Stop만 호출하며 붉은 실행을 거치지 않습니다. 일반 종료, 취소, 제거를 색 전환용 독립 고정 타이머로 대체하지 마세요.

이펙트가 표시되는 것과 실제 타격창/접촉 시점은 별개입니다. 실행 진입 이벤트에 SetPhase를, 판정은 기존 전투 시스템에 둡니다. 붉은 표시가 퍼펙트/패링 기회를 부여하지 않습니다. 전조 프로필을 실제 액션 데이터/제작 도구에 저장하고 미지정을 검증하는 연결은 연동 담당 범위입니다.

## 미리보기와 검증 상태

기존 L_VFXGallery에서 `-game -MonsterTelegraphReview`로 별도 시각 검토를 실행합니다. `-MonsterTelegraphCapture` 추가 시 비교 6장을 저장하고 **검증 프로세스 자체를 종료**합니다. 반드시 별도의 UE 프로세스에서 사용하며 두 캐시 방지 플래그를 포함합니다. 일반 갤러리와 저장된 맵은 변경하지 않습니다.

미리보기는 기존 SKM_Slime_Liquid와 AS_Slime_Attack을 그대로 재생합니다. 준비/실행은 비교용 드라이버가 명시적으로 호출합니다. 드라이버의 고정 비교 시간은 실제 공격 단계 연결이나 전조 컴포넌트의 자동 전환 기능이 아닙니다.

- 재질 생성 완료.
- RED: 새 테스트 2개가 고리/상태 미구현으로 실패 확인.
- GREEN: 독립 Editor Development 빌드 성공, 신규 테스트 2개 경고 없이 통과.
- 밝은/어두운 배경, 거리, 다수 적의 비교용 실제 렌더링: 아래 20261027-045309 결과 6장 확인. 실전 배치/가독성 최종 승인은 별도.
- 본 게임/CombatRuntime 연결 검증은 아래 연동 담당의 최신 기록을 참조합니다. 30/60 FPS 직접 가드·퍼펙트 조작, 최종 외형 승인, Shipping/Cook는 미검증입니다.
- 이번 작업에서 기존 전투 코어/BP 단계 연결, 기존 효과, 애니메이션 자산, 전투 UI는 수정하지 않습니다.

## 2026-10-27 검정 고리 수정

연동 담당이 제공한 `Saved/CombatExpansion/20261027-Telegraph/RenderPIE/Saved/yellow.png`, `red.png`에서 단계와 API 반환은 정상이지만 고리가 검게 렌더링되는 결함을 확인했습니다.

원인: 생성 스크립트가 VertexColor 출력 이름을 `RGB`로 지정했습니다. UE 5.8의 해당 표현식 첫 출력은 이름 없는 RGB 출력이고, MaterialEditingLibrary의 이름 탐색은 이를 `RGB`로 찾지 못합니다. 연결 반환값도 검사하지 않아 tint Multiply의 A 입력이 비어 있었습니다. 기본 A=0 때문에 PhaseColor/Brightness를 바꾸어도 최종 Emissive가 0이었습니다. `material-inspect.log`에서 실제 저장 그래프의 `[None, MaterialExpressionVectorParameter_0]`를 확인했습니다.

이번 수정 파일:
- 게임 저장소 `Content/Constellation/VFX/Telegraph/M_MonsterTelegraph.uasset`: 기존 VertexColor 노드의 이름 없는 첫 출력을 tint Multiply A에 연결하여 저장. 다른 노드 및 색상/발광 수치는 유지.
- 형제 Art 저장소 `ArtSource/VFX/MonsterTelegraph/create_material.py`: 출력명을 빈 문자열로 수정. 모든 그래프 연결 반환값을 assert하여 실패 시 저장 전 중단.
- 형제 Art 저장소 `ArtSource/VFX/MonsterTelegraph/validate_material.py`: 저장 재질의 VertexColor × PhaseColor × Brightness → Emissive 연결과 Unlit 설정을 읽기 전용 검사.

C++ 컴포넌트, 본 게임·시험장 공격 단계 연결, Blueprint, 애니메이션은 이번 색상 버그 수정에서 변경하지 않았습니다. 수정 전 자산은 `Saved/CombatExpansion/vfx1/M_MonsterTelegraph-before-color-fix.uasset`에 보존했습니다. 진단 및 수선 로그: `material-inspect.log`, `material-repair.log` (같은 vfx1 폴더). 수선 전 실제 누락 입력을 assert로 확인했고, 수선 후 연결 노드 일치 검사와 저장이 성공했습니다.

기존 C++ 검증 기록 보완: `telegraph-final-report/index.json`의 합계는 28개(13 성공, 15 경고 포함 성공), 실패/미실행 0입니다. 전조 lifecycle, hollow geometry, attachment/reregister, CombatRuntime에서의 exported profile 연결 검사를 포함합니다. 이 수치 검사는 화면 색상 검증을 대체하지 못했으므로 별도 재질 그래프 검사와 실제 렌더링으로 보강합니다. 이 보고서는 해당 과거 실행 기록이며 이번 재질 수정 후 C++ 테스트 재실행을 뜻하지 않습니다.

### 저장본 재검증 및 본 게임 결과

- 별도 프로세스 재로드 그래프 검사 통과: `Saved/CombatExpansion/vfx1/material-verify-reload.log`의 `TELEGRAPH_MATERIAL_GRAPH_PASS`.
- 연동 담당의 수정 후 본 게임 캡처 `Saved/CombatExpansion/20261027-Telegraph/FinalRenderPIE/Saved/yellow.png`, `red.png`를 VFX 담당도 직접 열어 노란 준비 고리와 붉은 실행 고리, 빈 중심을 확인했습니다. 동일 폴더 `telegraph-pie.json`의 passed=true도 확인했습니다.
- 이 캡처는 한시적으로 `r.MorphTarget.Enable 0` 조건입니다. 기본 morph 활성 조건의 전체 캐릭터 외형 검증으로 확대 해석하지 않습니다.
- 연동 담당 보고: 원본 build5 성공, FinalAutomationReport 96/96 성공, MainPIE/LabPIE/UIOriginal 통과. 상세 범위와 원본 증거는 `docs/2026-10-27-monster-telegraph-integration.md`에서 관리합니다. 이번 VFX 담당이 이 전체 시험을 직접 재실행한 것은 아닙니다.
- 위치/밝기는 여전히 후보입니다. 본 게임에서 고리는 슬라임 소유이나 겹친 화면에서는 플레이어 소유처럼 보일 수 있고, 실행 자세에 따라 머리 위에 떠 보입니다. 색상 버그 수정과 최종 배치/가독성 승인은 구분합니다. 다수 적 실전 가독성 및 30/60 FPS 직접 가드 검수는 남아 있습니다.

### 비교용 갤러리 렌더 검증 완료

- 최종 결과: `Saved/CombatExpansion/vfx1/Saved/MonsterTelegraph/20261027-045309/`의 6장 모두 직접 확인. 밝은 근거리 준비/실행, 어두운 원거리 준비/실행, 밝은/어두운 배경의 3개 독립 고리에서 노랑·빨강과 빈 중심이 표시됩니다. `telegraph-color-render-compiled.log`, 프로세스 종료 코드 0.
- 기존 `AS_Slime_Attack`을 `SKM_Slime_Liquid`에서 재생한 비교 장면입니다. 캡처 로그에 animation_position 기록이 있지만 정지 이미지 6장으로 전체 동작·손상 없는 리타기팅·공격 단계 동기화를 합격 처리하지 않습니다. 고리의 높은 위치와 낮은 노출에서 어두운 빨강은 배치/밝기 후속 검수 사항입니다.
- 처음 NullRHI에서 수정·저장한 뒤 standalone 비교 화면에서는 회색 대체 셰이더가 보였습니다(`20261027-044941/`, 보존). RHI 활성 편집기로 동일 그래프를 재컴파일·저장한 뒤 재실행하니 정상 색상이 나왔습니다. `material-rhi-compile.log`에 그래프 검사 통과 및 컴파일 오류 없음/저장 성공 기록이 있습니다.
- 생성 스크립트는 신규 생성 시 NullRHI를 거절하고, recompile_material 오류 반환값도 검사하도록 보강했습니다. 읽기 전용 그래프 검사는 NullRHI에서도 가능합니다. 자산 제작/수선 완료 판정에는 실제 RHI 컴파일과 저장본 렌더 검사를 함께 사용합니다.
- 최종 재질 SHA256: `1DC47497553A7EAAAD10D303828723FE0BA18F9DD11FE117BEA93CB6CB5908BE`.
- 이번 버그 수정에서 커밋/푸시는 수행하지 않았습니다.
