# BP_DropItem 전용 획득 VFX — 제작 후보 인계

작성: 2026-10-30. 이 문서는 전용 에셋 제작과 검수를 기록합니다. 실제 지급·저장·흡수 이동·UI 및 BP 연결은 `docs/drop-items.md` 담당 범위입니다.

## 의도와 승인 범위

사용자 요청은 몸 접촉 후 지급 저장이 성공했을 때 재생할 전용 획득 이펙트입니다. 청록/빨강/노랑 캔은 같은 재화이므로 동일 효과를 사용합니다. 색·형태·시간은 아직 사용자 최종 승인을 받지 않은 제작 후보입니다.

후보 표현은 작은 아이보리색 고리가 접촉점으로 수렴한 뒤 부드러운 중심 빛으로 사라지는 0.36초 연출입니다. 검/피격 효과와 구분하도록 폭발·파편·십자 섬광·화면 흔들림·동적 조명·사운드를 넣지 않았습니다. 추가 흡수 이동이나 UI를 만들지 않습니다.

## 연결 정보

- 에셋 타입: `UParticleSystem` (Cascade CPU sprite).
- 재생 자산: `/Game/Constellation/VFX/Pickup/P_DropItem_Absorb.P_DropItem_Absorb`.
- 전용 재질: `/Game/Constellation/VFX/Pickup/M_DropItem_Absorb.M_DropItem_Absorb`.
- 권장 `EffectScale`: **0.35** (현재 DropItem 기본값 유지). 이 값에서 sprite 사각형 35cm, 가장 큰 가시 고리 지름 약 28cm입니다. 크기는 확정 밸런스가 아니라 조정 가능한 후보입니다.
- Emitter 1개, burst 입자 1개, rate=0, loop=1, duration/lifetime=0.36초, auto_deactivate=true. 무한 루프가 없습니다.
- `SpawnEmitterAtLocation(..., FVector(EffectScale), true)`의 autoDestroy=true를 유지합니다. 현재의 `PickupEffect` 속성에 직접 지정할 수 있으며 Niagara/새 런타임 타입은 필요 없습니다.
- `TryCollect`의 **저장 성공 후 분기에서 1회** 호출합니다. 실패/접근 시작/접촉 전에는 호출하지 않습니다. `Deactivate` 직전 저장한 Contact 위치를 사용하는 현재 코드와 호환됩니다. 부착형이 아니므로 빠르게 이동하는 플레이어를 따라가는 효과가 아닙니다.
- 최초/반복 획득 UI 종류, 캔 외형에 따라 효과를 중복 호출하지 않습니다. 효과는 재화 수량을 표현하지 않습니다.
- 이번 채팅에서는 `DropItem.cpp/.h`, 세 BP, 저장·UI 로직을 변경하지 않았습니다. 연결 담당이 임시 `P_Starcoin_Get`을 교체합니다.

## 제작 원본과 런타임 의존성

원본은 형제 Art 저장소 `ArtSource/VFX/DropItemPickup/2026-10-30/`에 보존합니다.

- `create_pickup.py`: 전용 절차적 재질 생성, 연결/컴파일 반환값 검사 및 제작 명령 호출. 기존 에셋 덮어쓰기 거부, 실제 RHI 필수.
- `DropPickupAuthoring.cpp`: 검증용 편집기 모듈에만 추가하는 에셋 생성 명령. Cascade 내부 모듈은 Python에서 보호되어 있어 C++에서 생성합니다. 기존 경로 덮어쓰기 거부.
- `review_pickup.py`: 별도 임시 PIE 검수. 실제 지급/UI를 실행하거나 저장 맵을 수정하지 않습니다.

게임에는 위 두 uasset만 필요합니다. 제작용 C++는 `Saved/CombatExpansion/vfx1`의 독립 편집기 모듈에만 빌드했으며 원본 게임 플러그인 소스를 수정하지 않았습니다. 에셋은 엔진 표준 ParticleSystem/Material만 참조하며 제작용 명령이나 Art 체크아웃이 런타임 의존성이 되지 않습니다.

## 검증

제작 도구 증분 빌드 성공: `Saved/DropPickupVFX/20261030/author-build-fixed.log`. 에셋 생성·GPU 재질 컴파일 성공: `create.log`, `DROP_PICKUP_CREATED saved=1` 및 `DROP_PICKUP_ASSETS_READY`.

최종 PIE 화면/종료 검증 결과는 아래에 추가합니다. 최초 검수 스크립트의 조명 접근 및 정리 호출 오류 기록은 보존했으며, 해당 실패 실행을 완료 근거로 사용하지 않습니다.

### 최종 결과

- `Saved/DropPickupVFX/20261030/Preview07/result.json`: **passed=true**. 별도 Editor/PIE 프로세스 정상 종료 코드 0 (`review07.log`). 실제 저장 uasset을 새 프로세스에서 로드했습니다.
- 한 번 호출하면 입자 1개가 생성되고, 원래 배속으로 복귀 후 수명이 끝나 활성 입자 0 / system inactive가 되는 것을 확인했습니다. 8개 동시 호출에서는 입자 합계 8개, 종료 후 활성 시스템 0개를 확인했습니다. 각 호출은 autoDestroy=true를 사용합니다. 이 검수는 메모리/GC 장시간 부하 측정이나 60 FPS 성능 보증이 아닙니다.
- `Preview07/bright-contact.png`, `bright-converge.png`, `bright-finish.png`, `dark-contact.png`, `dark-converge.png`, `dark-finish.png` 및 `after-expiry.png` 총 7장을 직접 확인했습니다. 고리가 작아져 중심 빛으로 사라지고 종료 후 잔여 표시가 없습니다. 밝은 옷과 배경에서도 고리 윤곽은 보이지만 마지막 중심 빛은 의도적으로 약합니다.
- 시각 검수는 기존 주인공 메시를 정적인 크기 기준으로 사용한 임시 PIE입니다. 캐릭터의 자세/애니메이션/리그는 수정하지 않았으며 해당 품질 검수로 간주하지 않습니다. 캡처는 0.2배 재생 후 일시 정지해 명목상 0.05 / 0.14 / 0.27초 모습을 비교한 것입니다. 프레임 단위 정확한 타임코드 측정이나 정상 속도 연속 영상은 아닙니다. 실제 본편의 움직이는 캐릭터·원거리 카메라·벽/바닥 접촉·지급/UI 동기화 검수는 연결 담당에게 남깁니다.
- 초기 검수 지연 중 PSO 생성 대기가 있었고, 준비 재생을 별도로 넣었습니다. 이후 반복 실패의 직접 원인은 검수 스크립트에서 `set_editor_property(custom_time_dilation)`을 사용해 컴포넌트를 재등록한 것이었습니다. 런타임 속성 접근으로 수정한 최종 실행에서 통과했습니다. 이 검수 코드 결함을 제품 에셋 결함으로 기록하지 않습니다. 콜드 스타트 비용/패키지 PSO 준비는 별도 확인이 필요합니다.
- 검수용 코드 오류(조명 속성 접근, 정리 API, 배속 속성 변경)의 실패 로그와 결과도 보존했습니다. 마지막 정상 실행만 납품 근거입니다.
- 새 에셋 제작 이후 원본 DropItem/BP에 자동 연결하지 않았습니다. 연결 담당에게 위 경로와 권장값을 전달하여 교체 후 실제 획득 동작을 확인합니다. 색/형태의 최종 아트 승인은 별도입니다.

최종 SHA256:
- `M_DropItem_Absorb.uasset`: `188891742439C58DAC658C92AC9BDD528151D9924DB7F5367FBAA46F5B20A238`
- `P_DropItem_Absorb.uasset`: `7DD298AF0F38F51660A7C3CA88C56F8C943B9DFFD4B6EAE4DE1D19D173151CE0`

이번 제작에서 커밋·푸시는 수행하지 않았습니다.
