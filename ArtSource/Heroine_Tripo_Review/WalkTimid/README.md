# 조심스러운 걷기 — 첫 테스트 클립

현재 게임의 `/Game/Resources/Characters/CommonAnimation/Walk`를 직접 내보내 발 디딤 순서와 상체 움직임을 분석했습니다. 원본 리듬을 작게 반영하고 짧은 보폭, 작은 팔 흔들림, 살짝 숙인 시선으로 조심스러운 성격을 표현했습니다.

- 애니메이션: `/Game/Resources/Characters/PC/player_heroine_new/Animations/AS_player_heroine_new_Walk_Timid`
- 스켈레톤: 기존 `SKEL_player_heroine_new`
- 미리보기 메시: `SK_player_heroine_new_WalkPreview`
- 미리보기 레벨: `/Game/Resources/Characters/PC/player_heroine_new/Preview/L_player_heroine_new_Walk_Timid`
- 해당 레벨에서 Simulate를 실행하면 반복 보행을 확인할 수 있습니다. 애니메이션 에셋을 직접 열어 재생해도 됩니다.
- 30fps, 1.333초 반복, 한 걸음 약 32cm, 기준 이동 속도 48cm/s, In-place.
- 좌/우 발 디딤 동기화 마커: LeftPlant / RightPlant. 발소리 실행 로직은 포함하지 않습니다.

`Heroine_Walk_Timid.blend`에는 편집 가능한 컨트롤 키가 있습니다. `AS_player_heroine_new_Walk_Timid.fbx`는 게임 본으로 베이크한 애니메이션입니다.

걷기 검사에서 기존 메시의 치마 일부가 골반에 과도하게 고정돼 다리가 관통하는 문제가 발견되었습니다. `SK_player_heroine_new_WalkPreview`는 치마 웨이트만 보정한 별도 사본입니다. 기본 정점 위치, UV, 텍스처, 얼굴과 체형은 유지했습니다. 원래 `SK_player_heroine_new`와 게임의 기존 이동 블렌드스페이스는 변경하지 않았습니다. 기존 메시로 이 애니메이션을 재생하면 치마 간섭이 남을 수 있으므로 동봉 미리보기 메시에서 먼저 확인하세요.

이 파일은 첫 걷기 테스트용입니다. 실제 이동 연결 시 캐릭터 이동 속도와 재생 속도를 맞춰야 하며, 경사면 발 IK, 방향 전환, 출발·정지 전환은 별도 작업입니다.
