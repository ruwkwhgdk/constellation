# v020 · 채광·식생 간격·잔잔한 수면

유지 맵: `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.

v019 비교에서 우선순위로 선정한 세 항목을 보정한다. 건축/천장 형태 재설계 및 비둘기 연출의 추가 수정은 이번 범위에 포함하지 않는다. 카메라와 공간 치수, 닫힌 천장, 후면 나무 제거, 기존 비둘기 시퀀스는 보존한다. 플레이 테스트는 사용자 담당.

## 변경

- 태양 8500→5000, 우측 스포트 위치(−490,1820,1000)cm→목표(50,850,0), 강도2200000·반경2400cm, 콘8°/14°, 볼류메트릭2.8. 창 보조광110000→75000. 벤치 전면에 그림자 없는 제한 반경750cm 면광원28000 하나 추가. SkyLight1.35→1.65로 어두운 면을 보완. 전체 노출1024 유지.
- 바닥 관목16배치를 선택한 연속 구간에서 제거. 51배치 크기를 기준본 대비 비균일하게 조정. 벽 잎13군집은 벽 방향으로 넓히고 실제 바운드 중심을 유지. 소스 메시/텍스처/Runtime LOD는 그대로 사용.
- 수면의 기존 얕은 물·잔물결 변위를 유지. 월드 노멀 진폭을 X0.0015/Y0.004로 낮추고 평면 반사 왜곡0.6→0.12, prefilter roughness0.10→0.04. 큰 emissive 얼룩을 끊어진 얇은 수평 스트라이프 마스크로 교체. 이는 미술용 하이라이트이며 물리 카우스틱이 아니다.
- 나무 없는 원경에 좌측의 차가운 중간 밝기와 우측의 따뜻한 밝기 차이를 적용. 실제 원경 지형은 추가하지 않음.

## 재현·검사

- 적용: `Content/Python/refine_hall_light_foliage_water.py`.
- 조명만 재적용: `Content/Python/balance_hall_atmosphere_finish.py`.
- 저장본 검사 및 촬영: `Content/Python/capture_hall_atmosphere_finish.py`.
- `baseline.json`은 수정 전 v019 기록. 스케일은 기준에서 재계산하므로 반복 축소되지 않는다. 기존 v019 재질을 보존하고 `/TripoFull/AtmosphereFinish`에 파생본 저장.
- `verification.json`은 카메라·폐쇄 천장50·비둘기28·삭제된 후면 나무 부재·관목 삭제·수면 및 보조광 설정을 검사한다. 범위 밖 액터의 변환/메시도 기준과 비교한다.
- `exposure_render_verification.json`은 실제 스크린샷 갱신 여부와 플레이 미실행 상태를 별도 기록한다.

게임 성능, 캐릭터 이동 및 다른 시점의 체감은 검증하지 않는다. 건축 측면 아치의 규칙성, 천장 부재와 비둘기 실루엣은 여전히 별도 개선 후보다.

최종 검증: 2026-09-29 03:54 KST 실제 렌더 확인. HallAtmosphereFinal.log의 HALL_ATMOSPHERE_FINISH_VERIFIED 및 정상 종료 확인. 총729액터. exposure_render_verification.json의 saved_exposure_verified/screenshot=true. 큰 수면 얼룩 제거와 벤치 가독성 개선 확인. 원화 수준의 따뜻한 사선 광선과 회화적 식생은 여전히 추가 미술 조정 여지가 있다.
