# 2026-09-14 플레이테스트 수정 정리

대상 브랜치: `develop`. 기준 커밋: `ab8fc7f`.

## 목표 및 커밋 분류

| 분류 | 목표 | 변경 파일 |
| --- | --- | --- |
| 프랍 충돌·물리 | 가구와 동굴 프랍의 충돌 기반 보완 | 아래 메시 11개 |
| 수집 오브젝트 | 현재 작업 중인 별 오브젝트 에셋 변경 보존 | `BP_Star_Object`, `BP_Star_Object_Sequence` |
| 통로 카메라 | passage_side 벽·바닥 카메라 관통 방지 | `BP_Spline` |
| 환경 재질 | 창문 외부 차폐 및 구멍 안쪽 시각 보정 | 신규 재질 2개 |
| 레벨 통합 | 조명, 배치, 추락 및 이동 경계 보정 | `AbandonedSchool.umap`, 본 문서 |

## 프랍 충돌·물리 파일 목록

- `Content/Art/ElevatorHubGround/Pass2/SM_HubDumpFixedCollar341.uasset`
- `Content/Art/ElevatorHubGround/Pass2/SM_HubP2RockCollar321.uasset`
- `Content/LuosCaves/Meshes/Props_Rocks/SM_LCave_P_Rock_31.uasset`
- `Content/ModulAbandJPSchool/Meshes/Props/Books/SM_Books01.uasset`
- `Content/ModulAbandJPSchool/Meshes/Props/Books/SM_Books02.uasset`
- `Content/ModulAbandJPSchool/Meshes/Props/Books/SM_Books03.uasset`
- `Content/ModulAbandJPSchool/Meshes/Props/Books/SM_Books04.uasset`
- `Content/ModulAbandJPSchool/Meshes/Props/SM_BookShelf01.uasset`
- `Content/ModulAbandJPSchool/Meshes/Props/SM_SchoolChair.uasset`
- `Content/ModulAbandJPSchool/Meshes/Props/SM_SchoolDesk.uasset`
- `Content/Resources/Environments/Props/AbandonedSchool/SM_Fluorescent_Light/SM_Fluorescent_Light.uasset`

## 블루프린트 및 재질

- `Content/Blueprints/Actor/Common/Star_Object/BP_Star_Object.uasset`
- `Content/Blueprints/Actor/Common/Star_Object/BP_Star_Object_Sequence.uasset`
  - 기존 작업 트리에 있던 변경을 별도 커밋으로 보존한다. 현재 그래프에는 상호작용 후 능력 해금, 튜토리얼 및 시퀀스 연계가 있다. 기준 버전과의 의미 단위 비교와 게임 실행 검증은 이번 Git 정리 범위에서 수행하지 않았다.
- `Content/Blueprints/System/BP_Spline.uasset`
  - 인스턴스별 `BlockCamera` 옵션 추가. 기본값은 false이며 passage_side에만 활성화.
  - Construction Script에서 생성하는 메시의 Camera 응답을 Block으로 설정하여 재생성 시에도 유지.
- `Content/Art/Hollow/M_CorridorHoleInterior.uasset`
- `Content/Art/SchoolCave/Materials/M_ClassroomStart_WindowBlackout.uasset`

## AbandonedSchool 레벨 수정 목록

여러 구역의 배치가 단일 바이너리 맵에 저장되어 있으므로 맵 파일은 한 커밋으로 관리한다. 아래는 작업 기록에 따른 분류이며 에셋별 바이너리 차이의 의미 분석을 대신하지 않는다.

- 조명: 형광등과 문제 광원의 그림자 비용 조정. corridor_hollow 구멍 위 형광등 배치 및 후속 광량 감소.
- classroom_start: 창문 바깥을 검푸른 재질로 차폐.
- classroom_slime: 파괴 후 노출되는 외부 차폐와 추락 방지 경계 보완.
- corridor_hollow: 구멍 가장자리와 안쪽 면 정리.
- sector3/corridor_main: 바닥·벽·상부 구조물 겹침 보정.
- elevator_hub 및 basement: 책상·의자·책을 기존 공용 물리 액터로 교체. 지하 책상·의자 크기 보정, 암석 및 떨어진 형광등 충돌 보완.
- elevator_hub: 상부 엘리베이터 메시 크기와 roof 재질 보정.
- basement 화물 엘리베이터: 시각 메시의 중복 스케일 보정.
- large_cave_passage: 추락 외부 차폐와 하부 복귀 트리거 배치. 입구에 접근하기만 해도 작동하던 트리거의 오버랩 비활성화. 하부 트리거의 추락 연출 시간 복원.
- large_cave: 동굴 내부로 돌출되던 EastLower 차폐면의 상단을 Z=6900으로 낮춤.
- large_cave/passage_side: 19개 통로 구간의 카메라 차단 활성화.

## 검증 및 남은 확인

- passage_side: 19개 메시의 Camera=Block 확인. 통로 5개 지점에서 양쪽 벽과 바닥을 향한 카메라 채널 검사 15건 모두 해당 통로 충돌 확인.
- EastLower: 수정 후 범위 Z=4000~6900 확인 및 뷰포트에서 돌출 차폐면 제거 확인.
- 이전 추락 복귀 시험에서 복귀 위치 도달을 확인했으나, 최종 타이밍 수정 후 실제 낙하 연출 전체는 다시 검증하지 못했다.
- 전체 패키징 및 전 구역 플레이테스트는 수행하지 않았다.
- `Saved/Profiling`의 임시 진단 스크립트와 로그는 기존 `.gitignore` 정책에 따라 커밋하지 않는다.
