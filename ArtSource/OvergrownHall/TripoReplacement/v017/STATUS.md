# v017 · 벽 식생 접합과 벤치 석판 마감

맵: `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.

- v016에서 일부 떠 보이던 벽 잎13군집을 가까운 기둥의 안쪽 면에 재배치. 메시 원점 대신 실제 월드 바운드 중심을 사용하고 잎의 얇은 방향이 기둥 범위에 일부 겹치게 연결한다. 기존 잎 재질·바람·LOD·NoCollision 유지. 바운드 접합 검사는 실제 잎 하나하나의 접촉이나 메시 삼각형 간 교차 검사가 아니며 렌더 확인을 병행한다.
- 벤치 아래 석판1개만 별도 가장자리 파손본으로 교체. 유지 v005 Tripo 보정 바닥 소스에서 불규칙한 주변 결손6곳을 제작. 중앙 받침, 액터 위치/스케일/기존 재질 유지. 588삼각형, 열린 경계0, 비매니폴드0. 지붕/정면 나무 제거/원경/조명/수면/비둘기는 유지.

## 재현

1. `tools/run-blender.ps1 -b -P ArtSource/OvergrownHall/Scripts/build_bench_shore_finish.py`.
2. `Content/Python/finish_hall_contacts.py`.
3. `Content/Python/capture_hall_contacts.py`로 저장본 검증 및 실제 렌더.

`baseline.json`은 v016 잎 및 석판의 위치·회전·스케일·메시 기록. 동일 기준으로 재적용하므로 배치가 누적 이동하지 않는다. `applied.json`에 각 잎의 접합 기둥과 최종 위치를 기록한다. 파생 메시 `SM_OH_BenchShoreFinish`는 원본 석판을 덮어쓰지 않는다. 유지 Blender 원본과 v012 제작 레시피가 입력이므로 삭제하지 않는다.

검증: `shore_mesh.json`, `verification.json`, 실제 렌더 `unreal_contacts.png`. 바운드 접합/저장된 위치/석판 충돌/천장50개/정면 나무 부재/물 재질/비둘기28 검사. 플레이 테스트는 사용자 담당이며 이번에 실행하지 않는다. 동선과 벤치 주변 걸림은 직접 플레이 확인 대상이다. 성능 측정은 이번 범위에 포함하지 않는다.

현재 남은 확인은 사용자 플레이와 다른 시점의 체감이다. 원화는 회화적 생략과 조명을 포함하므로 완전한 시각 일치를 주장하지 않는다. 물리적 굴절·캐릭터 파문 등은 별도 기능 범위다.
