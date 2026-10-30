# 자판기 전용 전기 피격 VFX

2026-10-31. BP_Vending_Machine의 짧은 접촉 불량 표현을 위한 전용 효과입니다. 에셋 제작 및 저장본 PIE 기능 검수 완료. 실제 BP 적용은 연결 담당 채팅에서 수행합니다.

## 제작 후보와 연결 계약

- 자산: `/Game/Constellation/VFX/Vending/P_VendingMachine_Hit.P_VendingMachine_Hit`.
- 타입: `UParticleSystem` (Cascade CPU sprite).
- 재질: `/Game/Constellation/VFX/Vending/M_VendingMachine_Hit.M_VendingMachine_Hit`.
- 권장 스케일: `FVector(0.15)` — 기존 자판기 코드와 동일. Sprite 전체 사각형은 36cm이며 전기 아크는 그 내부 약 20–26cm를 사용합니다.
- 수명/EmitterDuration: 0.34초. Emitter 1개, burst 1개, rate=0, loops=1, autoDeactivate=true.
- 기존 OutletOffset `(65,0,75)`를 변환한 월드 위치에서 `SpawnEmitterAtLocation(..., true)`로 재생합니다.
- 청백색 꺾인 아크가 세 구간으로 끊겨 나오고 작은 점 불꽃이 사라집니다. 색·밝기·크기는 제작자 선정 후보이며 최종 아트 승인과 구분합니다.
- 기존 0.4초 강제 종료보다 짧습니다. 기본 3회 피격 중 마지막 피격도 동일 효과를 사용합니다.
- 조명/발광 깜박임, 캔 분출, 피해 판정 및 BP 연결은 담당 채팅의 범위입니다. 이 효과는 별도 조명·사운드를 만들지 않습니다.

## 제작 원본

원본 보존 위치: 형제 Art 저장소 `ArtSource/VFX/VendingMachineHit/2026-10-31/`.
`VendingHitAuthoring.cpp`, `create_vending.py`, `review_vending.py`를 사용합니다. 제작용 명령은 분리된 검증 프로젝트의 편집기 모듈에서만 실행하며 게임 런타임에는 위 두 uasset만 필요합니다. 외부 텍스처나 제작용 플러그인을 요구하지 않습니다.

## 검증 범위

독립 검증 프로젝트 증분 빌드는 성공했습니다 (`Saved/VendingHitVFX/20261031/build.log`). 최초 편집기 실행은 Python 실행 전 엔진 `InheritedContext.cpp` assertion으로 종료 코드 3을 반환했습니다 (`create.log`). 에셋 오류로 단정하지 않으며 실패 기록을 보존합니다.

두 번째 실행은 HLSL 예약어 `line`을 변수명으로 사용한 오류를 컴파일 단계에서 잡았습니다. 저장 전에 중단했으며 `arcMask`로 수정했습니다. 최종 `create03.log`에서 재질 컴파일 오류 없이 저장 성공, `VENDING_HIT_CREATED saved=1`, `VENDING_HIT_ASSETS_READY` 및 종료 코드 0을 확인했습니다. 첫 엔진 초기화 오류는 재실행에서 재현되지 않았으며 근본 원인을 확정하지 않았습니다.

`Saved/VendingHitVFX/20261031/Review-20261031-033623/result.json`: passed=true, `review01.log` 프로세스 종료 코드 0.

- 새 편집기에서 저장된 ParticleSystem/Material을 재로드했습니다.
- 입자 1개 생성, 수명 종료 후 입자 0개 및 system inactive 확인.
- 정상 배속 3회 호출 후 각 효과 종료, 8개 동시 호출 후 활성 효과 0개 확인.
- 밝은/어두운 배경에서 3개 시점 및 종료 후 총 7장 직접 확인. 전기선 배열이 변하고 종료 후 잔여 표시가 없습니다.
- 사진은 0.2배속 후 정지한 명목상 0.045/0.155/0.265초 상태입니다. 정확한 프레임 타임코드나 정상 속도 영상 평가로 간주하지 않습니다.
- 비교 장면은 기존 자판기 메시 자체를 기본 크기로 놓은 임시 월드입니다. BP의 컴포넌트 변환·조명·피격·캔 분출은 실행하지 않았습니다. 근접 구도에서는 자판기 하단이 프레임 밖에 있습니다.
- 비스듬한 시점에서 표면 가까운 일부 아크는 깊이 검사로 가려집니다. 실제 BP 적용 후 가독성이 부족하면 **이펙트 생성 위치만** `Outlet + GetActorForwardVector()*10~15cm`로 조정하는 후보를 검토합니다. 캔 분출 위치나 OutletOffset 자체를 자동 변경하지 않습니다. 현재 납품 검수는 기존 (65,0,75), scale 0.15 기준입니다.

실제 BP 피격·조명·캔과의 동기화 및 패키지 콜드 스타트/30·60 FPS 성능은 연결 담당의 후속 검증입니다. 이 검사 결과로 전체 게임 성능을 보증하지 않습니다.

## 저장본 해시

- M_VendingMachine_Hit.uasset: `A6690E74EEC595C6C2DB04C579D4A1719A973CE48C7084AAD98D5C63B05FDA22`
- P_VendingMachine_Hit.uasset: `A848D2AE66C8F1A5814786765EB919DA0946A577BBABBE15553EF0BEFAD2CC6E`

이 에셋과 납품 문서는 079fe983 이후 별도의 자판기 VFX 커밋으로 관리합니다. BP 연결 및 자판기 런타임 코드는 이 납품 범위에 포함하지 않습니다.

## 전체 구도 추가 검수

`Review-20261031-033820/result.json`도 passed=true입니다. 자판기 전체 크기가 보이는 구도에서 밝음/어둠의 세 시점과 종료 후 이미지 7장을 직접 확인했습니다. 신규 에셋은 변경하지 않았습니다. 작은 국소 전기선으로 읽히며, 재질 자체의 흰 인쇄 영역과 겹치는 일부 선은 대비가 낮습니다. 실제 BP에서는 배출구/접점 부위에 맞추는 최종 위치 검수가 필요합니다. `review02.log`에 정상 엔진 종료 기록이 있으며 프로세스 종료 코드 0을 확인했습니다.
