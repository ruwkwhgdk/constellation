# Combat VFX Candidates Implementation Plan

**Goal:** 최신 전투 기준의 공격·방어·그로기 표시를 기존 VFX 재료로 제작하고 연결 API를 전달합니다.
**Architecture:** ConstellationVFX에 게임 규칙과 독립적인 후보 프로필/접촉 결과/그로기 수명 관리 API를 추가합니다. CombatVFXComponent는 기존 실제 타격창에서 프로필을 선택합니다. 공유 MainCombatBridge, CombatAbilitySystem, HUD는 수정하지 않습니다.
**Tech Stack:** Unreal 5.8 C++, 기존 procedural ribbon/ISM/materials.
**Spec:** ../specs/2026-10-26-light-heavy-attack-design.md 및 2026-10-27 전달된 VFX 제작 범위.

## 제약과 결정
- 사용자 요청 범위의 전용 후보입니다. 색·폭·잔상·밝기는 제작자 제안이며 승인된 모션/타격창을 새로 정의하지 않습니다.
- develop 공유 체크아웃의 VFX 파일만 수정합니다. 커밋/푸시하지 않습니다.
- 기존 enum 값과 기본 리본 설정을 보존합니다. 피격 종류는 대상이 결정합니다.
- 퍼펙트 성공은 접촉 결과이며 패링 공격은 별도 궤적입니다. 빗나감에는 접촉 효과를 만들지 않습니다.
- 기존 빌드와 경쟁하지 않습니다. 새 UE 검증은 두 AssetRegistry 캐시 방지 플래그를 사용합니다.

## 작업
- [x] 테스트: 후보 리본 폭/잔상 차이, miss/perfect 단일 접촉, SlimeHit 정체성, 그로기 중복 진입/해제/정리.
- [x] ConstellationCombatFX.h/.cpp: 7종 궤적 프로필과 접촉 결과 API, 그로기 전용 컴포넌트.
- [x] ConstellationSwordRibbonComponent: 기본값을 보존한 폭/잔상/밝기 설정.
- [x] ConstellationFXActor/Library: enum 뒤에 그로기 3종 추가, 고정 입자 유지와 명시적 종료.
- [x] CombatVFXComponent: 액션별 프로필 지정과 종류별 후보 선택, 종료/reset 수명 정리. 공유 액션 정의 파일은 수정하지 않습니다.
- [x] 독립 검증 프로젝트에서 빌드/자동화 테스트. 실제 모션 동기화·게임 연결·외형 검수는 구분해서 기록.
- [x] 새 제작 기록: 자산 재사용 목록, 이벤트 계약, 미연결 항목과 검증 범위.

## 검토 중점
오래된 종료 이벤트가 새 궤적을 끄지 않음; 명시적 Disabled 존중; 강공격이 SlimeHit를 금속 피격으로 바꾸지 않음; 사망 시 그로기 해제 연출을 내지 않음; 유지 효과가 무한히 입자를 생성하지 않음.

## 실행 기록
- 기존 검 리본/공통 피격은 존재합니다. 독립 약/강 패링 및 그로기 VFX는 없습니다.
- 다른 빌드의 cl/dotnet 프로세스가 실행 중입니다. 현재 빌드 실행을 보류합니다.
- 테스트 우선 작성 후 컴파일/실행은 기존 빌드 종료를 확인한 다음 수행합니다. 실제 red/green 실행 여부를 결과에서 구분합니다.
- 완료 기록: `docs/2026-10-27-combat-vfx-candidates.md`. 독립 빌드 성공, 24개 관련 자동화 통과(15개 경고 포함), 합성 궤적/접촉 비교 실제 렌더링. 첫 통합 실행의 이전 슬라임 경로 실패를 현재 유지 자산 참조로 수정했습니다.
- 리뷰 수정: 액션 맵 const 변환, 테스트 샘플 간격, 추가 피격 시 독립 그로기 루프 정리 충돌. 검토 전용 카메라/배경 분리를 추가했습니다. 실제 모션·본 게임 연결·성능/쿠킹 검증은 완료 범위 밖으로 남깁니다.
