# 2026-10-07 검수 작업 공간 이동 안내

Rebuild 제작·검수 자료는 사용자 요청으로 `C:/Users/User/Documents/Constellation_ArtWorkspace/ArtSource/Heroine_Rebuild`로 이동했다. 아래 기록의 `ArtSource/Heroine_Rebuild/...` 참조는 외부 작업 공간 기준으로 읽는다. 기존 프로젝트 경로를 다시 생성하지 않는다.

최신 검토 소스는 외부 경로의 `FaceDefectRepair/R11/Heroine_R11_Review.blend`, FBX는 같은 폴더의 `SK_player_heroine_new_FaceDefectReview.fbx`다. 최신 상태와 미완료 항목은 외부 `CURRENT.md`, `FaceDefectRepair/status.json`, `Migration_20261007/result.json`(외부 작업 공간 루트)을 함께 확인한다. 자동화 스크립트의 하드코딩된 경로 갱신은 후속 작업이며, 실행 전에 반드시 확인한다. 원본 Carry Blend/FBX와 게임 리소스는 프로젝트에 유지한다.

외부 작업 공간은 이 Git 저장소의 푸시 대상이 아니므로 별도 보관이 필요하다. 과거 기록은 아래에 보존한다.

---
name: constellation-character-animation
description: Project Constellation의 여주인공 애니메이션을 기존 게임 모션 기반으로 리타기팅, 폴리싱, 검증하고 언리얼에 전달할 때 사용하는 프로젝트 작업 절차.
---

# Constellation 캐릭터 애니메이션 작업 절차

## 작업 기준

- 캐릭터 키 160cm. 기존 모델의 스타일·비율·얼굴 디테일을 보존한다. 애니메이션 문제를 체형 변경으로 해결하지 않는다.
- 소심하고 조심스러운 캐릭터에 맞는 작은 동작을 지향하되 실제 원본 모션의 관절 관계와 무게 이동을 우선한다. 성격만으로 경직된 팔이나 기계적인 다리 궤적을 만들지 않는다.
- 큰 재작업이나 원본의 장점을 없애는 변경은 적용 전에 구체적인 차이와 이유를 설명한다. 이미 요청받은 국소 보정은 범위 안에서 진행한다.
- 사용자는 자연스러운 보폭을 먼저 정하고 맞는 이동 속도를 제안하는 방식을 선택했다. 기존 게임의 800cm/s 등에 억지로 맞추지 않는다. 게임 이동 코드·ABP·Blend Space 연결 변경은 별도 요청 범위다.

## 현재 작업 시작점

프로젝트 루트 기준 경로:

| 용도 | 현재 기준 |
|---|---|
| 달리기 편집 원본 | `ArtSource/Heroine_Tripo_Review/RunSoft/Heroine_Run_Soft.blend` |
| 달리기 클립 | `/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Run_Soft` |
| 달리기 프리뷰 메시 | `/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview` |
| 달리기 설정 | 30fps, 1.0초, In-place, 168cm/s, Play Rate 1.0 |
| 한손검 1타 검토본 | `ArtSource/Heroine_Tripo_Review/Attack01/Heroine_Attack01.blend`; 상세 조건은 해당 폴더 README 참조 |
| 한손검 1타 연결 후보 | 60fps·1초, 0.50~0.65초 입력 창. 2타 시작 후보는 `Attack01/combo_handoff_pose.json`; 실제 2타 연결은 미검증 |
| 걷기 편집 원본 | `ArtSource/Heroine_Tripo_Review/WalkTimid/Heroine_Walk_Timid.blend` |
| 걷기 클립 | `/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Walk_Timid` |
| 걷기 설정 | 첫 테스트본, 1.333초, 48cm/s. 재사용 전 품질 재평가 필요 |
| 게임 스켈레톤/익스포터 | `ArtSource/Heroine_Tripo_Review/RigReferenceFit/Delivery/` |
| 게임 원본 모션 | `/Game/Constellation/Characters/Shared/Animations/Walk`, `/Game/Constellation/Characters/Shared/Animations/Run` |

이 값은 현재 클립의 결과이지 모든 새 모션에 적용할 고정 표준이 아니다. 최신 README와 실제 리소스를 함께 확인한다. 모델링·텍스처 원본과 게임 원본 모션은 정리 대상이 아니다.

## 1. 시작 시 상태 확인

1. 현재 `.blend`, 활성 Action, 프레임 범위, FPS, 스켈레톤, 단위와 메시 높이를 확인한다. Blender MCP 사용 전 `get_addon_status`, `get_scene_info`를 읽는다. 버전 차이가 있으면 지원되는 기능부터 확인하고 필요 없는 설치 작업을 끼워 넣지 않는다.
   커맨드라인 Blender는 루트 `AGENTS.md`에 따라 `tools/run-blender.ps1`을 통해 실행한다. 썸네일 경로 보호 검사를 우회하지 않는다.
2. 사용자가 편집한 씬이나 재생 상태를 무단으로 덮어쓰지 않는다. 저장된 원본과 별도의 검토본을 사용한다. 정량 검사·배치 렌더·FBX 출력은 백그라운드 Blender, 시각 검토는 연결된 Blender를 활용한다.
3. 기존 게임 모션과 수정본을 같은 카메라·배속·스케일에서 비교한다. 포즈와 속도가 다른 정지 화면만으로 품질을 판단하지 않는다.
4. 손목 뒤틀림, 다리 관절, 발 접지, 몸통 상하 이동, 의상 간섭을 분리 측정한다. 변경 가설과 성공 조건을 먼저 기록한다.

## 2. 원본 모션을 옮기고 국소 수정

- 기존 애니메이션을 추출하고 본의 rest pose, bone roll, 로컬/월드 좌표를 보정해 리타기팅한다. 서로 다른 리그의 회전값을 그대로 복사하지 않는다.
- 애니메이션 FBX의 imported bind pose가 첫 프레임의 자세일 수 있다. 검증된 중립 rest 자료를 사용하고 부모 컨트롤부터 회전을 적용한다. 무기 등 추가 FBX 임포트 후에는 FPS가 바뀌지 않았는지 재확인한다.
- 좌우 다리를 독립된 단순 곡선으로 새로 만드는 대신 원본의 허벅지·종아리 관계, 무릎 굽힘, 발 회전을 보존한다. 허벅지만 줄이면 무릎 관계가 깨질 수 있으므로 관련 구간을 함께 평가한다.
- 손목의 원본 움직임을 무조건 0으로 만들지 않는다. 손가락을 공통 전역축으로 꺾지 않고 각 손가락의 해부학적 굽힘축과 손바닥 방향을 확인한다.
- FK/IK 모드, 스트레치, 부모 공간을 명시적으로 확인한다. 현재 리그는 `Heroine_AnimationRig`, 메시 `Heroine_DetailFinish2`; 기존 Run은 FK 중심이다. 새 모션에 강제로 같은 모드를 적용하지 않는다.

## 3. 접지·템포·상하 이동

1. 접지와 공중 구간을 먼저 지정하고 발끝·뒤꿈치·신발 바닥 높이를 실제 변형 메시에서 측정한다.
2. 접지 구간의 발 이동량으로 권장 이동 속도를 산출한다. In-place 클립에 해당 가상 이동을 더해 월드 공간 발 미끄러짐을 검사한다.
3. 접지를 맞추기 위해 매 프레임 몸 전체를 과도하게 올리면 도약이 과장된다. 몸통 높이의 최대-최소, 공중 발 높이, 변화 속도를 반드시 기록한다.
4. RunSoft에서는 몸통 범위가 17.36cm에서 10.77cm로 줄었다. 공중 여유를 기준으로 높이를 완화해 접지와 관절 회전을 보존했다. 더 낮추려면 다리 굽힘까지 재조정해야 할 수 있다. 전신 Z를 무조건 낮추지 않는다.
5. 주기 변경은 모든 컨트롤·의상 키·보간 핸들·루프 끝·마커를 함께 리타이밍한다. 0.8초를 1.0초로 늘리면 속도는 210→168cm/s가 된다. 이미 늘린 클립에 배속 0.8을 또 적용하지 않는다.

## 4. 의상 폴리싱

- 메시 웨이트부터 확인한다. 이전 치마는 상단 상당수가 골반에 약 98% 고정되어 패널만 움직여도 허벅지가 관통했다.
- 허리 고정부에서 의상 본으로 부드럽게 웨이트를 전환한다. 현재 메시 보정은 치마에 한정하며 정점 위치·UV·얼굴을 바꾸지 않았다.
- 부모 골반 회전을 포함한 패널의 실제 월드 기울기를 측정한다. 로컬 각도만으로 다리를 따라간다고 판단하지 않는다.
- 필요한 여유는 실제 변형된 허벅지 표면에서 산출한다. 골반 기준 보정 벡터가 치마를 아래로 끌어내리는 문제를 피한다. 주기 경계까지 부드럽게 만든다.
- 웨이트 변경은 애니메이션 FBX만으로 전달되지 않는다. 해당 프리뷰 메시도 함께 전달하고 사용자에게 정확한 메시를 안내한다.

## 5. 검증 순서와 한계

1. 빠른 뷰포트에서 정면 사선·반대 사선·측면의 접지/공중/최대 굽힘 자세를 본다.
2. 현재 `RunSoft/validate.py`처럼 프레임 사이까지 120Hz로 검사한다. 루프 관절 위치·회전 차이, 무릎 최소 굽힘, 바닥 침범, 접지 미끄러짐, 치마 외곽을 확인한다. 임계값을 새 모션에 맞춰 검토한다.
3. 정량 검사 통과만으로 자연스럽다고 선언하지 않는다. 전체 주기 렌더와 실제 속도의 반복 재생을 확인한다. 특히 상하 진폭과 템포는 사용자 검토가 중요하다.
4. 방사형 치마 검사는 검사한 허벅지 외곽만 다룬다. 모든 삼각형 충돌 검증으로 표현하지 않는다. 접지 구간 수치와 전 구간 수치를 구분한다.
5. 언리얼 저장 후 별도 프로세스에서 다시 읽어 duration, skeleton, materials, preview mesh, sync markers, source SHA256을 확인한다. 엔진 실제 재생, 게임 이동, 방향 전환, 경사면 IK, 전환 블렌딩은 서로 다른 검증 단계다. 수행하지 않은 단계를 완료로 보고하지 않는다.

## 6. 전달과 반복 작업

- 현재 게임용 스켈레톤은 94본이며 기존 익스포터로 컨트롤 리그를 게임 본에 베이크한다. 이름만 UE 표준으로 바꾸거나 새 스켈레톤을 자동 생성하지 않는다.
- 기존 프로젝트의 FBX 축/단위 설정을 사용하고 160cm 높이를 엔진에서 검증한다. 현재 경로는 legacy FBX importer, import scale 100을 사용한다. 이 값을 다른 파일에 무조건 재사용하지 않는다.
- 결과물에는 편집 `.blend`, 애니메이션 `.fbx`, 필요한 메시 FBX, 미리보기, 변경량·권장 속도·검증 범위를 담은 README를 둔다. API와 스크립트는 현재 설치된 버전에서 동작하는 것으로 검증한다.
- 이전 실패: 원본 관절 관계를 무시한 절차적 발 궤적, 손목 0 고정, 공통축 손가락 회전, 로컬 의상 각도만 평가, 수치 통과 후 자연스러움 확인 생략. 반복하지 않는다.
- 작은 가설 하나를 수정하고 빠른 검사 후 렌더한다. 실패한 변형을 계속 누적하거나, 매번 모든 파일을 다시 만드는 준비 스크립트를 남기지 않는다. 현재 편집 원본을 다음 작업의 시작점으로 사용한다.

## 7. 초안 정리

정리 요청 시 최신본과 재임포트 원본·텍스처·스켈레톤 의존성을 먼저 확인한다. 언리얼 Asset Registry의 hard/soft referencers를 조회하고 살아 있는 외부 참조가 있으면 삭제하지 않는다. 삭제는 엔진 API로 처리하고 결과를 다시 확인한다. 파일 폴더는 절대경로가 프로젝트 내부인지 검증한 뒤 삭제한다. 삭제 목록과 용량을 기록하되 초안을 이름만 바꿔 중복 보관하지 않는다. 사용자의 모델링 원본·게임 원본·설정 백업은 별도 필요성을 검토한다.


## Rebuild 얼굴 엔진 전달 검사 보충 — 2026-10-05

새 Rebuild 작업은 `ArtSource/Heroine_Rebuild/CURRENT.md`의 유지 원본을 따른다. 현재 검토 메시 FBX는 `RuntimeSurfaceReview/SK_player_heroine_new_Rebuild_SurfaceUV.fbx`; 상세 재실행 절차는 같은 폴더 README.md.

- NullRHI/독립 HLSL 컴파일 통과를 실제 엔진 렌더 통과로 간주하지 않는다. PreSkinnedPosition은 VertexInterpolator로 전달하고 스킨 메시의 실제 UV 한도(4)를 확인한다.
- 닫힌 입술처럼 같은 중립 위치에서 서로 다른 모프 변위를 갖는 정점은 임포트 병합을 검사한다. 이번 검토본은 해당 면의 사용하지 않는 UV3 정점 식별값으로 원래 위치/표정을 보존했다.
- 모프 이름/값 readback뿐 아니라 실제 눈꺼풀/입술 움직임을 캡처한다. 정적 에디터 씬에서 이전 변형 버퍼 재사용 문제가 있었으므로 검토는 상태별 독립 컴포넌트로 수행했다. 실제 게임에서는 연속 업데이트를 별도로 검증한다.
- 기존 FBX 재임포트는 저장된 import data를 확인한다. uniform scale=100, morph targets 활성화를 새 옵션에만 지정해도 적용된다고 가정하지 않는다. 재임포트 후 160cm·94본·10모프·재질 연결을 다시 확인한다.
- 전신 56/56 재질 연결과 7개 정적 비교까지 수행했다. RuntimeSurfaceReview/README.md를 따른다. 실제 게임 조명/후처리, 연속 표정·달리기, 얼굴 경계/셰이더 최적화·게임 ABP/표정 브리지 연결은 남아 있다.
- Blender Standard 비교 시 캡처는 RTF_RGBA8_SRGB + Tonemapper off를 사용했다. 톤매핑 진단 화면의 검은 뭉침을 텍스처 자체의 문제로 간주해 원본 색을 밝히지 않는다. 검토용 카메라 설정을 게임 전체 설정 변경으로 확대하지 않는다.

## Rebuild 표정 갱신 검사 보충 — 2026-10-06

- 동일 컴포넌트의 모프 값 readback만으로 렌더 갱신을 판정하지 않는다. 일반 에디터 월드에서는 `set_update_animation_in_editor(True)` 및 `play(True)`를 설정해도 이번 오프스크린 환경에서 시간이 진행되지 않았다.
- 정지 캡처는 상태별 초기화 방식으로 검사하되, 상태 전환 검사는 별도 Simulate In Editor 게임 월드를 사용하고 `get_position()` 진행·실제 변형·초기 상태 복귀를 함께 확인한다. 재생 시퀀스는 진단용으로만 만들고 기존 ABP/플레이어에 연결하지 않는다.
- 현재 재현 스크립트: `ArtSource/Heroine_Rebuild/capture_simulated_expressions.py`; 검사 결과: `EngineSimulationReview/verification.json`. 단계별 캡처 GIF는 실시간 FPS 영상으로 보고하지 않는다.
- `AnimationDataController.notify_populated`는 이 설치의 Python API에 노출되지 않음. 사용 가능한 `set_frame_rate`/`set_number_of_frames` 후 저장과 실제 길이 재확인으로 진단 시퀀스를 구성했다.

- 2026-10-06 텍스처 확인: 일반 스트리밍 조건의 오프스크린 SIE에서 저해상도 텍스처 상태로 눈/입/헤어가 깨지는 현상을 재현. 모델을 재조형하기 전에 `SkeletalMeshComponent.prestream_textures(60., True, 0)`처럼 검토 컴포넌트에 한시적으로 로딩을 요청하고 기다린 뒤 비교한다. 이번 근거리 검사에서는 전역 NoTextureStreaming 기준과 픽셀 오차 0. 이를 실제 게임의 무제한 고해상도 상주 정책으로 적용하지 않는다. 메모리 예산·요청 만료·거리 전환을 따로 검증한다.


### 2026-10-06 얼굴 표정 유지 / 엔진 검증 교훈
- 최신 형태·표정 소스와 남은 작업은 ArtSource/Heroine_Rebuild/HairFoundationRebuild/CURRENT.md를 먼저 확인한다. 현재 exporter/importer는 export_hair_foundation.py / import_hair_foundation_unreal.py다. 과거 일회성 repair 스크립트를 유지 소스에 중복 적용하지 않는다.
- 얼굴 4재질의 POINT 속성은 export-only UV2/UV3로 전달하며 UE Full Precision UVs가 필수다. MI_Exact 매핑을 보존한다. 원본 .blend UV나 형상을 변경해 이 전달을 흉내내지 않는다.
- SkeletalMesh 자산을 바꿔도 컴포넌트의 재질 오버라이드/MID는 남을 수 있다. 비교 시 모든 슬롯을 재설정하고 실제 MID 부모 경로를 매 상태 검증한다. 자산 이름 변경이나 화면 일치만으로 다른 재질이 적용됐다고 판단하지 않는다.
- 표정 검증은 실제 ticking SIE 게임 월드에서 동일 컴포넌트 재생 시간이 진행되는지 확인한다. 일반 에디터 월드 readback만으로 변형이 렌더됐다고 판단하지 않는다. 근접 텍스처는 컴포넌트 prestream과 대기 후 검사하고 전역 설정 변경은 피한다.
- FaceAttributeTransferReview/Maintained 및 FinalBlinkSweep의 실제 재질·복귀 픽셀 검증을 기준으로 삼는다. 단계별 GIF와 정적 셰이더 명령 수는 실시간 애니메이션/FPS 검증이 아니다. 얼굴 기존 스타일과 중립 모프를 보존한다.
