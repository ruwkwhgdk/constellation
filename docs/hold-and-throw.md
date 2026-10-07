# 물건 들기·내려놓기·던지기

## 기획자용 테이블 편집

콘텐츠 브라우저에서 `/Game/Constellation/Gameplay/Interaction/Data`를 연다.

| 에셋 | 행 / 키 | 수정할 내용 |
|---|---|---|
| `ST_CarryMessages` | `TooHeavy`, `PickupUnreachable`, `PlaceBlocked`, `ThrowBlocked` | 무게 초과, 도달 불가, 내려놓기 실패, 투척 실패 문구 |
| `DT_CarrySettings` | `Default` | 캐릭터 무게·들기 비율, 상호작용 거리, 투척 거리·비행 시간, 동작 재생 속도, 몽타주·미리보기 재질·안내 String Table |
| `DT_HoldableItems` | `SchoolChair`, `SchoolDesk`, `TestBox` | 운반 위치, 좌우 손 위치, 던지기 허용, 내려놓기 회전 |
| `DT_PhysicsProps` | `SchoolChair`, `SchoolDesk`, `TestBox` | 질량, 이동·회전 감쇠, 초기 물리·중력, Physical Material |

문구는 String Table의 **Source String**을 수정하고 키는 유지한다. 공통 수치는 Data Table의 `Default` 행을 선택해 편집한다. `PickupPlayRate`와 `PlacePlayRate`는 현재 2이며, 1은 원래 속도다. `Pickup/Place/ThrowContactTime`과 `Duration`은 몽타주가 없을 때 사용하는 대체 시간이다. 몽타주가 있으면 실제 접촉 시점은 몽타주의 Notify를 따른다. `NoticeDuration`은 실패 문구 표시 시간(초)이다.

`BP_Player_Heroine`의 Carry 컴포넌트 → **Carry / Data / Settings Row**가 공통 행을 선택한다. 각 물건의 `Ac_Holdable` → **Holdable / Data / Item Row**가 물건 행을 선택한다. 새 물건은 `DT_HoldableItems`에 행을 추가한 뒤 이 항목에서 지정한다. 운반 위치와 손 위치는 물건 로컬 좌표를 사용한다. `HoldMesh`가 지정되지 않았으면 기존대로 루트 Static Mesh를 사용한다.

저장 후 PIE를 다시 시작하면 적용된다. 질량은 DT_PhysicsProps에서 게임 시작 시 적용하며, 들기 판정은 실제 메시 질량을 사용한다. 들 수 있는 최대 무게는 `CharacterWeightKg × LiftWeightRatio`다. 운반 중에는 설정 재적용을 차단한다. **Resolved** 항목은 적용값 확인용이며 기획 수정은 테이블에서 한다. 미는 힘은 주인공의 Character Movement 설정에 유지한다(최초 360, 지속 6000).

`tools/setup-carry-tables.py`는 초기 이관과 블루프린트 연결용이며 이미 존재하는 행·문구를 덮어쓰지 않는다. 이관 전 블루프린트 백업과 검증 자료는 `Saved/CarryReview/DataTables/`에 있다. 아래 과거 수치 조정 스크립트는 테이블 도입 이전의 기록이며, 이후 기획값 수정은 테이블에서 진행한다.

## 플레이

현재 조정값: 주인공의 최초 밀기 힘은 360, 지속 밀기 힘은 6000으로 이전 300/5000보다 20% 높였다. 집기·내려놓기 몽타주는 2배속이며 접촉 Notify도 함께 빨라진다. 애니메이션이 없는 경우의 대체 타이머도 절반으로 줄인다. 던지기·운반 루프 속도는 유지한다. 아래 이전 물리 조정 수치와 시험 결과는 당시의 기록이다.

`/Game/Constellation/Review/Carry/Maps/L_Carry_Review`를 열고 Play로 확인한다. 실제 `BP_Player_Heroine`을 사용한다. AbandonedSchool에도 적용되어 있으며, 해당 맵의 가구 5개에 남아 있던 개별 물리 비활성 설정을 수정했다.

| 입력 | 동작 |
|---|---|
| F | 빈손이면 앞의 물건 들기, 운반 중이면 내려놓기 |
| 마우스 왼쪽 버튼 유지 | 조준 및 반투명 도착 위치 표시 |
| 마우스 왼쪽 버튼 해제 | 던지기 |
| 조준 중 F | 조준 취소 후 운반 상태 복귀 |

기존 Enhanced Input `IA_Interact`와 `IA_Attack`을 사용하므로 키 재설정을 따른다. 운반 중에는 걷기와 시점 조작만 허용하고 공격·점프·회피·대시·변신·밀기를 차단한다. 집기·내려놓기·발사 전환 중에는 이동을 멈춘다. 운반 동안 검을 숨기고 종료 시 원래 표시 상태를 복구한다.

운반 컴포넌트는 이동 속도를 덮어쓰지 않고 캐릭터의 기본 걷기 속도를 유지한다. 현재 주인공은 500cm/s이며, 기존 운반 전용 100cm/s 제한은 제거했다.

들고 있는 물건은 충돌을 끄고, 물건이 벽에 닿아도 캐릭터 이동·회전을 되돌리지 않는다. 따라서 운반 중 물건 외형이 벽을 통과할 수 있다. 내려놓기·투척 직전의 공간 및 경로 검사는 유지하며, 실제 분리 시 충돌과 물리를 복구한다.

## 새 물건 설정

### 학교 의자·책상 테스트 설정

`/Game/Constellation/Environments/School/Blueprints/`의 `BP_School_Chair`와 `BP_School_Desk`에 `Ac_Holdable`을 추가한다. 무게는 의자 8kg, 책상 10kg으로, 기본 주인공의 10kg 한계 안에 있다. 물리 질량과 들기 판정 무게를 동일하게 유지한다. AbandonedSchool에서 해당 블루프린트 인스턴스에 다가가 F로 들고, 다시 F로 내려놓거나 마우스 왼쪽 버튼을 유지한 뒤 놓아 던진다.

원래 자식 메시의 1.5배 크기·회전·오프셋은 `School/Meshes/SM_SchoolChair_Holdable`, `SM_SchoolDesk_Holdable` 사본의 형상과 단순 충돌에 반영한다. 메시를 루트로 사용하되 블루프린트의 기본 외형과 Actor 배치 변환을 유지하기 위한 설정이다. 원본 모듈 에셋은 수정하지 않는다. 처음부터 물리 시뮬레이션과 중력을 켜며, 운반 중에만 끈다. 가구의 선형 감쇠는 0.8, 각 감쇠는 2, 초기 겹침 해소 속도 한계는 100cm/s다. 투척 중 감쇠는 기존 포물선 예측에 맞춰 일시적으로 0으로 변경하고 첫 충돌 후 복구한다.

설정 스크립트는 `tools/setup-school-holdables.py`, 독립 재로딩 검사는 `tools/verify-school-holdables.py`, 실제 주인공 PIE 검사는 `tools/review-school-holdables.py`다. 검증 결과는 `Saved/CarryReview/SchoolFurniture/`에 기록한다. 가구별 손 위치는 기능 테스트용 초기값이며 최종 연출 검토 대상이다.

2026-10-02 저장 에셋 재로딩에서 두 가구의 재질과 경계 크기가 유지됨을 확인했다. `L_Carry_Review`와 AbandonedSchool의 실제 주인공 PIE에서 각각 가구별 14개, 총 28개 항목(들기·행동 제한·내려놓기·재획득·유효 조준·물리 투척)이 통과했다. AbandonedSchool 검사는 `-SchoolActualMap -RenderOffscreen -nullrhi`로 기존 배치된 의자·책상을 사용하며 맵을 저장하지 않는다. 가구별 최종 시각 품질은 별도 검토 대상이다.

바닥에 정확히 닿은 물건은 Chaos가 `Time=0`, `bStartPenetrating=false`인 바닥 접촉을 반환할 수 있다. 집기 경로 검사에서는 위로 벗어나는 시작 지점의 바닥 접촉만 허용하고, 접촉면 바로 위에서 남은 경로를 다시 검사한다. 실제 시작 구역의 32개 가구·128개 접근 방향을 비교해 바닥 접촉 실패 22개가 해소됐으며, 벽과 겹친 두 집기 시도는 계속 차단됐다. 기존 의자 두 개의 네 접근 사례를 `tools/diagnose-school-pickup.py`에서 회귀 검사한다. 천장·벽·깊은 바닥 관통 차단도 C++ Carry 자동 검사에 포함한다. 수정 전후 자료와 빌드·자동 검사 보고서는 `Saved/CarryReview/SchoolPickup/`에 있다.

### 공통 설정

2026-10-03 접촉 반응 보완: 이전 1500의 밀기 힘은 튕김은 막았지만 가구가 거의 움직이지 않게 했다. 사용자가 말한 증상은 중력 비활성이 아니라 캐릭터로 밀 수 없는 문제였다. 주인공의 지속 밀기 힘을 5000, 최초 밀기 힘을 300으로 조정했다. 질량(8/10kg), 감쇠, 투척 설정은 유지한다. 접촉 힘만 재적용하는 도구는 `tools/tune-furniture-contact.py`다.

접촉 회귀 검사는 `tools/review-furniture-first-contact.py`를 사용한다. 이전 접촉 검사의 준비 과정에는 물리 재활성화가 있었고, 통과 조건도 튕김 상한만 확인했다. 새 검사는 시작한 가구의 물리를 재설정하지 않고, 캐릭터를 1.5초 동안 접근시킨 뒤 이동 거리의 하한·상한과 높이·속도 상한을 함께 확인한다. 실제 집기·내려놓기 후에도 같은 검사를 반복한다. 보고서와 주인공 백업은 `Saved/CarryReview/FirstContact/`에 보관한다.

저장된 에셋을 독립 재로딩한 15·30·60FPS 검사 12개가 통과했다(`final15.json`, `final30.json`, `final60.json`). 60FPS에서 가구는 약 38~44cm 밀렸고 원점의 최대 상승은 약 1.5cm 이내였다. 15FPS에서는 의자가 기울며 원점이 약 30cm 올라가므로 저프레임까지 동일한 움직임을 보장하는 설정은 아니다. 이전 지속 힘 10000 후보는 변동 프레임 검사에서 과도하게 튀어 최종 채택하지 않았다.

넘어진 의자·책상으로 실제 주인공의 집기 전환·내려놓기·F키 재획득·조준·투척 36개 항목도 검토 맵에서 통과했다(`-SchoolTiltedPickup`). 결과는 `Saved/CarryReview/StartupAndTilt/tilted-play-verification.json`에 있다.

2026-10-03 시작 물리·넘어진 물건 보완: AbandonedSchool의 `VINE_Desk1`, `VINE_Desk4`, `VINE_Chair2`, `VINE_Chair5`, `VINE_Chair6`에는 블루프린트 기본값과 별도로 물리 비활성 설정이 저장되어 있었다. `tools/fix-school-instance-physics.py`로 해당 5개만 수정해 맵을 저장했다. 기존 배치 276개 모두 시작 시 물리·중력이 켜지는 것을 확인했고, 별도 공중 배치 가구 2개는 물리 재활성화 없이 약 149cm 낙하했다.

집기 사거리는 물체 원점 대신 실제 경계 상자까지의 거리로 판정하며, 메시 중심까지 시야가 가려졌는지 확인한다. 접촉 시점에 다시 검사하고 충돌을 끈 후 운반 자세로 전환한다. 충돌 없는 운반 정책에 맞춰 집기 전의 운반 자세 공간·경로 검사는 제거했다. 넘어진 물체를 세운 상자로 검사하면서 생기던 불필요한 차단을 없애고, 벽 너머 물체의 집기는 계속 차단한다. 내려놓기·투척 경로 검사는 유지한다. C++ 회귀 검사 2개와 12가지 자세별 집기 검사를 통과했다. 재현 도구는 `tools/diagnose-furniture-start-and-tilt.py`, 변경 전 맵 백업과 보고서는 `Saved/CarryReview/StartupAndTilt/`다. 아래 바닥 접촉·근접 오프셋 기록은 이전 구현의 수정 이력이다.

2026-10-02 책상 근접 집기 수정: 캐릭터와 책상 원점의 수평 거리가 65cm인 사례에서 기존 운반 위치가 뒤쪽 의자와 실제로 겹쳤다. `BP_School_Desk`의 `CarryOffset`을 `(72,0,-70)`에서 `(60,0,-70)`으로 변경해 몸쪽으로 12cm 당겼다. 주변 장애물 검사는 유지한다. 진단과 이번 검증 자료는 `Saved/CarryReview/DeskPickup/`에 보관한다.

2026-10-03 물리·재획득 수정: 바닥 원점을 사용하는 의자가 안착 후 바닥 아래로 미세하게 내려가면, 원점까지의 시야 검사가 바닥을 장애물로 판단했다. 시야 검사 끝점을 메시 경계 중심으로 변경했다. 바닥 아래 0.01cm에 있는 의자 선택은 허용하면서 벽 너머 집기는 차단하는 C++ 회귀 검사를 추가했다.

가구 접촉 시 과도한 힘을 줄이기 위해 `BP_Player_Heroine`의 지속 밀기 힘을 750000→1500, 최초 밀기 힘을 500→100으로 조정했다. 접촉 힘은 0.1, 최대 접촉 힘은 50이며 질량 비례 증폭을 끈다. 이 설정은 주인공이 접촉하는 다른 물리 물체에도 적용된다. 재적용 도구는 `tools/tune-school-furniture-physics.py`다.

수정 빌드와 Carry C++ 자동 검사 2개가 통과했다. 실제 AbandonedSchool의 저장된 가구와 주인공으로 초기 물리·질량·집기·충돌 해제·걷기 속도·내려놓기·F키 재획득·조준·투척 36개 검사가 통과했다. `tools/review-furniture-physics.py`의 1초 걷기 접촉 시험에서 최고 속도는 의자 약 3492→2.87cm/s, 책상 약 25306→2.81cm/s였고 공중으로 튀어 오르지 않았다. 경사·다른 물체와의 강한 충돌 등 모든 배치에 대한 보장은 아니다. 이번 보고서와 변경 전 에셋 백업은 `Saved/CarryReview/FurniturePhysics/`에 보관한다.

1. Actor의 루트에 Movable Static Mesh를 둔다. 단일 강체, Simple Collision, `Query and Physics`가 필요하다. Complex-as-Simple 및 여러 물리 몸체는 지원하지 않는다.
2. `/Game/Constellation/Gameplay/Interaction/Components/Ac_Holdable`을 추가한다.
3. PhysicsProps 컴포넌트를 추가하고 Physics Row에서 DT_PhysicsProps 행을 선택해 MassKg를 지정한다. 캐릭터 기본 50kg, 한계 비율 0.2이므로 10kg까지 허용한다. 캐릭터 Carry 컴포넌트에서 두 값을 조정할 수 있다.
4. `CarryOffset`, `LeftHandGrip`, `RightHandGrip`을 물건 크기에 맞춘다. Grip은 물건 메시의 로컬 좌표다. `BP_Holdable_TestBox`는 36cm 상자 예제다.
5. `CanThrow`로 던지기 허용 여부를 지정한다. 물건의 충돌 채널과 응답은 배치·비행 검사에도 적용된다.

무게 초과 및 배치 공간 부족은 화면 중앙 아래에 2초간 표시한다. 배치 중 새 장애물이 들어오면 물건을 유지하고 운반 상태로 돌아온다. 피격·사망·입력 잠금·대상 파괴 시 소유권과 미리보기를 정리한다. 해제 위치가 모두 막혔으면 안전한 공간이 확보될 때까지 물리 복구를 보류한다.

## 투척과 미리보기

카메라가 보는 지점과 거리 한계를 사용하고 물체의 회전하는 경계 상자를 따라 비행 경로를 검사한다. 유효 위치는 청록, 불가 위치는 적색이다. 물체는 월드 중력에 따른 포물선으로 이동하며 거리에 비례한 월드 Z축 회전을 받는다. 비행 중 감쇠를 0으로 설정하고 첫 접촉 또는 재획득 시 기존 값을 복구한다.

실제 분리 시점의 물리 시간 간격으로 Chaos 적분 오차를 보정한다. 비행 중 프레임 간격이 크게 바뀌면 예측 오차도 달라질 수 있다. 검토 맵의 36cm 상자 장거리 투척에서 첫 접촉 오차는 고정 30FPS 약 1.8cm, 60FPS 약 4.0cm였다. 모든 물건·거리·프레임 변동 조건에서 같은 오차를 보장하는 수치는 아니다.

미리보기는 **첫 충돌 시점의 물체 위치**다. 튀거나 굴러간 뒤의 최종 정지 위치는 예측하지 않는다. 복잡한 비정형 메시의 경계 상자는 실제 충돌보다 보수적일 수 있다. 다른 중력을 사용하는 Physics Volume 경로는 투척 불가로 처리한다.

## 리소스와 유지보수

- 원본: `ArtSource/Heroine_Tripo_Review/Carry/`의 다섯 `.blend`, FBX, 제작·출력·렌더 스크립트.
- 게임 모션: `/Game/Constellation/Characters/Heroine/Base/Animation/Carry/`의 `AS_Carry_*`, `AM_Carry_*`.
- Hold/Aim: `CarryUpperBody` 슬롯, 기존 보행 합성 및 양손 IK. Pickup/Place/Throw: `DefaultSlot` 전신 동작 및 접촉 Notify.
- 메시와 리그를 교체하지 않고 유지 소스에서 제작한 첫 기능 검토용 모션이다. 물건별 손 위치와 의상 간섭은 새 크기의 물건을 추가할 때 시각 검토한다.
- 재생성: `tools/setup-carry-assets.py`; 저장 후 독립 재로딩 검사: `tools/verify-carry-assets.py`.
- 검증 자료: `Saved/CarryReview/`의 빌드 로그, 자동 테스트 보고서, `reload-verification.json`, `play-verification.json`, 실제 플레이 캡처.

최신 자동 테스트는 `Saved/CarryReview/final-tests/index.json`에 있으며 프로젝트 테스트 8개가 통과했다. 실제 60FPS PIE의 입력·접촉·배치·재획득·투척·무게 안내 검사 15개가 통과했다. 검토 영상은 `Saved/CarryReview/carry-play-review.gif`다. 운반 상태의 양손 Grip 오차는 2cm 이내였다. 전환 모션의 모든 물건 크기별 손 접촉, 다각도 의상 간섭, 이동 중 발 미끄러짐과 최종 연출 품질은 별도 시각 검토 대상으로 남긴다.

Blender 작업은 반드시 `tools/run-blender.ps1`을 사용한다. 현재 유지 소스와 캐릭터 규칙은 `ArtSource/Heroine_Tripo_Review/AnimationWorkflow/SKILL.md`를 따른다.

## 공통 소품 물리 테이블 (2026-10-03)

콘텐츠 브라우저: /Game/Constellation/Gameplay/Interaction/Data/DT_PhysicsProps

| 행 | MassKg | LinearDamping | AngularDamping | 초기 물리 / 중력 |
|---|---:|---:|---:|---|
| SchoolChair | 8 | 0.8 | 2 | 켜짐 / 켜짐 |
| SchoolDesk | 10 | 0.8 | 2 | 켜짐 / 켜짐 |
| TestBox | 5 | 0.01 | 0 | 켜짐 / 켜짐 |

PhysicalMaterial에는 Physical Material 에셋을 지정한다. 마찰·반발력·밀도는 해당 에셋에서 관리한다. MassKg는 명시적 질량이므로 밀도 변경보다 우선한다.

새 소품에는 **Physics Prop Component**를 추가하고 **Physics / Data / Physics Row**에서 테이블과 행을 선택한다. 기본 대상은 루트 PrimitiveComponent이며, 여러 메시가 있는 소품은 Mesh Component Name으로 적용 대상을 명시한다. 대상은 Movable이어야 한다. 들 수 없는 소품에도 이 컴포넌트만 사용할 수 있다. 들 수 있는 물건은 기존 Ac_Holdable의 Item Row도 지정한다.

게임 시작 시 한 번만 적용한다. 테이블 편집 후 PIE를 재시작하면 반영된다. 실행 중 재적용은 차단하며 들기·내려놓기·투척·복구의 물리 전환은 기존 운반 로직이 담당한다. Physics Row를 비워 두면 메시 자체 설정을 사용한다. 메시의 충돌 및 충돌 형상은 이 테이블의 범위에 포함되지 않는다.

DT_HoldableItems의 WeightKg와 HoldableComponent의 별도 WeightKg는 제거했다. GetWeightKg는 현재 물리 바디 질량을 읽고, 운반 때문에 바디가 없을 때는 엔진 CalculateMass를 사용한다. 이 계산은 메시의 질량 override를 그대로 따른다. 플레이어 무게·들기 비율은 DT_CarrySettings, 밀기 힘·이동 설정은 CharacterMovement에 유지한다.

생성/연결 도구: tools/setup-physics-props.py. 최초 이관 값은 ArtSource/Gameplay/PhysicsProps/initial-rows.json에 보관하며 기존 테이블이 있으면 덮어쓰지 않는다. 이후 기획 수정의 기준은 Unreal 테이블이다. 이관 확인은 tools/verify-physics-props.py로 수행한다(최초 이관 값 보존 확인용이므로 추후 의도적으로 튜닝한 값에는 비교 기준도 갱신해야 한다).

들기 한계 비교는 Chaos 질량 반올림 오차를 위해 0.0001kg(0.1g)의 허용 오차를 둔다. 10kg 한계에서 10.01kg은 거부한다.

검증: 저장 에셋 재로딩으로 세 물리 행과 Blueprint 연결, 기존 운반 행의 비질량 필드 보존을 확인했다. 최종 C++ 빌드 성공, Constellation 자동 검사 12개 실패 0개(5개는 경고 포함), 검토 맵 의자·책상 실제 플레이 검사 42개가 통과했다. 보고서는 Saved/PhysicsPropsReview/ 및 Saved/CarryReview/SchoolFurniture/에 있다. 이번 변경에서 패키징 및 학교 전체 맵 플레이는 실행하지 않았다.
