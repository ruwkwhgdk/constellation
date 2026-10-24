# 별 획득 연출 · 추가 5종 제작

## 2026-10-19 Unreal 자산 전달 완료 / 이벤트 연결은 별도

전달 결과: 추가 5종을 `/Game/Constellation/Characters/Heroine/GamePilot/Interaction/AS_Star_{Inspect,Surprise,Absorb,RecoverChest,PalmConfused}` 및 대응 `AM_Star_*`에 저장했다. DefaultSlot, 30fps, 원본 길이 유지, root motion/force root lock 비활성, 개별 Montage blend in/out 0.15초다. Surprise 기존 눈썹·입 표정 커브를 독립 클립 시간으로 옮겼다. 기존 Reach AS/AM 해시는 동일하다.

별도 엔진 프로세스 exit0 재로드 검사: 44,086개 본 변환, 최대 위치 차이 0.002106cm·회전 차이 0.001691도. Inspect→Reach→Surprise→Absorb→RecoverChest→PalmConfused 경계는 최대 위치 0.000308cm·회전 0.000198도다. 승인 보정본과 본 자세 전달이 일치함을 확인했다. `verified.json`, `reach_preserved.json` 참조.

실제 저장 AnimSequence를 heroine SkeletalMeshComponent에서 재생하고 297개 시점의 전신/손 근접 캡처를 수집했다. `UnrealApply01/Frames03`가 유효 결과이며 Frames/Frames02는 기본 자세/과노출 캡처 실패로 제외한다. 최종 영상은 `UnrealApply01/Delivery`에 저장한다. 이 검수는 에디터 검수 월드의 시퀀스 재생이며 PIE 이벤트·VFX·카메라·최종 게임 Idle 연결 및 개별 몽타주의 런타임 블렌드 검증은 수행하지 않았다. 게임 맵/연출 그래프는 수정하지 않았다.

사용자가 Fingers01 보정본으로 추가 5종의 Unreal 반영과 기존 Reach 연결 검수를 승인했다. `StarSequence01/UnrealApply01`에 승인본 내보내기·저장·재로드 검사·실제 엔진 영상 스크립트를 준비했다. Inspect/Surprise/Absorb는 Wrist02, RecoverChest/PalmConfused는 Fingers01을 사용한다. 기존 `AS_ReachTouch_Right`는 보존한다. 엔진 완료 여부는 이 폴더의 `imported.json`, `verified.json`, `capture_manifest.json` 및 납품 기록으로 판단하며 스크립트 준비만으로 완료라고 하지 않는다.

관절·손가락 검수는 프로젝트 `AGENTS.md`의 최우선 품질 게이트를 따른다. 승인된 자연스러운 원본 기준, 팔꿈치–전완–손바닥과 각 손가락 연결, 접근·유지·회수·경계 중간, 엔진 적용 후 근접 재검사를 필수로 한다.

## 손가락 보정 검수 후보 — Fingers01

2026-10-19 사용자 지적에 따라 RecoverChest·PalmConfused의 손가락을 보정했다. 최신 두 Action은 외부 검수 루트 `StarSequence01/FingerCorrection01/Heroine_Star_Fingers01.blend`의 `Star_RecoverChest_Fingers01`, `Star_PalmConfused_Fingers01`이다. 나머지 Action은 Wrist02를 유지한다. 승인된 `ReachTouch_SourceAudit/Heroine_Mixamo_ReachingOut_02.blend`의 첫 프레임 손가락 회전을 기준으로 과한 벌어짐을 줄였다. 손가락 30본 회전만 변경했으며 팔·손목·몸동작은 그대로다. Recover 시작과 Palm 종료의 기존 자세를 보존하고 두 동작 사이에 같은 보정 강도를 사용했다.

저장 재열기 120fps 검사에서 비손가락 본 행렬 변화 0, 연결 최대 성분 오차 4.2e-7이다. 정점·UV·웨이트·697개 모프·94본 바인드 데이터는 Wrist02와 동일하다. 정확한 입력 SHA를 확인해 기존 전체 audit/snapshot을 재사용했고 별도 모델 해시 비교를 수행했다. 정면·측면 핵심 자세 및 근접 전후 영상은 `FingerCorrection01/Delivery/review.html`에 저장한다. **사용자 영상 승인 전 Unreal 반영 금지.** 수치 연속성만으로 손 모양 품질을 통과시키지 말고 엄지 간격·각 손가락 마디·중간 자세를 근접 확인한다.

## 손목·전완 보정 검수 후보 — Wrist02

사용자가 가슴 확인·손바닥 관찰 및 놀람·흡수의 손목 보정을 승인했다. 외부 검수 루트 `StarSequence01/WristCorrection01/Heroine_Star_Wrist02.blend`의 `Star_{Surprise,Absorb,RecoverChest,PalmConfused}_Wrist02`가 새 검수 후보다. 기존 파일은 유지한다. `Star_Before_*_Wrist02`는 전후 비교용 수정 전 Action이며 납품 대상으로 혼동하지 않는다. Inspect는 동일 파일의 `Star_Inspect_Wrist02`로 보존하되 이번 수정 대상이 아니다.

가슴 확인은 손 위치·팔꿈치 pole을 재조정하고 전완 축 회전과 손 방향을 함께 계산했다. 손바닥 관찰은 전완 회전을 함께 사용하고 수정된 가슴 확인 끝 자세에서 연결했다. 놀람·흡수는 양손 굽힘을 완화했다. 초기 Wrist01은 손 위치가 낮아 Wrist02로 대체했으며 유지 후보가 아니다.

120fps 저장 재열기 검사에서 오른손 최대 전완–손바닥 축 각도는 Surprise 29.8°, Absorb 20.0°, RecoverChest 20.0°, PalmConfused 24.6°다. 왼손은 각각 25.6°, 20.0°, 20.0°, 20.0°다. 각도 수치만으로 자연스러움 합격을 판정하지 않는다. `motion_audit02.json`에 팔꿈치·분기 연결·회전 변화·발 위치 기록을 저장했다. 팔·손·손가락 부모 기준 위치 오차 약 1e-6m 이내, 내부 세 경계 행렬 최대 성분 차이 약 1.3e-6 이내다.

`reach_boundary_detailed.json`에서 Surprise 시작이 승인 Reach 끝과 약 1e-6 이내임을 확인했다. PalmConfused 끝은 기존 후보의 끝을 약 7.2e-7 이내로 유지했다(`end_pose_preserved.json`). 기존 후보의 종료 자세 자체는 승인 Reach 시작의 전체 월드 자세와 같지 않으며, 실제 게임 Idle 연결은 미검증이다. 이를 이번 수정으로 해결했다고 보고하지 않는다.

`model_data_compare02.json`은 정점·위상·UV·웨이트·모프·바인드 데이터의 정확 일치를 확인했다. 전후 비교 영상은 `WristCorrection01/Delivery/review.html`에서 검수한다. **사용자 영상 승인 전 Unreal 반영 금지.** 기존 문서 하단의 Candidate04/Preview02는 수정 전 비교 기준이다.

## 손목 재검사: 현재 후보 수정 필요

사용자 지적 후 `StarSequence01/HandJointAudit01/review.html`에 6종(새 5종 + 승인 Reach) 재검사 기록을 저장했다. 가슴 확인의 오른손 전완–손바닥 축 굽힘은 최대 112.1°, 손바닥 관찰은 시작 107.9° 및 시작 연결 이후 최대 68.8°로, 현재 보정본은 수정 필요하다. 이 수치는 기하학적 측정이며 의학적 가동범위 기준이 아니다.

손바닥 월드 방향을 독립 지정하면서 전완 정렬을 제한하지 않은 보정이 원인이다. 이전의 quaternion 연속성·경계 자세·본 위치 검사를 손목 자세 품질 판정으로 사용한 것은 부족했다. 놀람/흡수의 약 43.7° 굽힘은 Reacting 원본에서 승계했지만 긴장 완화도 검토한다. Reach/Inspect에서는 같은 큰 꺾임을 발견하지 않았다.

부모 기준 관절 위치는 최대 약 1.03e-6m 오차이고 기존 모델/웨이트/바인드 비교는 동일했다. 연결 단절보다 자세 보정 문제이며, 데이터 일치가 외형 합격은 아니다. 다음 수정은 팔꿈치·전완·손목을 함께 정렬하고 양손 근접 영상에서 중간 자세까지 확인한다. **새 5종은 수정·사용자 재검수 전 언리얼에 반영하지 않는다.** 이번 실행은 진단만 했으며 후보 .blend는 변경하지 않았다.

2026-10-18 사용자 제작 승인. 첫 제작은 기존 Reach 끝에서 이어지는 Surprise. 이어서 Absorb, RecoverChest, PalmConfused, Inspect를 제작한다. **새 5종의 언리얼 반영은 사용자 검수 이후**다.

## 유지 기준
- 승인 캐릭터: 외부 검수 루트 `ReachTouch_SourceAudit/Heroine_Mixamo_ReachingOut_02.blend`.
- 기존 Reach 4초/30fps와 언리얼 `Interaction/AS_ReachTouch_Right`, `AM_ReachTouch_Right`를 보존한다.
- 원본 예제에서 실제 움직임을 가져오며, 새 자세의 단순 보간만으로 원본 기반 제작이라고 부르지 않는다. 원본 파일·사용 구간·변경을 기록한다.
- Surprise는 Reach 마지막 키의 실제 본 자세에서 시작. 작은 놀람과 오른손 회수, 제자리, 도약/과한 후퇴 제외.
- Absorb는 가슴 빛을 가리지 않는 움츠림. RecoverChest는 턱이 아닌 가슴 확인, 페이드인0.8초 뒤에도 주요 동작 유지. PalmConfused는 손바닥을 얼굴 방향으로 보고 별 위치 확인 후 게임 Idle로 복귀. Inspect는 양손을 몸 가까이 두고 별을 살펴 Reach 시작으로 연결.
- 1.2/2/2/3/2초는 제안이며 원본의 자연스러운 템포가 우선이다.

## 검수와 납품
1. 원본 예제를 확보하고 원시 마네킹의 움직임·관절 방향을 확인한다.
2. 유지 원본을 복사한 별도 후보에서 리타기팅한다. 동일 소스의 기존 audit/snapshot과 SHA를 대조하고 저장 후 재검사한다.
3. 시작 연결·최대 변형·끝 연결, 중간 프레임, 손목·팔꿈치·손바닥 방향, 발 접지, 의상 간섭을 검사한다.
4. 정상 속도와 느린 비교 영상, 원본/캐릭터 비교, 정면/측면을 제공한다. 확정 카메라 정보가 확보되는 범위에서 구도 검수도 추가한다. 미검증은 구분한다.
5. 사용자 검수 전 새 자산·맵·연출 그래프를 언리얼에 적용하지 않는다. VFX 제작은 범위 밖이다.

## 현재 검수 후보 (2026-10-18)

검수 루트는 외부 시각화 루트의 `StarSequence01`이다. `Delivery/review.html`에서 사용자 검수 후에만 새 5종을 언리얼에 반영한다. 기존 Reach 에셋은 변경하지 않았다.

| 동작 | 저장본 / Action | 프레임·시간 | 원본과 보정 |
|---|---|---|---|
| Surprise | `Heroine_StarSurprise_Candidate04.blend` / `Star_Surprise_Candidate04` | 1–49, 1.60초 | Mixamo Reacting 17–49프레임 좌우 반전, 연속 시간 보간. Reach 끝에서 0.45초 연결, 고개 회전 축소, 하체 고정 |
| Inspect | `Heroine_StarFour_Preview02.blend` / `Star_Inspect_Candidate02` | 1–99, 3.27초 | Looking Down 상체 움직임 축소, Reach 시작 자세로 복귀 |
| Absorb | 위 파일 / `Star_Absorb_Candidate02` | 1–75, 2.47초 | Reacting 끝 팔 자세 + Looking Down 상체. 가슴 중앙 확보 |
| RecoverChest | 위 파일 / `Star_RecoverChest_Candidate02` | 1–90, 2.97초 | 원본 상체 위에 오른팔 2본 접촉 보정. 목이 아닌 가슴 위치, 0.8초 이후 확인 자세 유지 |
| PalmConfused | 위 파일 / `Star_PalmConfused_Preview02` | 1–156, 5.17초 | Look Around 1–140프레임 좌우 반전. 얼굴 방향 손바닥·열린 손·손목 연결 보정, 중립 상체 복귀 |

모두 30fps. 시간은 키 간 길이이며 동영상은 마지막 표시 프레임 때문에 약 1/30초 더 길 수 있다. 제안 시간보다 긴 동작은 원본 템포를 우선한 검수 후보이며 사용자 확인 전 최종 게임 길이로 확정하지 않는다.

원본 FBX와 SHA는 `Sources/catalog.json`, `catalog_look.json`, `catalog_down.json`에 기록했다. `Surprised`는 조사했지만 최종 제작에는 사용하지 않았다. 원본 준비 동작을 그대로 연결한 Surprise02는 손이 내려갔다 다시 올라와 제외했다. 최종04는 원본 반응 구간부터 사용한다.

### 검사 기록
- `motion_checks_final.json`: 최종 5종 120fps 샘플 검사. 발 본 위치 변화 최대 약 1.23e-7 m. 팔꿈치·회전 변화 수치와 최악 프레임을 기록했다.
- `seam_checks.json`: Inspect→Reach→Surprise→Absorb→RecoverChest→PalmConfused의 5개 경계에서 전 본 월드 행렬 최대 성분 차이 1.44e-6 미만. 이는 자세 연속성 검사이며 속도 연속성 보증이 아니다.
- `final_data_equivalence.json`: 승인 Reach 원본과 최종 파일의 정점·위상·UV·웨이트·697개 모프·94본 바인드 데이터가 정확히 동일함을 저장 재열기 후 비교했다.
- lida audit/snapshot/compare는 Surprise02와 Four Preview에서 완료했고 비교 일치. 이후의 동작 전용 수정본04/Preview02는 위 정확 데이터 비교로 같은 모델 데이터임을 확인했다. 오래된 `motion_checks.json`은 폐기 후보도 포함하므로 최종 결과로 사용하지 않는다.
- 손바닥 관찰의 가슴 자세→원본 자세 연결에서 움직이는 목표가 180도 최단 회전 경계를 넘어 손목 경로가 바뀌는 오류를 발견했다. 시작/끝 방향을 고정한 브리지로 수정. `transition_fix.json`, `palm_diagnostic.json` 참고.
- 정면·측면 영상은 실제 저장본의 렌더로 제작했다. 저장 오류로 잘린 프레임은 재렌더하고 `frame_scan.json` 및 영상 프레임 수 검사로 확인한다.

### 다음 단계 / 미검증
- 사용자가 검수한 뒤에만 Unreal AnimSequence·Montage 및 이벤트 연결을 제작한다. 아직 새 5종의 언리얼 임포트·PIE·최종 게임 Idle 블렌드는 실행하지 않았다.
- 현재 마지막 자세는 승인 Reach 중립 상체를 사용한다. 게임 Idle 연결과 확정 카메라의 시선/별 위치, VFX 접촉은 별도 확인한다.
- Surprise 얼굴 표현은 기존 모프의 작은 값(눈썹0.18/입0.10)을 검수 타임라인에 사용했다. Unreal 납품 시 독립 Surprise 클립 시간으로 얼굴 커브를 이동·전달해야 한다.
- 발 본 고정과 제한된 정면·측면 검수는 전신 메시 충돌/성능 합격을 뜻하지 않는다.
- 이번 실행의 중간 후보 5개는 `RetiredDrafts_20261018.zip`에 CRC와 SHA256을 검증한 후 보관했다. 원본·최종 후보·프로젝트 Intermediate는 삭제하지 않았다.
