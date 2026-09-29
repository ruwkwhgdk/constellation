# 한손검 첫 타 — 오른쪽에서 왼쪽으로 수평 베기

기존 `/Game/Resources/Characters/PC/Player_Heroine/Animation/AM_Sword_Attack_Horizontal`과 그 안의 `Sword_Attack_Horizontal`을 참조한 첫 검토본입니다. 원본의 준비·베기·후속 회전·회수 흐름을 새 캐릭터에 옮기고 발 접지, 과도한 머리 기울기, 치마 추종을 보정했습니다. 캐릭터의 체형·얼굴·텍스처는 수정하지 않았습니다.

## 사용 리소스

- 애니메이션: `/Game/Resources/Characters/PC/player_heroine_new/Animations/AS_player_heroine_new_Attack01_Horizontal`
- 몽타주: `/Game/Resources/Characters/PC/player_heroine_new/Animations/AM_player_heroine_new_Attack01_Horizontal`
- 프리뷰 메시: `SK_player_heroine_new_RunPreview` — 기존 치마 웨이트 보정이 적용된 메시입니다.
- 편집 원본: `Heroine_Attack01.blend`
- 미리보기: `Attack01_Preview.gif`, 주요 자세: `Attack01_KeyPoses.jpg`
- 60fps, 1.0초, In-place, Play Rate 1.0. 몽타주 DefaultSlot, Blend In 0.08초 / Out 0.12초.

Blender 프리뷰에는 기존 `SM_Weapon_Sword` 메시를 검토용 0.5배 크기로 장착했습니다. 게임의 무기 크기·소켓·장착 로직은 변경하지 않았습니다. 언리얼 애니메이션 FBX는 스켈레톤 애니메이션이며 검 메시를 포함하지 않습니다. 게임 적용 시 실제 무기 장착 변환을 맞춰 검 궤적과 판정을 재검증해야 합니다.

## 콤보 연결 기준

| 시간 | 몽타주 알림 |
|---|---|
| 0.35초 | Hitbox On |
| 0.50초 | Hitbox Off / ComboWindow Open |
| 0.65초 | ComboWindow Close |
| 0.99초 | End Attack |

알림은 `AnimNotify_PlayMontageNotify`의 이름으로 저장했습니다. 위 시간은 초 단위이며 실제 데미지 실행이나 입력 버퍼 자체를 구현하는 코드는 아닙니다. 게임의 Play Montage/AnimInstance 처리 방식에 맞게 연결해야 합니다. 시퀀스의 동기화 마커에도 동일한 타이밍이 있지만 마커는 판정 이벤트를 실행하지 않습니다.

후속 입력은 0.50~0.65초에서 다음 타로 전환하는 구조를 제안합니다. 입력이 없으면 1초까지 회수 동작을 재생합니다. 0.50초(31프레임)의 편집 컨트롤을 `combo_handoff_pose.json`으로 저장했습니다. 2타는 이 후속 회전 자세를 시작점으로 삼고 약 0.08초 블렌드를 출발값으로 평가합니다. 2타·3타가 아직 없으므로 실제 연속 공격의 자연스러운 연결을 검증했다는 의미는 아닙니다. 입력 창 여러 시점에서 모두 연결을 시험해야 합니다.

## 검증 범위

- 120Hz, 프레임 사이 포함 121개 샘플 검사.
- 최소 신발 바닥 높이 약 +0.32mm, 무릎 굽힘 왼쪽 약 40~69도 / 오른쪽 39~57도.
- 검사한 치마 정점과 허벅지 방사형 외곽 사이 최소 여유 약 +1.36mm. 모든 삼각형 충돌을 보장하는 검사는 아닙니다.
- 검날 중심선은 30Hz 주요 프레임에서 캐릭터 메시와 교차하지 않았습니다. 검날 전체 부피·외부 적·환경 충돌 검증은 별도입니다.
- 전체 30프레임 렌더와 주요 자세를 시각적으로 확인했습니다.
- 언리얼 저장본의 길이·배속·스켈레톤·몽타주 세그먼트·알림 시간·원본 보존·소스 SHA256은 `unreal_verification.json`에 기록합니다.
- 기존 전투 블루프린트, 데미지, 입력, 원본 몽타주는 변경하지 않았습니다. 실제 게임 전환과 무기 판정은 후속 연결 작업입니다.

## 편집 재현 및 주의점

다음 국소 수정은 최종 `.blend`에서 시작합니다. 완전 재생성이 필요한 경우에만 `build_attack.py` → `polish_attack.py` → `fit_garment.py` → `finalize_attack.py` 순서로 실행합니다. `fit_garment.py`는 수치 계산이 오래 걸릴 수 있습니다. 중간 단계를 최종 파일에 임의로 누적 적용하지 마십시오.

원본 FBX의 첫 애니메이션 자세가 bind pose에 반영되므로 보존된 중립 스켈레톤을 회전 보정 기준으로 사용했습니다. 부모 컨트롤부터 회전을 적용해야 상체의 의도치 않은 추가 기울어짐을 피할 수 있습니다. 의상은 골반 기준 앞뒤 회전만으로 부족해 실제 허벅지의 3차원 방향과 표면 여유를 사용했습니다.

검 FBX 임포트는 장면 FPS를 25로 바꿉니다. `finalize_attack.py`가 60fps·1~61프레임을 명시적으로 복원하고 `validate_attack.py`가 이를 검사합니다.

익스포트는 `export_attack.py`, 언리얼 임포트는 `import_attack.py`(몽타주 생성은 `fix_montage.py`), 저장본 검증은 `verify_unreal.py`입니다. Blender CLI는 루트 AGENTS.md에 따라 `tools/run-blender.ps1`로 실행합니다. 미리보기는 `render_attack.py '--' all` 후 일반 Python으로 `encode_preview.py`를 실행합니다.
