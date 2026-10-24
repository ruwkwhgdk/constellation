# 상태 변경 — 2026-10-18 사용자 반려 / 원본 예제 기반 전환

## 2026-10-18 언리얼 반영 완료

사용자 승인으로 `Heroine_Mixamo_ReachingOut_02.blend`를 언리얼5.8에 추가했다. 아래의 Blender 전용/언리얼 미반영 기록은 이전 단계 상태다.

- AnimSequence: `/Game/Constellation/Characters/Heroine/GamePilot/Interaction/AS_ReachTouch_Right`
- AnimMontage: `/Game/Constellation/Characters/Heroine/GamePilot/Interaction/AM_ReachTouch_Right`, `DefaultSlot`, 0–4초, 재생률1.0. blend in/out 각0.15초, 자동 blend out. 원본 시퀀스는 30fps/121키/4초이며 뻗은 자세에서 끝난다.
- 기존 heroine 스켈레톤과 preview mesh를 사용한다. root motion/force root lock은 비활성. 원본의 첫 수평 위치만 기존 Idle 기준으로 정렬하고 동작 변화는 유지했다.
- 별도 엔진 프로세스에서 저장본을 재로드하여 11,374개 본 변환을 검사했다. 최대 위치 오차0.00059675cm, 회전 오차0.00080489도. 검증 프로세스 exit0. `ReachTouch_SourceAudit/UnrealApply/verified.json` 참조.
- 최초 생성의 존재하지 않는 자산 조회가 로그 Error/exit1을 남겼지만 두 자산은 저장됐다. 이후 재로드 검증은 exit0이며 생성 스크립트도 `does_asset_exist` 검사로 수정했다. 오류 이력을 성공 실행으로 바꾸어 기록하지 않는다.
- 특정 게임 이벤트/입력과 연결하지 않았고 실제 게임 영상 검증은 이번 단계에 포함하지 않았다. 접촉 notify도 아직 없다. 별 획득 연출에 연결할 때 실제 별 위치와 손의 접촉 시점을 검사해 notify/VFX 타이밍을 결정한다. 임시 4.5초 예산에 맞춰 원본을 늘리지 않는다.
- 재현: `UnrealApply/export.py` → `apply.py` → 별도 프로세스 `verify.py`. 다음 편집기 작업 전 `Saved/JumpAcquisition/coordination.txt`의 최신 예약을 확인한다.

### 전달받은 후속 제작 대기 항목

후속 상태: 사용자의 추가 5종 제작 승인 후 Blender 검수 후보를 제작했다. 최신 후보·영상·검사와 언리얼 적용 대기는 [StarSequence.md](StarSequence.md)를 따른다. 아래는 제작 전 전달 기록이다.

점프 능력 획득 연출 채팅에서 2026-10-18 전달받음: Star_Inspect(~2초), Star_Surprise(~1.2초, 우선), Star_Absorb(~2초), Star_RecoverChest(~2초), Star_PalmConfused(~3초). ConfusedIdle은 선택 후순위. 이는 후속 대기 목록이며 이번 반영 작업에서 새 클립을 제작하지 않았다. 완성 Reach를 재제작/덮어쓰지 않는다. 상세 입력은 `ArtSource/JumpAbility/Production/ResourceRequests_v02.txt`와 전달 메시지의 최신 카메라 승인 상태를 함께 참조한다. 완성 클립 연결 때 임시 JumpAcquisitionPose 팔 보정의 중복 적용을 제거하고 Inspect 시간을 별도 확보한다. 맵/카메라는 이 작업에서 수정하지 않았다.

ReachTouch01/04는 손 방향과 동작이 부적절하다는 사용자 피드백으로 **반려·적용 보류**. 유지 승인본으로 사용하지 않는다. 거의100% 도달과 연속 회전 검사만으로 손 방향·손목 정렬·자연스러움을 보장하지 못했다. 문 밀기에서 가져온 hand 회전을 다시 기준으로 삼지 않는다.

새 조사: `ReachTouch_SourceAudit/review.html`. 로그인 후 Mixamo 공식 Reaching Out 원본을 다운로드했다. SHA256 `94D8573FD8F355EFF3AE72996CE91ACCCD7917613D77CFB795C4A627FCF2E81E`, X Bot 포함 FBX Binary, 30fps, 키 감소 없음, 1–121프레임(4초). `Mixamo_ReachingOut_Raw.blend`에 원본을 보존했다.

사용자 최신 승인: **다운로드한 애니메이션 자세 그대로 사용**. 원본의 손 방향·팔꿈치 굽힘·타이밍을 보존하며 이전의 거의100% 신전 요구에 맞추려고 원본을 변형하지 않는다. 캐릭터 비율/리그 차이에 따른 리타기팅과 검수만 진행한다. 현재 캐릭터 후보는 `ReachTouch_SourceAudit/Heroine_Mixamo_ReachingOut_02.blend`, Action `Heroine_Mixamo_ReachingOut_SourcePose`다. 01은 상체 시험본이며 유지 시작점으로 사용하지 않는다. **언리얼 미반영**.

- 전신 원본 자세를 옮겼으며 오른팔 각도는 121개 키에서 원본과 최대 약 0.0001도 차이. 손목→중지 기저 방향도 별도로 대조했다. 체형 차이 때문에 끝점의 절대 위치는 동일하지 않다.
- 팔 손목에는 관절 숫자 회전을 복사하지 않고 손목–중지 기저와 검지–소지 기저가 만드는 해부학적 방향을 사용했다. 실제 정면·측면 이미지로 손가락 방향을 확인했다.
- 원본은 뻗은 자세로 끝난다. 새 복귀/루프를 추가하지 않았다. 키 범위 4초, 마지막 프레임을 포함하는 영상 재생 길이는 약4.03초.
- 별도 저장본에서 120Hz 481개 중간 샘플을 확인했다. 오른팔 상완·전완·손목의 분기당 최대 회전 변화는 약0.402도/1⁄120초. 이는 자연스러움이나 모든 의상 충돌을 증명하지 않는다.
- `Delivery/review.html`에 원본/캐릭터 정면·측면 비교 영상과 검사 범위를 저장했다. `delivery.json`과 `compare.json`, `saved_motion_checks.json`, `Delivery/video_audit.json`을 최종 결과 근거로 사용한다.

Free Interaction Animation의 anim_ReachLever는 목록만 확인한 보조 후보. UniMate README의 keep_frames/keep_joints 기능을 확인했으나 새 생성은 수행하지 않았다. 부적절한 기존 자세를 고정 입력으로 재사용하지 않는다.

아래는 반려된 시안의 제작 기록이다.

---
# 오른손 조심스럽게 뻗기 — 2026-10-18

현재 후보는 외부 검수 루트 `ReachTouch01/Heroine_CautiousRightTouch_04.blend`. 검토 페이지 `ReachTouch01/Delivery/review.html`, 본 트랙 `motion.json`, 검사 기록 `delivery.json`. 원본 모델은 승인 유지본 GateOpen01/Sync05/Main02의 최종 GP_Idle 자세에서 가져왔다.

사용자는 앞의 물체를 오른손으로 조심스럽게 만지는 동작을 요청했다. 최초80% 도달 조건은 최신 **거의100%, 완전히 뻗은 자세** 요청으로 대체됐다. 01/02 및 중단한 렌더는 이전 조건이므로 사용하지 않는다.

4.4초: 0–2.2초 뻗기,2.2–2.9초 끝 자세 유지,2.9–4.4초 거두기. 접촉 목표에서 어깨–손목 거리는 상완+전완 길이의99.9977%다. IK 길이 여유0.01mm로 역꺾임을 피하고, 자유 접근/복귀는 로컬 회전으로 연결한다. 중간에만 약21도 팔꿈치 굽힘을 더해 곧은 팔이 통째로 올라가는 느낌을 줄였다. 상체2도·시선4도의 작은 움직임과 기존 Idle을 사용했다. 발 이동0, 시작/끝 자세 일치.

정면/측면 전체133프레임을 EEVEE 실제 재질로 렌더했다. Workbench의 활성 디버그 텍스처로 정면 눈 색이 잘못 표시될 수 있으므로 최종 영상에는 쓰지 않는다. 측면의 판은 위치 참고용이며 실제 게임 접촉 자산이 아니다. 정면에서는 손을 가리지 않도록 판을 숨겼다.

529개120Hz 중간 자세 검사 및 저장 재열기 snapshot 기록 필드 일치. 전 삼각형 의상 충돌을 증명한 검사는 아니며 최종 표시 검수와 구분한다. 원본 캐릭터 메쉬·웨이트·모프 형상은 유지했다.

이번 단계는 사용자 검토용 동작 제작이다. **언리얼 미반영**. 사용 대상 액터/높이/거리 및 게임 접촉은 후속 적용 단계에서 검증한다. 게임 본 트랙은 기존 좌표 변환과 최초 수평 오프셋 제거 방식으로 저장했고 원본과 게임 Idle의 root scale100을 보존한다.

