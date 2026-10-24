> **2026-10-23 재점검: 관절 결함 확인, 이전 외형 합격 판정 철회.** RightUpper06 오른손/전완의 과도한 축 비틀림이 저장본과 엔진 영상에 존재한다. 현재 저장본은 수정 기준점일 뿐 승인 가능한 완료본이 아니다. 상세: `ArtSource/SwordAcquisition/JointRecheck20261023/Findings.txt`. 사용자 요청에 따라 `ArmCorrection20261023`에서 별도 후보를 보정 중이다. 엔진 에셋은 아직 교체하지 않았다. 역수 그립 후보03 및 어깨 누적 회전 결함 후보06은 제외했다. 반프레임 연속성 통과는 관절 외형 합격을 뜻하지 않는다.

# 현재 유지본 — 2026-10-23 사용자 수정 반영

현재 소스는 `ArtSource/SwordAcquisition/GripRevision20261023/Heroine_Sword_RightUpper06.blend`, 전달 데이터는 같은 폴더의 `Delivery/manifest.json`이다. 오른손 상단·왼손 하단으로 변경하고 `RegripRight`를 제거한 7클립을 사용한다. 이전 `Final03`은 보존 원본이며 후속 수정의 현재 시작점이 아니다. 기존 RegripRight 엔진 에셋은 보존하되 런타임에서 참조하지 않는다.

저장·재열기 메시/UV/웨이트/보정 키 보존 검사, 반프레임 관절 연속성 검사, 엔진 재로드와 실제 이벤트 재생 검수 완료. 상세 범위 및 제한은 `ArtSource/SwordAcquisition/AnimationIntegration_2026-10-23.txt`와 `Delivery/engine-review.json`을 확인한다. 사용자 영상 승인 여부는 별도로 기록한다.

이벤트는 실제 QTE/획득 UI/대사/공격 해금/컨트롤 복구/토스트에 연결됐다. BraceLoop와 RaisedHoldLoop는 런타임 몽타주 반복 섹션으로 대기하며, 루프 경계에서 다음 클립으로 넘어간다. 검·본 경계는 연속이고 오른손 재그립은 없다. 과거 8클립 및 미연결 기록은 아래의 제작 이력이다.

---

# 검 획득 애니메이션 — 캐릭터/Unreal 전달

2026-10-21 사용자가 `SwordPull_Sequence03_ForwardGrip`의 캐릭터 적용과 Unreal 에셋 추가를 승인했다. 기존 역수 그립 후보는 사용하지 않는다.

## 유지 소스

- 작업 루트: `C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/SwordPull_Heroine01`
- 현재 저장본: `Heroine_Sword_Final03.blend`. 연속 Action과 `Sword_Approach`, `Sword_BraceLoop`, `Sword_ExtractRecover`, `Sword_RegripRight`, `Sword_ReleaseLeft`, `Sword_Raise`, `Sword_RaisedHoldLoop`, `Sword_Lower` 및 대응 검 Action을 포함한다.
- 원본 캐릭터: `StarSequence01/FingerCorrection01/Heroine_Star_Fingers01.blend`. 기존 메시·UV·웨이트·보정 키를 유지한다. 의상/표정 키를 삭제해 검사 비용을 줄이지 않는다.
- 검수 페이지: 위 작업 루트의 `Delivery/review.html`. 영상 마감 전에는 `delivery.json` 존재 및 최종 검증 상태를 확인한다.
- 프로젝트 전달 데이터: `ArtSource/SwordAcquisition/HeroineDelivery/`.

## Unreal 에셋

`/Game/Constellation/Characters/Heroine/GamePilot/SwordAcquisition/`의 `AS_Sword_*`, `AM_Sword_*` 각 8개. 기존 GamePilot 스켈레톤/메시를 사용한다. 새 스켈레톤, 기존 이벤트/맵 수정, 빌드는 하지 않았다.

| 이름 | 길이 | 용도 |
|---|---:|---|
| Approach | 3.3초 | 접근·양손 잡기 |
| BraceLoop | 2.4초 | 반복 버티기 |
| ExtractRecover | 3.7초 | 뽑기·균형 잡기 |
| RegripRight | 2.0초 | 왼손 지지 중 오른손 정방향 재그립 |
| ReleaseLeft | 1.4초 | 오른손 그립 확정 후 왼손 회수 |
| Raise | 2.2초 | 한손으로 높이 들기 |
| RaisedHoldLoop | 2.4초 | 높이 든 유지 |
| Lower | 2.4초 | 내리기 |

루프 시퀀스는 동일 시작/끝 자세를 포함한다. 재생 시 중복 끝 프레임을 별도 정지 프레임으로 추가하지 않는다. **AM은 기본 1회 재생 래퍼다.** 무제한 QTE/UI 대기는 해당 AS의 looping state 또는 별도로 구성한 montage section으로 구현해야 한다. `enable_auto_blend_out=False`로 끝 프레임을 붙잡는 방식은 루프가 아니다. 이번 Unreal Python 인터페이스는 `composite_sections` 편집을 노출하지 않아 자동 영구 루프 몽타주를 구성하지 않았다.

## 접촉·관절 보정에서 확인한 사항

1. 손목 원점만 옮기면 체형별 손바닥 길이 차이로 손가락과 손잡이가 어긋난다. 실제 근위 마디와 손가락 정점의 접촉을 함께 검사한다.
2. 원본 마네킹의 검지 큰 접힘을 캐릭터에서 그대로 재현하지 않는다. 검지 방향을 안정적인 인접 손가락 축 기준으로 맞추고, 엄지와 각 손가락을 개별 조정했다.
3. `rotation_difference`로 거의 반대인 축을 단독 정렬하면 중간 프레임에서 회전 축이 바뀔 수 있다. 핵심 자세가 자연스러워도 반 프레임 연속성 검사로 급변을 찾는다. 이번 중간 후보의 100도 이상 급변을 제거했다.
4. IK에서 bone tail과 실제 다음 관절 위치가 같다고 가정하지 않는다. 이 리그의 비틀림 본 연결에서는 실제 자식 관절 벡터를 기준으로 풀어야 한다.
5. 캐릭터 팔이 짧아 도달하지 못하면 팔을 늘리거나 손이 검에서 떨어지는 상태로 전달하지 않는다. 뽑기 중 검 궤적을 도달 범위 안으로 조정하고, 한손 구간에서는 검이 실제 손을 따라가도록 했다.
6. 검 quaternion도 부호 연속성과 키 사이 회전을 확인한다. 본 회전만 검사하면 내리기 중 검이 회전하는 결함을 놓칠 수 있다.

검사 파일은 `lock02_metrics.json`, `grip_clearance_lock02.json`, `Heroine_Sword_ContactLock02_continuity.json`, `preservation_final03.json`, `UnrealApply01/verified.json`이다. 정점-원통 거리 검사는 모든 메시 삼각형의 충돌 증명이 아니다.

## 이벤트 연결 경계

- 현재 완료 범위는 캐릭터 저장본, Unreal 에셋 저장/독립 재로드, 임시 씬의 실제 메시 재생 검수다. 실제 검 획득 이벤트·QTE·획득 UI·조작 복귀는 별도 연결/검증이다.
- `HeroineDelivery/sword_tracks.json`은 Unreal component space(cm)의 검 프록시 궤적이다. 피벗은 가드 중심, 검날은 local -Z다. 실제 검 모델의 피벗·치수를 먼저 맞춘다.
- 재그립 전후 손-검 상대 변환은 다르다. 처음 역수 그립의 고정 오프셋을 끝까지 재사용하지 않는다.
- 루프의 임의 위상 종료/0.3초 전환은 마네킹 시안과 실제 런타임 구현을 구분한다. 캐릭터 엔진에서 임의 위상 종료 블렌드는 아직 검증하지 않았다.
- 마지막 자세는 검을 낮게 든 상태다. 게임의 검 장착/해제 Idle과 자동으로 같다고 가정하지 않는다.

## 재현

작업 루트의 `contact_lock02.py`가 손가락 접촉과 도달 범위를 보정한다. `finalize03.py`, `export03.py`, `UnrealApply01/apply.py`, `verify.py`, `capture02.py`가 최종 전달 경로다. `Raw01`, `Contact01/02/03`, `Final/Final02`와 첫 엔진 캡처는 진단용 중간본이며 현재 전달본으로 사용하지 않는다.

모든 Blender 명령줄 실행은 프로젝트 `tools/run-blender.ps1`을 통한다. 다른 채팅의 빌드 작업 디렉터리나 실행 중인 편집기를 정리하지 않는다.
