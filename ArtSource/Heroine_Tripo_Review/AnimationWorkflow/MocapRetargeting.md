# 일어서기 의상 전체 구간 반영 — 2026-10-15

현재 GetUp 편집 시작점은 외부 검수 루트 `Klian_GarmentFull01/Heroine_GarmentFull.blend`다. 본동작은 승인된 PalmsDown과 동일하며, 기존 `Klian_GarmentKeyPoses01/02/03`의 의상 승인 내용을 전체 구간에 연결했다. `CURRENT_GETUP.json`의 garment_delivery와 해당 폴더 status.json/review.html을 함께 확인한다.

- 초기 1초·1.5초 보정 두 개를 추가해 기존 ProneHold 모프 해제와 새 보정의 공백을 줄였다. 총 7개 새 모프는 시작/끝에서 0이다. 기존 676개 게임 모프와 60개 재질 슬롯을 보존했다.
- 가디건 경계는 형상만의 문제가 아니었다. 기존 아틀라스의 회색/피부색 띠를 제거하는 지역 샘플링 보정도 전달했다. 의상 세 재질만 UV2=donor UV, UV3.x=mask로 포장한다. 얼굴의 UV2/UV3 인코딩을 덮어쓰지 않는다. 내부 치마 패널의 mask는 0이다.
- `Materials/LockerGarment`의 새 재질은 기존 환경광 재질 그래프의 Tex0 샘플만 국소 혼합한다. `Cloth_Klian_Lift_CardiganOverlap`으로 모프와 재질 효과를 함께 조절한다. 시작·종료 원단은 기존 그래프 그대로다.
- 애니메이션의 add_curve flags=4는 Editable 플래그다. 모프/재질 타입으로 해석하지 않는다. `AnimationLibrary.set_curve_meta_data_morph_target`/`set_curve_meta_data_material`로 스켈레톤 메타데이터를 명시한다. 재질 플래그는 경계 보정 커브 하나만 켠다.
- 재현: early.py → connect.py → verify_source.py → export.py → apply_engine.py → set_metadata.py/verify_engine.py. 재임포트 전에 열린 편집기의 자산 점유와 변경 내용을 확인한다. apply_engine.py는 초기 전달 스크립트이므로 기존 LockerGarment 자산이 있으면 재실행 전 중복 생성 경로를 검토한다. before/는 초기 게임 자산 백업이다.
- 검증: 원본 346프레임/94본 및 기존 모프 정점 변화 0; 게임 저장본 16,356개 본 위치 최대 오차 0.00426cm. 실제 학교 PIE에서 약6.33초 대기/드리프트0/일어서기/입력 이동83.29cm, 7개 커브와 재질 활성화 및 끝0 확인. 원본 173프레임, 엔진 의상 후방·측면15시점 검수.
- 학교 저각도 SceneCapture는 노출 부족으로 의상 검수 증거에서 제외했다. 실제 학교 뷰포트 영상과 별도 조명 검수 씬을 구분한다. 단독 SkeletalMeshActor의 루트 처리 화면을 게임 캐릭터 접지 검사로 해석하지 않는다. 패키징 빌드 및 전 삼각형 충돌 증명이 아니다.

---

# 폐교 S0 실제 이벤트 연결 — 2026-10-15

`SchoolOpeningSceneActor`가 실제 플레이어의 `AM_Locker_Event`를 재생한다. 그래프 `/Game/SceneDirector/School/DA_S0_Opening`의 Fall → 기존 소녀 이동/Wait → Recover → GetUp 길이+0.55초 Wait → PrepareHandoff → GameplayReturn 순서다. ProneHold는 이벤트가 Recover를 보낼 때까지 반복한다. 기존 대화·선택지·소녀 이동은 유지했다.

- `AS_Locker_GetUp`의 키와 승인 포즈는 그대로다. Enable Root Motion=true, Root Lock=Anim First Frame, **Use Normalized Root Motion Scale=false**를 유지한다. 이 리그의 root scale=100에서 기본 정규화 옵션은 91cm 이동을 100배로 만들었다. 단위가 맞는지 반드시 실제 Character 캡슐 이동으로 확인한다.
- 시작은 바닥 트레이스와 메시 상대 Z로 배치하고, 일어서기 후 0.35초 블렌딩한다. PrepareHandoff는 실제 종점을 넘긴다. 과거 고정 ExitTransform으로 순간이동하지 않는다.
- 이동·충돌·애니메이션 갱신·루트모션 모드는 이벤트 동안만 변경하고 복구한다. 취소 시 시작 전 위치로 돌아간다. 표시·입력 복구는 SceneDirector가 담당한다.
- 실제 AbandonedSchool PIE: 두 조사 순서, 약6.6초 대기, GetUp 완료, 카메라 복귀, Enhanced Input `IA_Move` 주입 이동, 대기 중 취소까지 통과했다. 대기 골반 이동0cm, 루트 이동91.01593cm, 인계 시 캡슐 위치 튐0cm. 검사 프로세스 exit0.
- 근거: 외부 검수 루트 `SchoolLockerIntegration/result.json`, `game2.log`, `implementation.txt`. 최종 화면 및 재검사는 `final_result.json`/`review.html`을 확인한다. 패키징 빌드 및 모든 의상 정점 충돌 검증으로 확대 해석하지 않는다.
- Python에서 이벤트 GUID는 `GuidLibrary.equal_equal_guid_guid`로 비교한다. 일반 객체 비교로 부모 연결이 누락될 수 있다. 변경한 그래프는 저장 전에 컴파일하고 실제 분기 두 개를 재생한다.

이 아래는 단계별 제작 이력이다. "학교 이벤트 미연결" 및 과거 종료 예외 기록은 당시 검사 범위이며 위 최신 결과와 구분한다.
# 언리얼 정식 자산 적용 — 2026-10-15

사용자가 Klian_Heroine04_PalmsDown을 승인하고 언리얼 추가·적용을 요청했다. 기존 `/Game/Constellation/Characters/Heroine/GamePilot/Locker/AS_Locker_GetUp`에 승인본을 적용했으며 `AM_Locker_Event`의 GetUp 섹션도 이 정식 자산을 참조한다. `_Klian` 자산은 이전 검수본이고 새 수정의 적용 대상은 정식 `AS_Locker_GetUp`이다.

수정 전 GetUp과 몽타주는 외부 `Klian_Heroine04_PalmsDown/UnrealApply/*_before.uasset`에 보관했다. 애니메이션 원본은 `Heroine_Klian_PalmsDown.blend` 그대로다. 재현용 `UnrealApply/apply.py`, `verify.py`, `test_runtime.py`와 결과 JSON을 함께 유지한다. 0·5·15초 대기 검사 결과는 `UnrealApply/RuntimeMontage/result.json`에 기록한다. 원래 폐교 카메라·대화 그래프를 이번 적용에서 변경하지 않았다.

# 최신 국소 수정 — 손바닥 방향, 2026-10-15

현재 편집 원본: 외부 검수 루트 `Klian_Heroine04_PalmsDown/Heroine_Klian_PalmsDown.blend`, Action `Heroine_Klian_PalmsDown`. 기존 03은 연결 자세 제작 이력이다.

- 사용자 요청: 첫 0~1초에 손이 위를 향하는 회전을 없애고 손바닥이 바닥을 향하게 한다.
- 시작 대기 자세의 양손 월드 방향을 0~1초에 유지한다. 1~1.75초는 부드럽게 원래 밀어 올리기 손 방향으로 연결한다. 바닥 침범 방지를 위해 필요한 팔 체인 위치만 보정한다.
- 몸통·다리 본 위치는 03과 동일. 1.75초 이후 전체 본 위치 차이 최대 0.000024cm(수치 오차).
- 120Hz 691개 샘플: 양손 바닥 침범 없음. 30Hz 게임 키로 재평가한 693개 샘플에서 최저 여유 왼손 1.400mm, 오른손 1.253mm.
- 첫 1초 양손 손등 법선의 위쪽 성분 최소 0.9999966. 바닥 높이뿐 아니라 손바닥 방향을 함께 검사했다. 이 법선은 손목–중지 기저와 검지–소지 기저로 계산하고, 처음 확인된 손등 방향으로 부호를 맞췄다.
- 검수 영상: `before_after.mp4`(0.5배속 전후 비교), `palms_down_full.mp4`(정상 속도 전체). 이미지에서 손바닥이 아래인지 확인한 뒤 수치를 해석한다. 법선 수치만으로 해부학적 방향을 추정하지 않는다.
- 교훈: 이전 손 바닥 침범 보정은 손 방향을 보존했기 때문에 기울어진 손을 유지했다. 접촉 검사에는 **침범·들뜸·미끄러짐·손바닥 방향**을 따로 기록한다. 어느 한 항목 통과로 모두 통과라고 하지 않는다.
- 기존 게임 GetUp 자산과 몽타주 연결을 갱신했다. 저장/재읽기 결과는 `Klian_Heroine04_PalmsDown/runtime_delivery.json`. 이번 변경에서 PIE 전체 몽타주 재생 검사를 다시 수행하지 않았다. 이전 03의 PIE 통과를 04에서 새로 수행한 결과로 보고하지 않는다.

# 최신 유지 상태 — 기존 대기 연결 승인 반영

2026-10-14 사용자가 기존 대기 자세에서 이어지도록 GetUp 변경을 추가 승인했다. 현재 원본은 외부 검수 루트의 `Klian_Heroine03_HoldTransition/Heroine_Klian_FromExistingHold.blend`이며, Action은 `Heroine_Klian_FromExistingHold`다. 아래 02 기록은 손 침범 수정 단계의 이력이다.

- 첫 1초: 기존 게임 ProneHold와 정확히 같은 본 자세에서 승인된 Klian 시작으로 연결. 기존 대기 의상 모프를 1초 동안 해제한다.
- 이후: 승인 동작 유지. 기존 게임 위치에 맞춘 일정 XY 이동만 포함한다.
- 게임 시퀀스: `/Game/Constellation/Characters/Heroine/GamePilot/Locker/AS_Locker_GetUp_Klian`.
- `AM_Locker_Event`의 GetUp을 새 시퀀스로 연결했다. 기존 ExitFall/ProneHold 자산은 유지한다.
- 소스 60Hz 5.75초. 게임은 기존 샘플러에 맞춰 30Hz 5.766667초이며 끝 자세가 약 16.7ms 늘어난다. 이 전달 방식을 바꿀 때 압축 sampler rate/프레임 경계를 반드시 함께 검사한다.
- 60Hz 원본: 691개 120Hz 샘플에서 손 최저 여유 1.358/1.425mm. 게임 30Hz 키를 Blender에서 다시 평가한 693개 샘플: 0.954/1.155mm. 엔진 압축 후 메시 전정점 검사는 아니다.
- 저장 후 별도 엔진 프로세스에서 16,356개 본 위치를 읽었다. 최대 오차 약 0.00427cm, 기존 대기→새 시작 최대 오차 약 0.000135cm. 프로세스 정상 종료 확인.
- 실제 PIE 검증과 캡처는 `Klian_Heroine03_HoldTransition/RuntimeMontage/result.json` 및 PNG를 확인한다. all_pass가 true일 때만 해당 검사 범위를 통과로 보고한다.
- 현재 `DA_S0_Opening`을 읽었을 때 직접 Animation 자산 참조는 없었다. 새 몽타주 재생 테스트를 실제 학교 연출·카메라·캡슐 전달 완료로 혼동하지 않는다.
- 60Hz 자산에서 AnimCompressionTypes.cpp:993 비정수 sample-frame assertion이 발생했다. 실패 자산은 외부에 보존하고 기존 30Hz 방식으로 새로 생성한 후 정상 종료를 확인했다. JSON 작성이나 raw 본 readback 성공만으로 압축까지 통과했다고 주장하지 않는다.

# 모캡 원본에서 게임 애니메이션까지 — 유지 절차

최종 갱신: 2026-10-14. 프로젝트 AGENTS.md가 요구하는 AnimationWorkflow/SKILL.md와 함께 읽는다.

## 현재 소스와 승인 범위

- 검수 루트: `C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b`.
- 승인된 원본 마네킹: `Klian_KneeSupport01`. 캐릭터 적용 승인본: `Klian_Heroine01/Heroine_Klian_Contact.blend`.
- 최신 손 접지 수정: `Klian_Heroine02_HandFloor/Heroine_Klian_HandFloor.blend`, Action `Heroine_Klian_HandFloor`, 94본, 60fps, 1–346프레임(5.75초).
- 이번 사용자 승인: 손 바닥 침범만 수정하여 게임 전달. 기존 무릎 지지, 발, 체형, 템포는 보존. 이 파일의 타 동작·의상까지 포괄적으로 승인됐다고 해석하지 않는다.
- 게임 반영 상태는 같은 검수 폴더의 `runtime_delivery.json`을 확인한다. 파일이 없으면 게임 반영 완료로 취급하지 않는다.
- 과거 UniMate/절차적 GetUp 및 LockerAnimation/status.json의 오래된 단계는 이 동작의 편집 시작점이 아니다. 다른 모션의 유지 소스는 별도 CURRENT 기록을 확인한다.

## 제작 과정에서 확인한 실패와 전환

초기 절차적 동작은 핵심 포즈만 맞추면서 관절 굽힘 방향, 체중 이동, 중간 접촉을 놓쳤다. 손목을 임의로 고정하거나 발/손 타깃만 맞추면 팔·다리와 연결이 부자연스러워졌다. UniMate의 자유 생성에서는 시작 자세와 전신 연결이 요구와 달랐다. 프롬프트에 자세를 적는 것과 실제 시작·중간·끝 조건을 고정하는 것은 다르며, 고정 결과도 원시 스켈레톤으로 확인해야 한다.

실제 사람의 동작(Physitrack)을 비교 기준으로 삼고, Klian과 CMU 원본을 비교한 뒤 사용자가 Klian을 선택했다. 원본 마네킹에서 손으로 무릎을 짚는 부분을 보정하고 영상을 승인받은 뒤 캐릭터로 옮겼다. 캐릭터 적용 후 체형 차이에 따른 손·무릎 접촉과 발 지지를 국소 보정했다. 이후 사용자가 시작/밀어 올리기 손 바닥 침범을 발견했다. 기존 검사가 무릎 접촉과 발에 치우쳐 양손 전체 표면의 바닥 침범을 누락했기 때문이다. 검사 범위 누락이며 리그 오류로 단정할 근거가 아니다.

## 재사용할 단계별 절차

1. **요구와 접촉 표 작성:** 시작, 이동, 지지, 해제, 끝의 지지 부위와 이벤트 대기/루프 조건을 적는다. 바닥에 닿는 손바닥·손가락·무릎·발끝·뒤꿈치를 좌우로 나눠 기록한다.
2. **원본 검수:** 실제 속도와 느린 속도로 원본 스켈레톤을 측면·전면·사선에서 비교한다. 사용자가 원본 확인을 요청했다면 캐릭터 적용 전에 승인받는다. 생성 결과에 조건이 실제로 적용됐는지 프레임으로 검증한다.
3. **원본 보정:** 원본 관절 관계와 무게 이동을 유지한다. 핵심 자세와 연결 동작은 각각 검수한다. 손목/팔꿈치 굽힘, 발목 방향, 지지면 위 몸통 이동을 함께 본다.
4. **리타기팅:** 원본/대상 rest, 축, 스케일, 본 계층을 기록한다. append/import 직후 depsgraph를 평가한 뒤 matrix_world를 읽는다. FBX bone tail은 실제 자식 관절 방향과 다를 수 있으므로 shoulder–elbow–wrist 같은 실제 관절 위치로 체인을 계산한다. 회전값을 그대로 복사하지 않는다.
5. **캐릭터 접촉 보정:** 실제 변형 메시를 기준으로 지지점을 맞춘다. 이 캐릭터는 palm 및 twist 본 웨이트가 있으므로 hand/thigh 그룹 하나만 선택하면 실제 표면 일부가 빠진다. 손목 위치를 손바닥 접촉으로 보고하지 않는다. 옷소매와 손 표면을 구별한다. 팔꿈치 pole과 손 방향을 연속적으로 유지하고 진입/지지/해제 구간을 부드럽게 연결한다.
6. **전 구간 정량 검사:** 120Hz 등 프레임 사이까지 검사한다. 침범 최저점뿐 아니라 지지 중 들뜸, XY 미끄러짐, 관절 굽힘/회전 연속성, 시작/끝/루프 이음새를 검사한다. nearest-point 하나의 거리만으로 손바닥 전체 접촉이나 전신 충돌 통과를 주장하지 않는다. 원본 끝의 점프도 별도로 확인한다.
7. **영상 검사:** 전체 동작 정상 속도와 접촉 확대 느린 영상으로 확인한다. 수치가 통과해도 기계적인 템포/역관절/부유가 보이면 통과 처리하지 않는다. 원본과 대상 비교 시 카메라·스케일·시간을 맞춘다.
8. **게임 전달:** 기존 94본 스켈레톤의 검증된 좌표 변환을 사용한다. 파일명만 같은 새 스켈레톤을 만들지 않는다. 저장 후 별도 엔진 프로세스로 길이, 스켈레톤, 실제 본 포즈를 다시 읽는다. 모프 커브는 구 동작에서 무조건 복사하지 않는다.
9. **실제 연결:** 독립 시퀀스, 몽타주 연결, 대기 루프, 학교 이벤트, 캡슐/루트 전달, 취소와 조작 복귀는 서로 다른 검증이다. 기존 Fall/ProneHold와 새 GetUp의 시작 자세가 다르면 통과로 숨기지 않는다. 기존 연출을 크게 바꿔야 한다면 비교 자료와 함께 확인받는다.
10. **완료 보고:** 수정본 경로, 검증 샘플 수/범위, 실제 게임 변경 자산, 미검증 범위를 함께 기록한다. exit 0, 머리 높이, 0/5/15초 대기 성공만으로 시각 품질이 검증됐다고 하지 않는다.

## 이번 손 바닥 침범 검사의 회귀 기준

- 좌우 손/손바닥/모든 손가락 웨이트 합 >0.5인 정점 각각 998개를 실제 변형 후 검사했다.
- 수정 전 샘플 최대 침범 약 64mm. 수정 후 전 구간 691개 시점 최소 여유: 왼손 1.358mm, 오른손 1.425mm.
- 발 최소 여유: 왼발 0.137mm, 오른발 0.275mm. 기존 결과 유지.
- 비수정 본과 214프레임 이후 팔 자세의 행렬 최대 차이 약 6.56e-7(수치 오차).
- 기록: `baseline_hands.json`, `corrections.json`, `dense_audit.json`, `summary.json`, `hand_floor_fixed.mp4`.
- 손 방향을 유지한 팔 체인 보정이다. 전체 의상 관통, 손바닥 전체 하중, 실제 학교 바닥과의 접촉까지 이 수치로 검증됐다고 확대 해석하지 않는다.

## 출처와 권리

- Klian, Getting Up Animation: https://www.fab.com/listings/69dae222-05e9-4065-9030-45887986cdec — CC BY 4.0. Rokoko 모캡 원본 기반. 손 무릎 지지, 리타기팅, 접지/끝 프레임 수정 포함. 배포 시 제작자·원본 링크·라이선스 링크·변경 사실을 함께 표시한다.
- 라이선스: https://creativecommons.org/licenses/by/4.0/
- Physitrack: https://na.physitrack.com/home-exercise-video/getting-up-from-the-floor-variation-without-support — 동작 관찰 참고. 영상을 재배포하거나 모캡 원본으로 사용하지 않았다.

## 게임 전달 현황 — 손 수정본

`/Game/Constellation/Characters/Heroine/GamePilot/Locker/AS_Locker_GetUp_Klian`으로 별도 저장했다. 기존 Fall/ProneHold/GetUp/AM_Locker_Event는 변경하지 않았다. 기존 대기와 새 시작은 팔다리 자세 및 위치가 다르다. `seam_comparison.jpg`는 골반 XY를 맞춰 자세 차이를 보여 준다. 현재 자산 레지스트리에서 AM_Locker_Event referencers는 빈 목록이다(동적 문자열 참조 부재까지 증명하지는 않는다). 실제 학교 이벤트 연결 완료로 보고하지 않는다. 이 연결을 해결하려면 기존 넘어짐 끝·대기·새 시작의 연결 범위에 대한 사용자 결정을 확인한다.

엔진 저장 후 백그라운드 압축에서 AnimCompressionTypes.cpp:993 SampleFrameTime subframe assertion이 발생했다. 학교 자산을 로드하지 않는 독립 재읽기에서도 재현됐으므로 학교 그래프가 원인이라고 단정하지 않는다. 본 포즈 readback과 JSON 저장만으로 게임 자산이 안전하다고 판정하지 않으며 정상 프로세스 종료까지 확인한다. 기존 프로젝트 30Hz 전달 경로로 다시 검사한다.


최종 PIE 검사: 0·5·15초 대기 및 기립 12개 검사 통과, 중간 자세 PNG를 확인했다. 검수용 에디터 종료 단계에서 OS 코드 -1073741819가 반환됐다. 재생 중 실패는 기록되지 않았고 종료 로그는 Exiting까지 도달했으나, 종료 예외 원인은 미확정이다. 별도 저장/재읽기 커맨드릿은 exit 0이었다. `CURRENT_GETUP.json`에 두 결과를 분리 기록했다. 이 예외를 성공 코드로 바꾸거나 숨기지 않는다.

2026-10-15 정식 적용 검증: 별도 엔진 재읽기 exit 0, 16,356 본 위치 검사 최대 오차 약 0.00426cm. 실제 PIE에서 0·5·15초 대기 및 기립 12개 검사 통과. 현재 자산과 프로세스 종료 코드는 CURRENT_GETUP.json에 기록.

