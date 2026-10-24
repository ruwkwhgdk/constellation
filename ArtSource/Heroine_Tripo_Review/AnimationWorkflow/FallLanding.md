# 낙하·착지 엔진 연결 — 2026-10-19

## 최신 타이밍 수정: Timing02

사용자 요청으로 일반·약한 착지의 끝 유지 자세를 제거했다. 최신 소스는 `Timing02/quick_candidate.json`의 Normal_AB/Weak_C와 기존 runtime_candidate04의 나머지 클립이다. 엔진 AS_Fall_Normal_AB_Quick(0.467초), AS_Fall_Weak_C_Quick(1.20초)을 기존 AM에 연결한다. AS 원본은 보존했으며 Quick 끝 구간에서 Idle로 직접 연결하고 발 접지를 보정했다. 초기 단순 몽타주 자르기 후보(GameRun01)는 Idle 블렌드 도중 발이 최대2.9cm 침범해 폐기했다. Quick의 몽타주 끝은 이미 Idle와 일치하므로 별도 blend-out0. AM_Fall_Severe_D RateScale1.5(충돌 후 복귀 전체5.644초)는 유지한다. GameRun02 실제 PIE22개 검사 통과: 조작 복귀 실측0.433/1.167/5.633초. 최신 영상은 Timing02/Delivery02/review.html. 이전 Timing02/Delivery 및 아래 DeliveryFinal은 최종본이 아니다.

사용자는 일반 A→B, 약한 C, 심한 D의 캐릭터 보정본을 엔진에 적용하도록 승인했다. D 종료 후 기존 승인 Locker AS_Locker_GetUp으로 복귀한다. 기존 낙하 높이 기준과 피해 계산은 PlayerFallComponent 소유이며 변경하지 않는다.

## 유지 소스

작업 루트: `C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/FallLanding_Heroine01/UnrealApply01`.
- 모델: `Heroine_FallMerged02.blend`. 기존 CarryD_Desk_CuffClearance를 복원하고 기존 685 엔진 모프를 보존했다.
- 동작: `runtime_candidate04.json`; 원본 승인 세 blend와 기존 승인 일어서기를 합성한 엔진 변환 데이터. contact04은 D 전환·회복 중 손/발 위치와 손가락 상대 회전을 보존하며 골반 높이를 최대 약4.04cm 보정한다.
- 엔진: `/Game/Constellation/Characters/Heroine/GamePilot/Fall/AS_Fall_*`, `AM_Fall_*`, `SK_Heroine_FallReview02`.
- BP_Player_Heroine의 PlayerFallAnimation 컴포넌트와 GP_ABP_Player_Heroine 최종 출력의 FallFullBody 슬롯으로 연결한다.

## 전달 시 재발 방지

1. 공중/착지/복귀를 실제 CharacterMovement와 PIE에서 검증한다. 시퀀스 단독 재생은 착지 블렌드 품질의 증거가 아니다.
2. 이 리그의 root scale100과 normalized root-motion scale 조합은 실제 변위를100배 증폭했다. Severe_D는 root motion을 사용하되 normalized scale은 false. 실제 복귀 위치 오차도 검사한다.
3. 착지 blend-in .15초는 공중→충돌 사이 발을 바닥 아래로 보간했다. 현재 충돌 몽타주 blend-in0.0초이며 정상 속도 시각 검사를 별도로 수행한다.
4. StrongAirborne 마지막 자세 유지 설정은 동적 몽타주 생성 후, Montage_Play 전에 적용한다. 재생 후 에셋 플래그 변경은 기존 인스턴스에 반영되지 않는다.
5. 종료 콜백은 인스턴스별 델리게이트와 재생 세대로 보호한다. 동일 몽타주 에셋 포인터만 비교하면 이전 종료가 새 착지 잠금을 해제할 수 있다.
6. 모프 이름 수와 실제 비영(非零) 델타 수를 구분한다. CPanel_031/081은 델타0이어서 FBX 임포트에서 제외됐다. 기존 엔진 모프685개는 모두 보존한다.
7. 저장본 재로드 본 데이터 일치, 손가락 수치 보존, BVH 교차0은 시각 합격을 대체하지 않는다. 실제 엔진의 전환·최대 변형·복귀를 확인하고 검증하지 않은 경사면/이동 발판/다른 행동 조합을 명시한다.

## 현재 상태

최종 저장 및 별도 엔진 재로드 완료. GameRun08 실제 PIE에서 세 높이·입력 복귀·긴 공중 자세 유지 등19개 기능 검사 통과. 기존 낙하 회귀3종도 통과. DeliveryFinal/review.html에 정상 속도 실제 PIE 영상3개와 검사 기록을 저장했다. 엔진 기록을 저장 모델에 재적용한 착지 표본185개에서 치마/다리 교차0; 전체 바닥 최저점 일반+0.018cm, 약한-0.032cm, 심한+0.053cm. 약한 착지의 약0.32mm 오차를 수치상 완전무관통으로 보고하지 않는다. 최종 소매 보정에서 손 위치 변화는 최대0.77cm이며 발/골반과 손가락 상대 자세를 보존했다. 큰 관절 꺾임은 검수 프레임에서 발견되지 않았다. 정상 속도 영상은 캡처 타임스탬프로15fps 재구성했고 인코딩 후 디코딩 프레임을 확인했다. 경사면/이동 발판/운반·전투 조합/패키징 빌드는 미검증.
