# v023 · 원화 명암과 수면의 균형

유지 맵 `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.

## 이번 연속 작업

- v021: 측면 아치6개·지붕 트러스3개에 큰 비대칭 파손, 처진 부재6개, 비둘기28마리의 크기0.27–0.58 및 밝은 크림색 실루엣. 기존 Tripo 리깅·경로·140개 애니메이션 섹션 유지.
- v022: 잎127배치의 잔무늬를 큰 녹색 색면으로 묶고, 기둥55배치의 차가운 색감 보정. 수면 및 우측 역광 강조.
- v023: 과해진 반사를 중심(−65,940)cm·반경430×140cm로 좁히고 노이즈를 넓게 끊음. 스포트2200000, 볼류메트릭4.3으로 완화. 후면 벽 Y1960cm에 닿는 잎 군집4개 추가. 나무를 복원한 것이 아니며 NoCollision, 그림자 없음.
- 후면 군집의 바운드 최저점은 바닥 위5–15cm로 낮춰 기존 하부 식생과 연결. 측면 나무10개는 X±1150→±1600cm로 옮겨 주요 창에서 줄기 노출을 줄임. 원래 Y/Z·크기·충돌 유지.
- 나무 없는 원경은 아래쪽 창에 밝은 녹색 색면이 남도록 하늘 전환 높이를1850–2950cm로 조정. 실제 나무/지형 추가가 아닌 유지 원경 재질의 미술 보정.

카메라/홀 치수/닫힌 천장50개/정면 뒤 나무 제거 상태 유지. 물은 잔잔한 노멀과 평면 반사를 사용하며, 크림색 하이라이트에는 미술용 emissive 마스크가 포함된다. 잎은 기존 알파·바람·Runtime LOD 보존. 먼 잎에도 동일한 바람 파생 재질을 적용했으므로 과거 v014의 near/far별 비용 수치를 최신 성능으로 재사용하지 않는다.

## 유지 소스와 검증

- 형태: `Scripts/build_hall_silhouette_finish.py`를 `tools/run-blender.ps1`로 실행, `Content/Python/finish_hall_silhouettes.py`로 적용.
- 색면: `Content/Python/finish_hall_color_masses.py`.
- 최종 균형: `Content/Python/balance_hall_reference_final.py`.
- 저장본 검사/촬영: `Content/Python/capture_hall_reference_final.py`.
- 현재 레벨을 확인하기만 할 때는 마지막 검사/촬영만 사용한다. 이전 전체 생성 스크립트 단독 실행은 최신 결과를 되돌릴 수 있다.
- 기준과 변경 내용: 각 버전의 `baseline.json`, `applied.json`, `verification.json`.

직접 플레이·성능·날개 충돌은 확인하지 않는다. 성공 판정은 `../../REFERENCE_ACCEPTANCE.md`의 고정 카메라 시각 기준을 따른다. 실제 최신 렌더를 본 뒤 판정을 기록한다.

## 최종 확인

2026-09-29 04:29:56 KST의 `unreal_reference_final.png`를 원화와 비교했고, 위 문서의 다섯 시각 기준에 대해 통과로 판단했다. 동일한 이미지·붓터치 재현을 뜻하지 않으며 세부 차이는 판정 문서에 명시했다.

`Saved/HallReferenceBackdrop.log`: HALL_REFERENCE_FINAL_VERIFIED, 스크린샷 저장, 정상 종료 확인. Error/재질 컴파일 실패 없음. `verification.json`:739액터, 후면 나무 제거 유지, 측면 나무10이동, 후면 잎4, 천장50, 비둘기28/140애니메이션 섹션. `exposure_render_verification.json`: saved_exposure_verified=true, screenshot=true, playtest=false.

재검토: 사용자 후속 요청으로 원화와 다시 대조한 결과 창의 큰 구성·중간 건축·식생 덩어리·안개광 차이가 남았음을 확인. 앞선 시각 통과 판정은 철회하고 v024 이후 보정 중. 기술적 저장 검사 결과는 유지됨.
