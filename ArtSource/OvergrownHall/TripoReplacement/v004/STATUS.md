# 애니메이션 배경 재질 보정 · 2026-09-25

사용자 요청: 원화에 비해 날카롭고 사실적인 표면을 따뜻하고 부드럽게 변경.

- 현재 맵: `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.
- 실제 렌더/전후 비교: `review.html`, `unreal_painted.png`. 이전 화면은 v003/unreal_structure.png.
- 재적용: `Content/Python/style_tripo_hall.py`를 Unreal Editor의 ExecutePythonScript로 실행. 전체 재생성 시 v002 반입 → v003 건축 보정 → 이 스크립트 순서.
- 재질 재생성 없이 새 프로세스 검증/촬영: `Content/Python/capture_painted_hall.py`. 재질 그래프를 삭제·재연결하는 적용 중에는 임시 missing-input 경고가 발생할 수 있으므로 최종 상태는 `Saved/PaintedHallFresh.log`의 새 로드/SM6 렌더로 구분한다.
- 21종 새 머티리얼: `/Game/Environment/OvergrownHall/TripoFull/PaintedMaterials/M_OH_Painted_{ID}`.
- 532개 액터에 컴포넌트 재질 오버라이드. 원본 텍스처와 메시의 기본 재질 슬롯은 보존.
- 샘플 mip bias +2, 채도 완화 18%, 색상별 안료색 혼합 32–42%, 노멀 강도 10–16%, 러프니스 .76–.87, 스페큘러 .2. 새 텍스처를 손으로 그리거나 AI로 다시 생성한 작업은 아님.
- 태양 16000, 색 (1,.84,.60), 광원 각도 10도, 스카이라이트 2.2. 색 대비 .90, 감마 1.06, 채널 게인 (1.04,1.03,.98), AO .35. 기존 고정 노출 1024 유지.
- 저장 후 맵 재로드 시 532개 재질 오버라이드 검증. 기존 치수·충돌·비둘기 시퀀서 검사 통과. 렌더 성공 여부는 exposure_render_verification.json 확인.
- 실제 캐릭터 플레이와 성능 측정은 미실시.

한계: 재질 보정은 메시 자체의 깨진 실루엣과 잘게 갈라진 잎 형태를 바꾸지 않는다. 원화의 숲 배경, 반사 수면, 구도 차이도 별도 작업이다.
