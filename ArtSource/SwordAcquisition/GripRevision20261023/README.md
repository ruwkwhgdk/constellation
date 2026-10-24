# 오른손 위 그립 수정 06

최종 Blender 검수 후보는 `Heroine_Sword_RightUpper06.blend`다. `Delivery/manifest.json`의 SHA256과 일치하는 파일만 엔진 검수에 사용한다. 사용자 원본 Final03의 SHA256은 유지했다. 모델·토폴로지·UV·웨이트·셰이프 키·재질 할당은 lida snapshot/compare에서 완전 일치한다. 94본 부모 관계를 유지한다.

오른손을 처음부터 손잡이 위쪽 정방향으로 잡고, 왼손을 아래에 둔다. 기존 승인된 오른손 정방향 손가락 형태를 유지하고 어깨–팔꿈치–전완을 함께 푼다. 접근 시 오른손은 조금 위로, 왼손은 바깥으로 들어오도록 분리해 중간 손 겹침을 제거했다. 고정 시작 quaternion을 사용해 접근 중 회전 경로 반전을 제거했다. 뽑기 복귀 자세를 왼손 회수 시작에 직접 연결한다. Raise/유지/Lower의 기존 오른팔 움직임은 보존하고 검은 실제 오른손 접촉을 따른다.

| 클립 | 길이 | 30fps 샘플 수 |
|---|---:|---:|
| Approach | 3.3초 | 100 |
| BraceLoop | 2.4초 | 73 |
| ExtractRecover | 3.7초 | 112 |
| ReleaseLeft | 1.4초 | 43 |
| Raise | 2.2초 | 67 |
| RaisedHoldLoop | 2.4초 | 73 |
| Lower | 2.4초 | 73 |

런타임에서 RegripRight를 재생하지 않는다. .blend에는 원본 Action 및 기존 연속 타임라인의 예약 구간이 남아 있으므로 `clips.json`의 수정 Action 또는 Delivery의 7개 클립만 사용한다. 루프는 동일 끝 자세 샘플을 별도 정지 시간으로 더하지 않는다.

## 검사

- 수정 전 audit/snapshot, 최종 저장·재열기 audit/snapshot/compare 완료. 비교 대상 필드 완전 일치.
- 인접한 6개 클립 경계의 전체 본/검 t/q/s 차이 0. 초기 Approach 검 transform도 원본과 완전 일치하여 기존 배치 오프셋을 유지할 수 있다.
- 고정 그립 이후 오른손–검 상대 위치/회전 유지 확인. 정확한 오차와 프레임 단위 회전은 `delivery_checks06.json`.
- 실제 저장본의 정면·측면·손 근접 핵심 자세와 접근 중간 프레임을 확인했다. 접근50샘플 영상은 ffmpeg 전체 디코드 exit0.
- 전체 영상 렌더는 외부 디스크 고갈로 중단됐다. 최종06 영상은 접근 구간만 제공하며, 후반은 실제 저장본 핵심 PNG와 수치 검사 범위로 한정한다. 전체 후반 연속 외형과 실제 Unreal 재로드/압축/블렌드/실제 검 모델은 부모 작업의 엔진 검수 대상이다. 데이터 검사 통과를 게임 합격으로 보고하지 않는다.

## 파일과 재현

`revise06.py`, `export06.py`, `validate06.py`, `checks06.py`를 사용한다. 모든 Blender 명령은 프로젝트 `tools/run-blender.ps1 --background --factory-startup --disable-autoexec`를 통한다. 원본·인터랙티브 Blender·Unreal 코드/맵/그래프는 이 작업에서 수정하지 않았다.

폐기 후보01–05 .blend는 디스크 고갈 대응으로 제거했고 재생성 스크립트와 진단 기록을 남겼다. 원본과 최종06 및 검수 PNG/MP4를 보존했다. 초기 Delivery/Delivery04/Delivery05 자료는 과거 진단 결과이며 `Delivery/manifest.json`의 최종06만 현재 전달본이다. Intermediate는 건드리지 않았다.
