# Hold and Throw Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution or superpowers:subagent-driven-development if the user selects that method. Track steps with checkboxes.

**Goal:** 여주인공의 물건 들기·내려놓기·예측 투척을 게임에서 사용할 수 있게 연결한다.

**Architecture:** C++ `UHoldableComponent`와 `UCarryComponent`가 판정·상태·물리를 소유한다. 기존 캐릭터 Blueprint가 입력을 분기하고 애니메이션·HUD를 연결한다. 물건에는 `Ac_Holdable` Blueprint 컴포넌트를 붙인다.

**Tech Stack:** 프로젝트의 Unreal Engine 5.8, C++, Blueprint, Enhanced Input, UMG, 기존 게임 스켈레톤과 Blender 소스.

**Spec:** `docs/superpowers/specs/2026-10-01-hold-and-throw-design.md`

## Global Constraints

- 싱글플레이, 단일 강체 물건, 양손 운반, 한 번에 하나.
- 무게 한계 20%, 초기 캐릭터 50kg/물건 한계 10kg, 조정 가능.
- 좌클릭은 운반 시 조준/투척, 빈손 시 기존 공격. 유지 시간 충전 없음.
- 운반·조준은 걷기/방향 전환/시점만 허용. 전환 동작은 이동 제한.
- 미리보기는 최초 충돌 위치. 최종 정지 위치 보장 없음.
- 캐릭터 키 160cm, 기존 스타일과 94본 게임 스켈레톤 보존.
- Blender CLI는 `tools/run-blender.ps1` 사용.
- 환경의 유지 맵과 다른 작업의 변경을 덮어쓰지 않는다.

## Review Focus

1. 반복 입력/중복 Notify: 물건이 두 번 발사되거나 소유권이 꼬이지 않아야 한다.
2. 배치 동작 중 새 장애물: 물건을 유지하고 운반 상태로 복귀해야 한다.
3. 긴 물건/낮은 천장: 중심점 궤적만 통과했다고 발사 가능으로 판정하면 안 된다.
4. 죽음/시네마틱과 중단: 운반 해제가 기존 액션 제한을 해제하면 안 된다.
5. 좌클릭 취소/포커스 상실: 예기치 않은 투척과 남은 미리보기가 없어야 한다.

## Task 1: 현행 연결과 안전한 편집 범위 확정

**Files:** `tools/audit-carry-integration.py`, `Saved/CarryReview/integration.json`.

- [x] Unreal Python으로 현재 `BP_Player_Heroine`, `BP_PlayerCharacter`, `Ac_Interact`, `Ac_Ability`, `ABP_Player_Heroine`, `WBP_PlayerHUD`, `IAC_Default`를 로드한다. 기존 `ResourceRecoveryLibrary.export_blueprint_graphs`로 최신 그래프를 `Saved/CarryReview/graphs`에 기록한다.

```python
bp = unreal.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine')
assert bp is not None
text = unreal.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
assert 'EventGraph' in text
```

- [x] 각 입력 이벤트의 Started/Completed/Canceled 연결, 상호작용 대상 선택, 액션 상태와 죽음/피격/시네마틱 경로를 기록한다. 공격·점프·회피·대시·변신 진입점 목록을 빠짐없이 작성한다.
- [x] 활성 게임 메시·ABP·스켈레톤과 신규 소스의 호환성을 확인한다. 기존 검 소켓과 무기 표시의 운반 중 처리를 기록한다.
- [x] 수정 대상 에셋만 해시와 원본을 `Saved/CarryReview/backups`에 보존한다. 현재 열린 편집기와 Blender를 중단하지 않는다.
- [x] 조사 결과와 변경 목록이 일치하는지 검토한다. 과거 audit 자료에서 확인한 경로가 현행에도 유효한지 검사한다.

## Task 2: 무게·상태·투척 수학의 자동 검증

**Files:** `Source/Constellation/CarryMath.h`, `Tests/CarryMathTests.cpp`, `tools/test-carry.cmd`, `Source/Constellation/CarryTests.cpp`.

**Interfaces:** `CanLift(double ObjectKg, double CharacterKg, double Ratio)`, `SolveThrow`는 목표 변위/중력/비행 시간에서 초기 속도를 반환한다. Unreal과 독립된 수학만 헤더에 두고 월드 충돌 판정은 컴포넌트에서 한다.

- [x] 테스트부터 작성하고 최소 선언/기본 실패 반환으로 실제 assertion 실패를 확인한다. 음수·0·NaN 질량, 9.99/10/10.01kg 경계, 서로 다른 높이 목표를 포함한다.

```cpp
assert(!CarryMath::CanLift(10.01, 50.0, 0.20));
assert(CarryMath::CanLift(10.0, 50.0, 0.20));
assert(CarryMath::CanLift(9.99, 50.0, 0.20));
assert(!CarryMath::CanLift(-1.0, 50.0, 0.20));
```

- [x] 유한값/양수 확인 후 무게 비율 판정을 구현한다. 투척은 `Vxy = DeltaXY / T`, `Vz = (DeltaZ - 0.5 * GravityZ * T * T) / T`로 계산하고 0 이하 비행 시간은 거부한다.
- [x] 수치 적분한 위치가 목표에 도달하는지 검사하고 동일 시작점·목표, 높고 낮은 목표, 거리 한계와 Z축 회전 상한을 추가 검증한다.
- [x] `tools/test-carry.cmd`는 기존 독립 C++ 테스트 방식처럼 VS 환경을 불러오고 `Saved/CarryTests`에서 실행한다. 엔진 상태 전환 테스트 이름은 `Constellation.Carry.*`로 등록한다.

## Task 3: 물건과 플레이어 컴포넌트

**Files:** `Source/Constellation/HoldableComponent.h/.cpp`, `Source/Constellation/CarryComponent.h/.cpp`, `Source/Constellation/CarryTests.cpp`.

**Interfaces:** `bool TryPickUp(UHoldableComponent*)`, `bool TryPlace()`, `bool BeginAim()`, `void CancelAim()`, `bool CommitThrow()`, `void OnPickupContact()`, `void OnPlaceRelease()`, `void OnThrowRelease()`, `void FinishAction()`, `void AbortCarry()`, `bool BlocksOtherActions() const`, `bool AllowsWalking() const`. 실패 이유는 enum과 UI 이벤트로 공개하며 내부 이름을 화면에 표시하지 않는다.

- [ ] transient world의 실제 컴포넌트 테스트로 초기 상태, 중복 획득, 무효 대상, 애니메이션 이벤트 중복, 대상 파괴, EndPlay 처리를 검증하고 구현 전 실패를 확인한다.

```cpp
TestTrue(TEXT("Pickup accepted"), Carry->TryPickUp(Holdable));
TestTrue(TEXT("Other actions blocked during pickup"), Carry->BlocksOtherActions());
TestFalse(TEXT("Repeated pickup rejected"), Carry->TryPickUp(Holdable));
Carry->OnPickupContact();
Carry->OnPickupContact();
TestEqual(TEXT("Duplicate contact keeps one carried actor"), Carry->GetHeldActor(), Item);
```

- [x] 대상의 단일 물리 몸체와 루트 구성을 검증하고 설정 저장→부착→분리→복구를 구현한다. 물리 질량을 게임 설정과 일치시킨다.
- [x] `BlocksOtherActions()`는 기존 상태를 덮어쓰지 않고 추가 조건으로 사용한다. 중단 시 사망/시네마틱 상태의 이동이나 입력을 허용하지 않는다.
- [x] 배치 시작/분리 시 각각 충돌 검사한다. overlap뿐 아니라 손→배치점 경로와 바닥 경사도 확인한다. 바닥 접촉을 장애물로 오판하지 않는다.
- [x] 장애물 진입 테스트에서 분리 실패 후 물건 유지, 상태 복귀, 이동 설정 복구를 확인한다.

## Task 4: 조준·예측·투척과 UI

**Files:** `CarryComponent.h/.cpp`, `CarryTests.cpp`, `Content/Constellation/Gameplay/Interaction/Materials/M_HoldPreview.uasset`, `Content/Constellation/UI/Widgets/WBP_PlayerHUD.uasset`.

- [ ] 테스트 월드에 벽/낮은 천장/긴 상자/경사를 배치하고 경로 검사와 발사 거부 테스트가 실패하는 것을 확인한다.
- [x] 목표 탐색, 거리 제한, 예상 분리 자세, 동일 중력/속도에 따른 예측을 구현한다. 실제 지원 충돌 형상으로 검사하고 최초 충돌 지점을 미리보기로 표현한다.
- [x] 실제 발사는 release 이벤트에서 재검사 후 한 번만 수행한다. 거리 기반 월드 Z 각속도와 투척자 충돌 제외/복구를 구현한다. 반복 release 테스트로 두 번째 발사가 거부되는지 확인한다.
- [x] 시각용 Mesh와 반투명 material을 구성한다. 충돌·상호작용 없음, 유효 청록/불가 적색, 조준 종료/포커스 상실/파괴 시 제거를 검증한다.
- [ ] 중앙 아래 메시지 3종을 HUD에 연결한다. 2초 유지, 동일 메시지 시간 갱신을 검증한다.

## Task 5: 기존 Blueprint 입력과 검토 맵 연결

**Files:** `BP_Player_Heroine.uasset`, 필요한 기존 `Ac_Interact`/`Ac_Ability`, `Content/Constellation/Gameplay/Interaction/Components/Ac_Holdable.uasset`, `Content/Constellation/Gameplay/Interaction/Actors/BP_Holdable_TestBox.uasset`, `Content/Constellation/Review/Carry/Maps/L_Carry_Review.umap`.

- [x] Task 1 목록에 있는 액션 진입점에 운반 상태 검사를 추가한다. 기존 빈손 공격·점프·대시·회피·변신이 그대로 동작하는 회귀 검증을 준비한다.
- [x] 운반 중 Interact는 내려놓기, Aiming 중 Interact는 취소, 빈손 Interact는 기존 흐름에서 Holdable을 처리한다. 좌클릭 Started는 조준, Completed는 투척, Canceled는 취소로 분기한다.
- [x] 실제 캐릭터에 CarryComponent를 추가하고 상체 운반 소켓/무기 표시를 연결한다. 다른 NPC·슬라임에는 자동 적용하지 않는다.
- [ ] 검토 맵에는 9.99/10/10.01kg 상자, 벽, 낮은 천장, 경사, 배치 차단 물건과 투척 거리 표식을 둔다. 기존 유지 환경 맵을 변경하지 않는다.
- [x] 수정 Blueprint 컴파일·저장 후 별도 엔진 실행으로 다시 읽고 컴파일 결과와 참조를 보고서에 기록한다.

## Task 6: 애니메이션 제작과 최종 검증

**Files:** `ArtSource/Heroine_Tripo_Review/Carry/` 편집 blend/FBX/README/검토 영상, `Content/Constellation/Characters/Heroine/Refined/Animations/Carry/`, `ABP_Player_Heroine.uasset`, `Saved/CarryReview/verification.json`.

- [x] `AnimationWorkflow/SKILL.md`와 유지 소스의 최신 README를 다시 확인한다. Delivery 리그·스켈레톤을 출발점으로 집기/내려놓기/던지기 및 운반·조준 자세를 제작한다.
- [x] Blender CLI는 보호 launcher로 실행한다. 프로필 실패 시 해당 명령만 정상 사용자 실행 맥락으로 승인 요청한다. 현재 interactive Blender를 종료하거나 덮어쓰지 않는다.
- [x] 중형 상자에 대해 접촉/분리 Notify, 손 IK, 운반 보행 합성, 몽타주 회복/중단을 연결한다. 임시 자세는 최종 모션으로 표시하지 않는다.
- [ ] 정면/양측 사선/측면 실제 속도 재생에서 손목·접지·발 미끄러짐·치마/물건 간섭을 검토한다. imported skeleton, duration, preview mesh를 저장 후 별도 실행에서 검사한다.
- [x] 독립 수학 테스트, `Constellation.Carry`와 기존 `Constellation` 자동 테스트, 엔진 빌드, Blueprint 컴파일과 재로드를 수행한다. 실행 명령과 결과 파일을 남긴다.
- [ ] PIE에서 무게 경계, 반복 입력, 운반 중 모든 액션 제한, 배치 중 장애물 진입, 근거리/최대거리, 낮은 천장, 조준 취소, 피격/사망, 미리보기 위치와 실제 첫 충돌을 확인한다. 위치 오차의 허용 기준은 초기 10cm이며 범위를 보고한다.
- [x] 사용자 시각 검토용 실제 플레이와 애니메이션 영상을 전달한다. 수행하지 않은 검증이나 남은 품질 문제를 명시한다.

## 실행과 변경 관리

권장 방식은 Native: 동일 에이전트가 이번 세션에서 순서대로 구현한다. Blueprint·애니메이션·게임 내 검증의 연결 의존성이 크므로 같은 문맥에서 진행하는 편이 적합하다. 병렬 방식은 사용자가 선택한 경우에만 사용한다.

조사 중 Git status가 LFS 임시 파일 쓰기 권한으로 실패했다. 전역 설정과 저장소 소유권을 변경하지 않는다. 변경 파일 목록/해시를 기록하고 필요한 Git 쓰기 작업은 정상 승인 경로를 사용한다. 문서 작성만으로 기능 구현이 끝났다고 보고하지 않는다.
