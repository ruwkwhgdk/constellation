# v027 · 원화 비교 마감

유지 맵: `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.

## 이번 연속 보정

v023의 성급한 통과 판정을 철회한 뒤 다음을 실제 저장 맵에 적용했다.

- v024: 후면 창을 큰 세 칸과 왼쪽 부분 창으로 정리. 창 사이 기둥·상하 창 높이·층 사이 띠를 원화 비율에 맞춤. 측면 보4개 재배치, 부착 잎4개·상부 벽8개 추가. 카메라와 통로 치수 유지.
- v025: 상부 벽 결손을 뾰족한 톱니에서 넓고 불규칙한 파손으로 보정. 최종 벽2종은454/462삼각형, nonmanifold0. 후면 원뿔형 잎4개를 바닥과 연결되는 Tripo 관목으로 교체. 창 띠 잎3군집, 후면 벽6개의 색면 보정.
- v026: 청록 수면의 반사 명료도와 우측 아래 창의 채광 보강. 측면 나무10개 그림자 비활성화. 평면 반사 screen percentage60→75, roughness0.018, prefilter0.01. 자세한 값은 `../v026/STATUS.md`.
- v027: 왼쪽 기둥의 강한 직사광 대비를 줄이기 위해 태양1700lux, 스카이라이트1.8. 상부 초점광2200000cd,5°/8°,volumetric4. 하부 창 광원450000cd,volumetric6. 모든 액터의 위치·회전·크기와 기존 메시를 유지.

## 유지 소스 / 재검사

1. 필요한 경우에만 `Scripts/build_hall_upper_wall_infill.py`를 `tools/run-blender.ps1`로 실행. 최신 FBX는 v024 폴더에 있다.
2. v024–025 구조 적용은 `Content/Python/finish_hall_reference_integration.py`가 순서대로 처리한다. v024 소스와 v025 설정이 필요하다.
3. `Content/Python/finish_hall_reference_light_water.py`로 v026 재질/반사/광원 적용.
4. `Content/Python/balance_hall_acceptance_light.py`로 v027 조명 적용.
5. 이미 저장된 맵의 재검사/촬영은 **`Content/Python/capture_hall_acceptance_light.py`만 실행**한다. 앞 단계 전체 재생성 스크립트를 단독 재실행하면 최신 보정을 덮어쓸 수 있다.

`verification.json`은 저장 맵을 다시 읽어755액터, 기존 변환/메시, 최종 조명값, 천장50개, 비둘기28마리, 제거한 후면 나무의 부재를 확인한다. 애니메이션140섹션과 새 식생/벽체 검사는 v025 기록을 참조한다. `exposure_render_verification.json`은 촬영 갱신을 별도로 확인한다.

`../v024/landmark_projection.json`의 최대 약7.1픽셀 오차는 수동 추정한 창 기준점 일곱 곳과 고정 카메라 투영의 비교다. 이미지 전체 유사도나 정밀 영상 정합 결과가 아니다.

## 범위와 한계

고정 카메라의 실제 Unreal 렌더를 원화와 비교한다. 판정은 `../../REFERENCE_ACCEPTANCE.md`를 참고한다. 원화의 붓터치·개별 파손·빛 모양의 완전한 복제는 아니다.

수면의 흰 반사 일부, 원경 및 식생/벽 밝기에 미술용 발광 보조가 있다. 모든 효과가 물리 시뮬레이션 결과는 아니다. 평면 반사 해상도 증가의 성능 비용은 미측정이며 이전 성능 수치를 재사용하지 않는다. 캐릭터는 추가하지 않았고, 직접 플레이는 사용자 담당으로 남겼다. 게임 성능·날개 충돌·다른 플레이 시점의 완성도는 이번 시각 판정에 포함하지 않는다.
