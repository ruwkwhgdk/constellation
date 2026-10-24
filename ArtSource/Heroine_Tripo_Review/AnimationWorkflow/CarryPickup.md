# 의자·책상 양손 집기 진행 기록 (2026-10-17)

사용자 승인: 양손 집기 자세 재작업. 캐릭터를 이동/회전시키지 않고 물체를 이동·회전해 정렬한다. 운반·투척 원본과 캐릭터 외형은 유지한다.

현재 편집 원본: `C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/CarryPickupD01/Attempt06/Heroine_Pickup_Chair.blend` 및 같은 폴더의 `Heroine_Pickup_Desk.blend`.
현재 UE 반영본: `CarryPickupD01/Unreal02`. 2.5초, 30fps, 1.0초 접촉. 독립 Pickup 몽타주와 테이블 FittedPickupMeshSpace 사용. 원본 모델의 기존 정점·UV·웨이트·재질·기존 모프를 보존하고 Pickup 소매 여유 모프만 추가했다. 검사 보고는 `Checks/CarryPickupD01_20261017/Attempt06`.

물체는 충돌 검사한 경로로 정렬한다. 직접 회전이 캡슐에 걸리면 공간이 허용될 때 바깥으로 이동한 뒤 회전/접근한다. 막힌 경로는 취소한다. 캐릭터 캡슐 이동·회전은 하지 않는다.

## 최종 결과 (2026-10-17)

사용자 후속 요청에 따라 정렬과 집기 애니메이션을 동시에 시작한다. .4초 직접 경로 또는 .75초 우회 경로로 정렬하고 1초 접촉 시점까지 준비한다. 캐릭터는 제자리에 유지한다.

- 최종 원본 Attempt06. 저장·재열기 snapshot compare에서 기존 메시 필드와 기존 shape key가 보존됨. 새 CarryPickup_CuffClearance만 추가.
- 최종 UE 설정/원본 검사 `Unreal02/asset_verification.json`: 각 클립 7144개 본 위치 표본, 최대 원본 오차 0.00631cm 미만. 기존 모프·재질 유지.
- 최종 증분 빌드 `build_matched_hold.log` 성공. 접촉 지연 복구 포함 Carry 회귀 3개 테스트 `hitch_test.log` 통과. 그 뒤 마지막 슬롯 전환 변경은 Run05/06 실제 게임으로 검증.
- 최종 정면 Run05, 후면 Run06에서 각 13개 흐름 검사 통과. 집기→운반→이동→조준→투척→조작복귀 확인.
- Run05 게임 본/모프를 저장 메시로 재현한 372개 샘플: 의상/가구 교차 0, 치마/다리 교차 0. 직접 GPU/연속 충돌 검증으로 확대 해석하지 않는다.
- 집기 손 접촉 목표 오차 최대 의자 0.071cm, 책상 0.037cm 미만. 발 본은 수치 정밀도 내 고정. 투척 발 본 최대 이동 의자 0.009cm, 책상 0.014cm 미만.
- 신발 표면은 스키닝 변형이 있고, 평지에서 최저점은 약 0.55~0.87cm 높이였다. 발 본 고정과 표면 완전 접촉을 동일시하지 않는다.
- 최종 영상: CarryPickupD01/Delivery/review.html. timing은 가구 먼저 정렬하던 Run02 대비 동시 정렬 Run05. pickup/throw는 과거 Run10 대비 최종 Run05. rear는 최종 Run06.
- 실제 플레이어/가구 BP를 사용하는 평지 검증 맵 범위이며 폐교 모든 지형/배치를 검사하지 않았다.

## 전환/취소에서 유지해야 할 조건

1. Pickup montage는 enable_auto_blend_out=False. 마지막 자세를 유지하다 끝 위치에서 FinishAction으로 넘긴다.
2. 이 Pickup의 마지막 자세는 Hold 원본과 일치한다. 다른 슬롯을 .15초씩 동시에 혼합하면 중간에 idle이 섞여 소매와 접촉이 무너졌다. 일치하는 이 전환에만 Montage_PlayWithBlendIn(0)을 사용한다. 다른 임의 애니메이션 전환에 일괄 적용하지 않는다.
3. 물체 lift 시간은 실제 Montage_GetPlayRate로 계산한다. 기존 generic PickupPlayRate(2)를 새 클립(1)에 쓰지 않는다.
4. 정렬 중 이른 접촉 알림은 bPickupContactPending에 보관하고 완료 시 처리한다. hitch에서 버리면 auto-blend-out 없는 PickingUp에 멈춘다.
5. 중도 취소 시 원래 물리 시뮬레이션을 썼다면 RestoreWhenClear로 안전하게 복구한다. 물리가 없던 가구는 불필요한 pending restore에 남기지 않는다.
6. 재작업 시 원본 파일과 양손/발 접촉 및 전환 영상부터 비교한다. 기존 유효한 운반/투척과 외형은 보호한다.

다른 작업의 편집기 사용을 조율해 저장 후 정상 종료 상태에서만 빌드/자산 저장했다. 최종 검증 후 해당 채팅에 재실행 가능함을 알렸다. 다른 실작업이 진행 중이므로 컴퓨터 종료 조건은 충족하지 않는다.


## 2026-10-24 런타임 응답 시간·정렬 정책 갱신

사용자 요청: 집기·내려놓기·던지기를 0.5~1초 내 완료하고, 운반 중 충돌 해제 정책에 맞춰 집기 실패를 줄인다. 위 2026-10-17의 정렬 경로 충돌 검사·1배속 재생 기록은 당시 구현이다. 현재는 DT_CarrySettings의 PickupActionSeconds / PlaceActionSeconds / ThrowActionSeconds(각 0.75초)로 전체 클립을 재생한다. 가구 정렬은 목표 시간의 20% 동안 진행하며 승인 직후 NoCollision이다. 정렬 경로 및 정렬 후 접촉 시야 검사는 제거하고 최초 무게·거리·시야 검사는 유지한다. 내려놓기·투척 안전 검사는 유지한다.

원본 blend/FBX, 본·손가락 키, 그립 위치, 몽타주 Notify 및 리소스 참조는 변경하지 않았다. 전체 행동 완료를 애니메이션 평가 후 처리해 지연된 해제 알림을 먼저 처리한다. 최종 빌드와 운반·물리 자동 검사 4개, 렌더링 검토 맵의 정상60FPS/넘어진30FPS 각 50개 흐름 검사 통과. 실제 단계별 PNG 및 시간 측정은 Saved/CarryResponsive20261024/Play07, Play08Tilted30. 손 근접 전 프레임 시각 검수나 원본 재제작 완료로 보고하지 않는다. 상세는 docs/hold-and-throw.md의 2026-10-24 절을 따른다.
