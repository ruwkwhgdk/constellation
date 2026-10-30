# Monster Telegraph VFX Implementation Plan

**Goal:** 노란 준비/붉은 실행 도넛 고리, 공격 실행 ID 기반 제어 API, 실제 UE 미리보기와 인계 기록.
**Spec:** ../specs/2026-10-26-light-heavy-attack-design.md §15.
**Architecture:** ConstellationVFX 전용 USceneComponent + 속이 빈 procedural annulus + 새 unlit 재질. 공격 코어/BP/UI는 수정하지 않습니다. 준비/실행 전환은 외부 이벤트만 수행하며 시각 맥동은 상태를 변경하지 않습니다.

## 제작자 선택 / 검수 후보
- 반지름60cm, 두께8cm, 얇은 어두운 안팎 테두리. 고리 중심은 삼각형 자체가 없는 공간입니다.
- 카메라 지향, 몸통 위치 부착, 준비 6% 맥동, 실행 순간 25% 밝기 증가는 후보 옵션이며 비활성화할 수 있습니다.
- 단일 재질과 96분할 고리를 재사용합니다. 다수 적에서 매 프레임 새 액터나 재질을 만들지 않습니다.

## 작업과 검증
- [ ] 재사용 재질 생성 및 원본 생성 스크립트 보존.
- [ ] API/회귀 테스트 먼저 작성: ID별 준비/실행, 자동 전환 없음, 오래된 호출 무시, 즉시 종료, 속 빈 형상, 독립 적, 유효하지 않은 설정.
- [ ] 실패를 확인한 후 전조 컴포넌트 구현. 기존 궤적/피격은 변경하지 않음.
- [ ] 밝고 어두운 배경, 근거리/원거리, 다수 적에서 기존 슬라임 모션과 실제 렌더링.
- [ ] 독립 검증 프로젝트 증분 빌드와 VFX 회귀, 코드 리뷰.
- [ ] docs/2026-10-27-monster-telegraph-vfx-delivery.md에 정확한 API·타입·기본값·검증 범위 기록.

## 보호 사항
기존 Intermediate/프로세스/검증 기록을 정리하지 않습니다. 새 UE 실행에 -NoAssetRegistryCache -NoAssetRegistryCacheWrite를 넣습니다. 커밋/푸시와 실제 공격 단계 연결, 애니메이션 제작은 범위 밖입니다.
