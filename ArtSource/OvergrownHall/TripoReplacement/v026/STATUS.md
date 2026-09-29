# v026 · 빛과 청록 수면 연결

유지 맵 `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.

## v023 이후 실제 수정

- v024: 후면 창을 큰3칸+좌측 부분 창으로 정리. 주요 기둥 경계·하부 창·상부 창·층 사이 띠 높이 보정. 측면 중간 보4개와 잎4군집, 상부 벽8개 추가. 중앙 카메라와 통로는 유지.
- v025: 상부 벽 결손을 덜 뾰족하게 수정. 후면 큰 수관4개를 바닥에 연결된 Tripo 관목으로 교체. 창 띠 부착 식생3군집, 하부 벽6배치의 청록/이끼 색면 보정.
- v026: 청록 수면의 roughness0.018·평면 반사 prefilter0.01로 명료도 보강. 반사 screen percentage60→75. 기존 잔물결·흰 반사 마스크 유지, 바탕색의 청록 비중 보강.
- 우측 아래 창에 실제 볼류메트릭 스포트1개 추가. 시작(−460,1900,680)→목표(−20,1000,20)cm,900000cd,4°/7°,반경1800,volumetric12,그림자 없음. 카메라를 향하는 빛 카드가 아니다.
- 창 너머 밝은 영역은 우측 아래에 한정된 크림색으로 보강. 측면 나무10개의 강한 그림자를 비활성화. 나무와 충돌/배치는 보존.

## 유지 소스

1. `Scripts/build_hall_upper_wall_infill.py`는 항상 `tools/run-blender.ps1`로 실행.
2. `Content/Python/finish_hall_reference_integration.py`는 v024 적용부와 v025 보정을 순서대로 실행한다.
3. `Content/Python/finish_hall_reference_light_water.py`로 최종 빛/물 적용.
4. 저장된 최신 상태 확인만 할 때는 `capture_hall_reference_light_water.py`만 실행한다. 앞선 전체 레벨 생성 스크립트는 최신 보정을 덮어쓸 수 있다.

## 검사와 범위

`verification.json`은 새 스포트 외 기존 변환·메시, 천장50개·비둘기28마리·후면 나무 제거 상태·반사 설정을 검사한다. `exposure_render_verification.json`은 실제 스크린샷 갱신을 별도로 기록한다. 구조/애니메이션은 v024/v025 검사 기록도 참조한다.

`../v024/landmark_projection.json`은 원화에서 추정한 창 경계와 고정 카메라 투영의 비교다. 최대 약7.1픽셀 차이이며 이미지 유사도 점수가 아니다.

수면의 흰색 영역과 원경·일부 재질에는 미술용 발광 보조가 있다. 모든 효과가 물리 시뮬레이션 결과인 것은 아니다. 반사 해상도 증가의 성능 비용은 측정하지 않았고 과거 성능 수치를 재사용하지 않는다. 직접 플레이·게임 성능·날개 충돌은 미검증.
