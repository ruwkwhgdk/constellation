# v025 · 후면 식생과 벽체 통합

유지 맵: `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.

`finish_hall_reference_integration.py`는 유지 v024 적용부를 먼저 실행하고(그 버전의 촬영/종료 예약은 제외) 다음 보정을 수행한다.

- v024 상부 벽 파생 메시의 뾰족한 두 결손을 넓은 단일 결손으로 다듬음. 원본 몰딩/본체 union 후 차집합. 최종454/462삼각형, nonmanifold0. 벽 높이·하단 바운드 검증.
- `OH_FinalWallGrowth_00..03`의 수관 메시를 유지 Tripo 관목 Runtime 메시로 교체하고 바운드 바닥을3cm로 맞춤. 높이125/195/145/170cm, 불규칙 폭270/300/310/225cm. 기존 바닥 식생과 연결.
- 층 사이 띠에 붙는 작은 잎3군집 추가. 충돌 없음. 새 접두사 `OH_ReferenceIntegration_`.
- 후면 하부 벽6배치에 청록 석재와 하부 이끼 색면을 적용하고 제한적인 밝기 보조(emissive130)로 너무 검게 막힌 면을 완화. 실제 유지 소스는 `/FinishMaterials/M_OH_Weathered_05`.

검사/촬영: `Content/Python/capture_hall_reference_integration.py`. `baseline.json`은 v024 적용 후 기준이다. 기존 카메라·통로·새 창 비율·닫힌 천장·새 상부 벽·비둘기 애니메이션 보존을 검사한다. 직접 플레이/게임 성능은 미실행.

v024의 저장된 렌더는 상부 벽 윤곽의 중간 결과다. 최신 형상과 재질의 실제 비교에는 v025 렌더를 사용한다.
