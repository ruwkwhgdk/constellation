# v019 · 새 구도 기준 남은 원화 보정 통합

맵: `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.
v018 기준 카메라, v015 닫힌 천장50개와 정면 나무 제거, v017 석판/벽 잎 접합은 유지한다. 플레이는 사용자 담당으로 실행하지 않는다.

## 반영한 항목

1. **우측 채광**: 카메라가 +Y를 향하므로 화면 오른쪽은 월드−X다. 기존 보조광은 반대편에 치우쳐 있었다. 초점 스포트를 (−450,1870,860)cm에서 (−30,910,5)cm로 향하게 변경. 1450000cd, 내부7°/외부16°, 반경110cm, 볼류메트릭1.6, 그림자 비활성 유지. 창 보조 면광원(−300,1890,650)cm,110000, 폭500/높이600. 태양15500→8500으로 좌측의 강한 직사광을 줄임. 안개 밀도0.024, 산란방향0.35. 전체 노출1024는 유지.
2. **식생 실루엣**: 관목85배치 중3개를 제거하고82개를 비균일하게 낮추거나 옆으로 확장. 앞쪽 높이46–76%, 후면72–96%로 둥근 덩어리의 연속을 완화. 기존 Tripo 풀11군집과 접합 잎에서 아래로 이어지는15군집 추가. 추가26배치는 NoCollision/그림자 없음. 남은 관목/잎의 Runtime LOD·미세 바람 유지.
3. **수면 색면**: 기존 잔물결과 투명 수면을 보존한 별도 `M_OH_ReferenceWater`. 청록색의 넓은 저주파 색면, roughness0.075–0.20, 정면 opacity0.88/사선0.97, DepthFade18cm. 중심(−60,880)cm·반경240×300cm에서 두 노이즈 마스크로 끊기는 크림색 하이라이트(미술용 emissive180). 실제 물리 반사/카우스틱을 계산한 것은 아니다. 평면 반사 prefilter roughness0.10, distortion0.6, 실시간 갱신 유지.
4. **건축**: 확인 결과 기둥 자체는 이미 사각형이었다. 단면을 임의 교체하지 않고, 유지 Tripo 보정 소스에서 얕고 넓은 박리 파손2종을 제작해18개 기둥 배치에 선택 적용. 각168삼각형,65×65×300cm, 비매니폴드0. 기단/주두20배치의 XY 돌출을 각각92%/88%로 줄이고 높이와 위치 유지. 주 통로와 홀 전체 치수는 확대/축소하지 않음.
5. **비둘기**:28마리, 기존 Tripo 리깅과 Fly/Glide 전환 클립,20초/48fps 유지. 높이240–888cm +15cm 변위, 스케일0.44–0.66, 방위·높이 상관을 바꿔 낮은 중앙부터 상부까지 분산. 기존 따뜻한 밝기 보조 재질 유지. 표본 중심간격109.371cm, 프레임 사이 선형 경로까지 계산한 최소109.366cm. 날개 충돌이나 동적 회피 검사는 아님.
6. **원경**: 기존 나무 없는 Y60m 원경의 별도 `M_OH_ReferenceHaze`. 두 크기의 부드러운 노이즈 색면과 우측(월드X−900cm/Z2100cm)의 넓은 크림색 안개 영역을 겹친다. 높은 곳은 기존 밝은 하늘색으로 이어진다. 실제 원경 나무/지형 또는 대기 산란 시뮬레이션을 추가한 것은 아니다.

## 재현

1. `tools/run-blender.ps1 -b -P ArtSource/OvergrownHall/Scripts/build_hall_spalled_pillars.py`.
2. `Content/Python/complete_hall_reference_finish.py`.
3. 조명/물만 조정할 경우 `balance_hall_reference_finish.py`는 같은 최종 레시피를 재사용한다.
4. `capture_hall_reference_finish.py` 저장 검사/실제 촬영, `verify_hall_reference_finish.py` 새 프로세스 읽기 검사.

`baseline.json`은 v018 액터의 원래 변환·메시·재질 기록이다. 관목/기단/주두는 이 기준에서 계산하므로 반복 적용 시 축소가 누적되지 않는다. 재생성 대상은 이 단계의 `OH_RefFinish_` 배치와 명시된 기존 비둘기 시퀀스다. 기존 메시/재질 원본은 보존하며 `/TripoFull/ReferenceFinish`에 파생 재질을 저장한다. 이전 적용 스크립트를 단독 실행하면 이 상태가 되돌아갈 수 있다.

검사 파일: `pillar_meshes.json`, `verification.json`, `Flock/routes.json`, `Flock/continuous_spacing.json`. 실제 렌더 `unreal_reference_finish.png`, 비교 `review.html`. 최종 체크는 기존 카메라·닫힌 천장·정면 나무 부재·변경 메시·물 재질·추가 배치 충돌·비둘기 경로를 포함한다.

## 한계와 다음 확인

요청한 나머지 시각 보정 항목을 이번 단계에 모두 반영했다. 원화의 회화적 생략, 식생 붓터치와 건축 해석까지 완전히 같아졌다는 의미는 아니다. 실제 플레이의 카메라/이동, 목표 플랫폼 게임 성능, 날개 충돌은 사용자 확인 또는 별도 테스트 범위다. 물리 굴절·수중 모델·캐릭터 파문도 미구현 상태로 구분한다. 과거 에디터 프로파일 수치를 최신 배치 성능으로 재사용하지 않는다.

최종 저장본 검사와 실제 렌더: 2026-09-29 03:38 KST, Saved/HallReferenceFinishFinal.log의 HALL_REFERENCE_FINISH_VERIFIED 및 스크린샷 저장 확인. 자동 작업 프로세스 정상 종료. exposure_render_verification.json의 saved_exposure_verified/screenshot=true, playtest=false.
