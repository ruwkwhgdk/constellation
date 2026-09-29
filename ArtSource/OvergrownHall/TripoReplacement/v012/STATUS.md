# v012 · 투명 수면과 얕은 침수 바닥

유지 레벨: `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.

## 변경 범위

- v011 불투명 반사 재질을 실제 반투명 Surface Forward Shading 재질로 교체. v011 월드 노멀과 최대 ±0.12cm 잔물결 변위를 유지.
- 시선 각도에 따라 투명도를 바꾸고 DepthFade 8cm로 바닥과 만나는 가장자리를 부드럽게 처리. SSR와 평면 반사 옵션 사용. 높은 금속성은 원화에 맞춘 반사 강도 조절이며 물리적으로 정확한 물의 파라미터가 아니다.
- 기존 침수 바닥 47개의 높이를 v011 기준 5cm 미만으로 추가 조정. 서로 다른 얕은 깊이를 부여. `baseline.json`을 유지하여 재실행 시 누적되지 않는다.
- 벤치를 받치는 석판 1개만 가장자리 파손 변형으로 교체. 기존 v005 Tripo 보정 소스 기반이며 중앙 지지면과 아래쪽 바닥은 유지. 532삼각형, 열린 경계/비매니폴드 모서리 0.
- v010 식생, v011 아치 파손3곳, 카메라·빛·비둘기28 유지.

## 유지 소스와 재현

1. `tools/run-blender.ps1 -b -P ArtSource/OvergrownHall/Scripts/build_shore_slab.py`.
2. 전체 Unreal 에디터에서 `Content/Python/apply_shallow_water.py` 실행. 이 스크립트는 `polish_shallow_water.py`를 APPLY=True로 호출한다.
3. 새 에디터 프로세스에서 `Content/Python/capture_shallow_water.py`로 저장본을 검사하고 촬영.

`polish_shallow_water.py` 단독 실행은 저장하지 않는 장면 시험이다. 재질/메시 애셋 생성은 별도로 저장되므로, 이미 v012 재질을 사용하는 맵에는 완전히 격리된 실험이 아니다. 새 파라미터 시험 시 별도 이름의 재질을 사용한다. 이번 최초 시험은 v011 유지 맵의 재질을 바꾸지 않은 상태에서 수행했다.

공통 Graph 도구는 `apply_hall_growth_water.py`, 유지 잔물결 그래프는 `apply_water_ruins.py`에서 읽는다. 따라서 이 제작 소스들도 유지한다. 이전 전체 장면 제작 스크립트를 단독 재실행하면 최신 보정을 덮어쓸 수 있다.

## 검증과 남은 한계

최종 새 프로세스 검증은 2026-09-29 00:33 KST. `Saved/HallShallowsVerify.log`에서 저장 검사 통과, 00:33:03 수면 화면·00:33:13 진단 화면 촬영, 정상 종료를 확인했다. Error/Traceback/재질 컴파일 실패 없음. 실제 최대 바닥 추가 하강은 4.5917cm.

`shore_mesh.json`은 실제 메시 검사, `verification.json`은 저장 맵·위치·재질·충돌 설정과 유지 애셋 검증이다. `unreal_shallows.png`는 실제 Unreal 렌더. `without_water.png`는 검증용으로만 수면을 숨긴 화면이며 그 숨김 상태를 맵에 저장하지 않는다.

바닥의 실제 알파 투과는 구현했지만 굴절·흡수/산란 수심 모델·수중 카메라·캐릭터 물보라/파문은 구현하지 않았다. 반사는 화면 및 평면 반사의 제약을 받는다. 직접 캐릭터 플레이, 프레임 시간, 다른 카메라에서의 경계/정렬은 별도 검증 대상이다. 원화와 비교할 때 후면 벽체의 큰 결손과 국소 조명, 물가 전체의 더 복잡한 경계는 추가 보정 여지가 있다.
