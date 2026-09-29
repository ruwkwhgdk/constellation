# 건축 식생·얕은 수면 보정

- 유지 맵: `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.
- 원화와 전후 검토: `review.html`. 실제 Unreal 렌더: `unreal_growth_water.png`.
- 이전 532개 환경 메시와 구조 치수는 유지.
- 9종 석재/바닥/지붕 재질에 월드 좌표 기반의 큰 이끼 패치와 작은 불균일을 혼합. 하단은 습기를 가정하여 더 강하게 표현. 새 재질은 `TripoFull/GrowthMaterials/M_OH_Moss_{ID}`.
- 승인된 Tripo 덩굴18과 관목17을 재사용하여 기둥·후면 창 아래·상부 보에 잎 덩어리와 덩굴 추가. 배치 좌표/규모는 applied.json. 추가 액터는 OH_Growth_ 접두사이며 재실행 시 이 접두사만 다시 배치.
- 최종 수면은 `M_OH_ReflectivePuddle`의 불투명 반사 재질과 동적 평면 반사. 앞선 물 재질과 법선 경로에서는 건축 반사가 충분히 나타나지 않아, 동일 메시의 불투명 거울 비교에서 확인한 최소 구성을 사용한다. 물 높이 2.2cm,러프니스 .018,금속도1,색(.42,.58,.52). 실제 바닥 투과/굴절과 애니메이션 잔물결은 생략한 스타일 표현이다. 금속도는 예술적 반사 강도 조절이며 물의 물리적 재질 수치라는 뜻이 아니다.
- `OH_WaterPlanarReflection`: 수면과 같은 높이, 75% 해상도, 45m 반사 거리. [Epic 평면 반사 문서](https://dev.epicgames.com/documentation/en-us/unreal-engine/planar-reflections-in-unreal-engine)에 따라 실제 장면을 추가 렌더링하는 방식이며 렌더 비용이 증가한다. 성능 측정은 별도.
- 실행 진단에서 r.ReflectionMethod=2(SSR), GI=0, GenerateMeshDistanceFields=0 확인. PP 설정 구조체 기본값만 보고 Lumen이 켜졌다고 판단하지 않는다. 기존 Config/DefaultEngine.ini의 잘못된 r.SupportGlobalClipPlane 항목을 실제 엔진 CVar인 r.AllowGlobalClipPlane=1로 수정. [Epic CVar 명세](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-console-variables-reference) 확인 후 실행 시 값1을 검사한다. 에디터 재시작과 관련 셰이더 재컴파일 필요.
- 물·추가 식생은 NoCollision. 기존 바닥 충돌로 이동 유지. 상호작용 물결·발소리·젖는 캐릭터·수영은 미구현.

## 실행 순서

기존 v002 → v003 → v004 → v005 유지본에서 `Content/Python/apply_hall_growth_water.py` → `Content/Python/refine_hall_water_reflection.py` → `Content/Python/finalize_hall_reflective_water.py` 실행. `verify_hall_growth_water.py`가 기존 메시 532개, 이끼 재질, 추가 식생, 수면/반사 설정, NoCollision과 기존 배치/비둘기 검사를 수행한다.

이후 v005 반입을 다시 실행하면 이끼 재질이 교체되므로 v006도 재적용한다. 직접 플레이와 성능 측정은 별도이며 미실시. 런타임 수면 반사는 카메라와 엔진 반사 설정에 영향을 받는다.

`capture_hall_growth_water.py`는 새 프로세스에서 재생성 없이 검증·촬영한다. 반사 캡처가 같은 시점으로 안정화되도록 검토 카메라를 먼저 에디터 뷰포트에 고정하고 `ShowFlag.ReflectionEnvironment 1`로 반사 표시를 명시한다. 이 플래그의 기본 CVar 값2는 각 뷰포트 표시 설정을 따른다는 뜻이며 활성화를 보증하지 않는다. `probe_hall_reflections.py`의 임시 거울은 저장하지 않으며 진단 이미지와 설정만 남긴다.
