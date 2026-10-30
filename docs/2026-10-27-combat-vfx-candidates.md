# 최신 전투 VFX 후보 제작·연결 기록

2026-10-27. 이번 기록은 10월 5/6일 작업의 커밋 확인과 별개인 신규 제작 기록입니다. 기준은 `docs/superpowers/specs/2026-10-26-light-heavy-attack-design.md`입니다. **색·폭·밝기·잔상은 미승인 후보**이며, 승인된 모션의 타격창·게임 규칙·수치 밸런스는 변경하지 않습니다.

## 제작 결과와 재사용 재료

| 항목 | 이번 제공 | 연결 상태 |
|---|---|---|
| 약1/2/3 | Light1/Light2/Light3 프로필 | CombatVFXComponent 후보 선택 + 명시적 액션 맵 |
| 강1/2 | Heavy1/Heavy2 프로필 | 종류 기본값 Heavy1, 강2는 명시적으로 매핑 |
| 약/강 독립 패링 공격 | LightParry/HeavyParry 프로필 | 액션 AttackKind로 선택. 퍼펙트 성공과 별개 |
| 확정 명중·슬라임/플레이어 피격 | 기존 SwordHit/SlimeHit/PlayerHit 재사용 | 기존 확정 피해 경로 유지 |
| 일반 가드/퍼펙트 성공 | 단일 접촉 결과 API, SwordBlock/SwordParry 재사용 | 권위 있는 판정 결과에서 호출 필요 |
| 그로기 진입/유지/해제 | GroggyEnter/GroggyHold/GroggyExit 신규 | 공통 컴포넌트 API 제공, 본 게임/ASC 상태 연결 필요 |
| 슬라임 공격 | 기존 전방 gel fan 재사용 | 기존 타격창 경로 유지. 모델·모션 수정 없음 |

자산은 `/Game/Constellation/VFX/Materials/M_FX_SwordRibbon`, `M_FX_Impact`, `M_FX_ImpactStar`, `M_FX_Cut`, `M_FX_GelImpact`, `M_FX_Glow`, `M_FX_Soft`와 엔진 기본 Sphere/Plane을 재사용합니다. 새 외부 리소스나 신규 uasset은 없습니다. 생성 원본은 이번 C++ 프로필과 절차적 효과 코드입니다. 기존 enum 0–12는 보존하고 그로기 3종을 뒤에 추가했습니다.

| 프로필 | 폭 cm | 잔상 초 | 밝기 배율 |
|---|---:|---:|---:|
| Light1 | 24 | .18 | 1.7 |
| Light2 | 26 | .17 | 1.7 |
| Light3 | 30 | .20 | 1.85 |
| Heavy1 | 38 | .24 | 1.9 |
| Heavy2 | 44 | .28 | 2.0 |
| LightParry | 28 | .12 | 2.2 |
| HeavyParry | 46 | .26 | 2.1 |

잔상은 이미 지나간 검끝 샘플의 표시 시간이며 타격창 시간이 아닙니다. 움직임은 실제 무기 위치에서 얻습니다. 그로기 유지는 6개 입자를 재사용하며 tick마다 새 입자·액터를 만들지 않습니다. 진입은 바깥으로 터지는 파편, 유지는 느린 부유, 해제는 짧게 흩어지는 파편입니다. 별도 게이지·아이콘·UI는 없습니다.

## 호출 계약

### 공격 궤적

기존 CombatRuntime의 `UCombatVFXComponent`에 `bUseCandidateTrails=true`를 설정하면 기존 Default 공격 궤적에만 후보를 적용합니다. 캐릭터 AttackCue가 Disabled/Builtin/Niagara이면 기존 우선순위가 그대로 적용됩니다. `ActionTrailProfiles`에 실제 UCombatActionDefinition 포인터를 키로 약1/2/3, 강1/2를 각각 지정합니다. 타수를 입력 횟수나 이름으로 추측하지 않습니다. 매핑이 없으면 Heavy는 Heavy1, LightParry/HeavyParry는 각각 전용 후보, 나머지는 Light1입니다.

본 게임 MainCombatBridge는 아직 이 컴포넌트와 자동 연결되지 않습니다. VFX 담당 외 공유 파일을 수정하지 않았습니다. 본 게임 어댑터는 실제 타격창 시작 시 리본을 만들고 `UConstellationCombatFX::ConfigureTrail(Ribbon,Profile)` 후 승인된 무기 끝 위치를 `AddTip`에 전달합니다. 타격창 끝/공격 종료/취소/피격/사망/가드 전환/권한 회수에는 해당 실행의 리본을 정리합니다. 실행 ID를 비교하여 오래된 종료 이벤트가 다음 타를 지우지 않게 합니다. CombatRuntime에는 OnActionEnded와 OnPresentationReset 정리를 보강했습니다.

### 확정 접촉

`UConstellationCombatFX::SpawnContact(Context,Result,TargetHitKind,Position,Direction)`:

- Result=Miss: 생성하지 않습니다.
- Result=Hit: 대상이 정한 TargetHitKind를 그대로 사용합니다. 강공격도 SlimeHit를 SwordHit로 바꾸지 않습니다.
- Result=Guard: SwordBlock 하나를 생성합니다.
- Result=PerfectGuard: SwordParry 접촉 섬광 하나를 생성합니다. **패링 공격을 시작하는 함수가 아닙니다.**

판정 어댑터는 한 접촉에 결과 하나만 전달해야 합니다. PerfectGuard 호출 후 기존 일반 피격 호출까지 함께 수행하면 API 밖에서 중복되므로, 기존 피해/피격 처리와 결과 분기 연결을 확인해야 합니다. 반환된 FX의 Owner를 전투 주체로 설정해 취소/사망 정리에 포함합니다. 대상의 커스텀 HitCue가 있으면 기존 SpawnCue 경로를 우선하고 이 기본 API를 추가 호출하지 않습니다. 위치는 피해 계산 위치와 분리된 표시 위치를 받을 수 있으며, 기존 슬라임 표면 보정 코드를 유지합니다.

### 그로기 상태

적에게 `UConstellationGroggyFXComponent`를 등록합니다. `LocalOffset`은 모델 중심/머리 근처의 실제 위치를 보고 조정할 후보이며 기본 (0,0,70)cm입니다.

1. 확정 그로기 진입: `SetGroggy(true)` — 진입 파편과 유지 6개 생성.
2. 유지 중 추가 피해: 상태를 유지. 같은 true 반복은 진입을 재생하지 않음.
3. 자연 회복: `SetGroggy(false)` — 이전 효과 정리 후 해제 파편 1회.
4. 사망/리셋/액터 제거: `StopPresentation()` — 회복 파편 없이 전부 제거.

본 게임 MainEnemyGroggy와 CombatRuntime 양쪽 어댑터에서 위 계약을 호출해야 합니다. 이 컴포넌트는 HP·게이지·지속시간을 판단하지 않습니다. 공격 VFX의 피격 중단은 이제 공격 궤적만 정리하므로 독립 그로기 루프를 지우지 않습니다. 전체 표시 리셋 후 아직 살아 있고 그로기인 경우 true를 재전달하면 유지 루프만 복원합니다.

## 후보 확인

기존 `L_VFXGallery`를 `-game -VFXCandidatesReview`로 열면 후보 전용 검토를 실행합니다. 새 맵을 만들거나 저장된 갤러리를 바꾸지 않습니다. 평상시 갤러리 입력/카메라는 그대로입니다. `-VFXCandidatesCapture`를 추가하면 약 19초 후 종료하며 `Saved/VFXCandidates/trails.png`, `contacts.png`를 요청합니다. 모든 일회성 실행에는 `-NoAssetRegistryCache -NoAssetRegistryCacheWrite`를 함께 지정합니다.

자동 캡처 옵션은 **별도로 실행한 검증용 UE 프로세스에서만** 사용합니다. 종료 시 프로세스 자체를 종료 요청하므로 작업 중인 일반 편집기에 적용하지 않습니다. 캡처 옵션이 없으면 두 비교 단계를 반복합니다.

궤적 검토의 두 행: 약1/약2/약3/강1, 강2/약패링/강패링. 접촉 검토의 두 행: 검명중/슬라임피격/플레이어피격/가드, 퍼펙트성공/그로기진입/유지/해제. **검토 궤적은 비교용 합성 곡선**으로 실제 모션 타이밍 합격 근거가 아닙니다. 모션 미승인 항목은 후보로 남깁니다.

## 검증 기록

- 테스트를 구현보다 먼저 작성했지만 다른 빌드가 진행 중이어서 최초 실패 실행은 수행하지 못했습니다. TDD red/green 완료로 보고하지 않습니다.
- 읽기 전용 코드 리뷰에서 발견한 액션 맵 const 키 문제, 긴 잔상 프로필 테스트의 샘플 간격 문제를 수정했습니다.
- 리뷰에서 확인한 추가 피격과 그로기 루프 정리의 충돌을 수정하고 회귀 테스트를 추가했습니다.
- 독립 Editor Development 빌드 성공: `Saved/CombatExpansion/vfx1/build.log` 및 최종 검토 화면 빌드 `build-review.log`. 원본 DLL을 사용하는 편집기는 종료하지 않았습니다. 긴 최초 검증 경로는 Windows 260자 제한으로 실패해 짧은 새 경로에서 빌드했습니다. 초기 기록은 보존했습니다.
- VFX + CombatVFX 자동화 **24개 통과, 실패 0, 미실행 0**: `Saved/CombatExpansion/vfx1/reports-verified/index.json`, `tests-verified.log`. 이 중 15개는 경고를 포함합니다. 임시 테스트 월드의 context 부재, 기존 몽타주의 겹친 branching point, GameplayCue 경로 미지정 경고입니다. 경고 없는 전체 프로젝트 검증으로 보고하지 않습니다.
- 첫 통합 실행에서는 `Constellation.CombatVFX.Contact.SlimeCustomCue`가 제거된 SKM_Slime_Normal 경로 때문에 실패했습니다. 10월 24일 교체 기록과 현재 기획서의 유지 모델을 확인하고 테스트 참조를 SKM_Slime_Liquid/AS_Slime_Liquid_Idle로 바꾼 뒤 24개 모두 통과했습니다. 모델·리그·애니메이션 에셋은 변경하지 않았습니다.
- 신규 검사: 7종 프로필의 실제 리본 형상, miss 미생성, perfect 단일 접촉, SlimeHit 종류 보존, 그로기 반복 진입/복귀 중복 방지, 30초 유지 후 실제 ISM 인스턴스 6개, 사망 정리, 실제 OnHitReceived 이벤트 후 루프 보존.
- 실제 D3D12 갤러리 렌더링으로 궤적 7종과 접촉/그로기 8종을 확인했습니다. `Saved/CombatExpansion/vfx1/Saved/VFXCandidates/trails.png`, `contacts.png`. 최초 배경 혼합 화면은 같은 경로의 `initial/`에 보존했습니다. 검토 전용 모드는 배경을 잠시 숨기고 동일 배율의 직교 카메라를 사용합니다. 일반 갤러리 UI 코드를 수정하지 않았습니다.
- 렌더링 로그 `review-isolated.log`에는 엔진 NiagaraToolsets Python 초기화의 `NiagaraToolset_Info` AttributeError가 있습니다. 이번 후보는 해당 Python 도구를 사용하지 않으며 두 이미지 저장 및 검증 프로세스 정상 종료를 확인했습니다.
- 화면에서 약/강의 폭·잔상 차이, 패링의 짧은/긴 곡선, 가드/퍼펙트 섬광의 크기 차이와 그로기 3종 생성은 확인했습니다. 검 리본의 외곽은 기존 재질의 부드러운 발광 형태입니다. 실제 배경 위 선명도와 모델 주변 그로기 위치는 후속 외형 검수 대상입니다.
- 본 게임 전체 연결, 승인 모션 동기화, 실제 플레이의 외형·성능, Shipping/Cook는 아직 검증하지 않았습니다. 헤더/API 제공과 본 게임 적용 완료를 구분합니다.

## 다음 연결 작업

MainCombatBridge/MainEnemyGroggy/CombatAbilitySystem 담당자는 위 API 계약에 따라 가드·퍼펙트 접촉 및 그로기 상태 전환을 연결하고, 본 게임과 전투 시험장에서 각각 검증해 주세요. 모션 승인 후 실제 액션 자산에 약3/강2 프로필 매핑과 타격창을 설정합니다. 후보 재질을 최종 승인된 아트로 취급하지 않습니다. 이번 작업에서 커밋·푸시는 하지 않았습니다.
