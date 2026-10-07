# Constellation 전투와 환경 이펙트 사용 안내

요청한 검 공격·타격·방어·패링, 슬라임 공격·피격, 유리 파괴, 달리기 흙먼지, 동굴 환경 효과를 프로젝트에 추가했습니다. 기존 전투의 확정 판정과 연출 종료 이벤트에 연결했으며, 효과 자체는 피해를 적용하지 않습니다.

## 바로 확인하기 — 통합 갤러리

`Play-VFX.cmd` 또는 `/Game/Constellation/Review/VFX/L_VFXGallery`를 열어 Play로 실행합니다. Simulate가 아닌 Play에서 마우스를 뷰포트에 클릭하면 조작할 수 있습니다. 셰이더 컴파일이 끝난 뒤 2초 동안 이펙트 렌더 자원을 준비합니다. 준비 중에도 자유 이동은 가능합니다.

이제 VFX 검토 맵은 L_VFXGallery 하나입니다. 이전 Combat/Cave 검토 맵은 `Saved/VFXImplementation/GalleryRevisionBefore`에 백업한 뒤 Content에서 제거했습니다. 기존 학교와 전투 테스트 맵은 유지합니다.

| 조작 | 동작 |
| --- | --- |
| WASD + 마우스 | 갤러리 자유 비행 및 시점 회전 |
| E / Q | 위 / 아래 이동 |
| 1~9, 0 | 해당 구역으로 이동하고 효과 재생 |
| PageUp / PageDown | 이전 / 다음 구역 |
| Enter | 선택 효과 다시 재생 |
| R | 반복 켜기 / 끄기 |
| F | 선택 구역의 기본 관찰 위치로 복귀 |
| Shift+F1 | 에디터 Play에서 마우스 해제 |

| 번호 | 효과 |
| --- | --- |
| 1 | 검 휘두르기와 궤적 |
| 2 | 검 명중 |
| 3 | 검 막기 |
| 4 | 검 패링 |
| 5 | 슬라임 공격 |
| 6 | 슬라임 피격: 표면 앞 젤 입자와 타격 섬광 |
| 7 | 플레이어 피격: 붉은 접점 섬광과 작은 파편 |
| 8 | 유리 파괴 |
| 9 | 달리기 흙먼지 |
| 0 | 동굴 안개·먼지·포자·낙수·물결 |

전시용 크기와 위치로 효과를 비교하는 맵입니다. 검은 표시용 궤도로 움직이고, 히로인은 기존 PreviewRelaxed의 고정 포즈로 표시합니다. 실제 전투 판정·캐릭터 공격 애니메이션을 테스트하는 모드는 아닙니다. PlayerHit는 슬라임의 실제 확정 명중 이벤트에도 연결했습니다. 갤러리와 실제 전투는 같은 이펙트 종류별 색·크기와 검 궤적 컴포넌트를 사용합니다.

일반 플레이는 스크린샷을 자동 저장하지 않습니다. 유리는 렌더 자원을 미리 준비하고 한 판을 재사용하며, 반복 간격을 4초로 두어 파편이 누적되지 않습니다.

```powershell
.\tools\play-vfx.ps1 -Mode Gallery
.\tools\play-vfx.ps1 -Mode Gallery -Capture  # 10개 구역 촬영 후 종료
.\tools\play-vfx.ps1 -Mode Probe -Capture    # 촬영 없이 이동/유리 반복 프레임 측정
```

`Glass`, `Benchmark`는 같은 갤러리 맵에서 실행하는 개발용 진단 옵션입니다. 재설정 스크립트 `tools/setup-vfx-review.py`는 갤러리 내부를 재작성하므로 수동 수정 전 백업이 필요합니다.

## 적용 내용

| 효과 | 구현과 연결 |
| --- | --- |
| 검 공격 | 검 끝의 최근 최대 0.18초 이동을 잇는 단일 얇은 궤적. 기존 Niagara와 굵은 보조 궤적의 중복 표시를 제거. 공격 유효 구간에만 생성하고 취소·피격·사망 시 정리 |
| 검 타격 | 실제 피해가 수락된 접점에서 섬광·스파크. 큰 슬라임 내부에 가려지는 접점은 표시 위치만 메시 경계 쪽으로 이동 |
| 방어와 패링 | 작은 방어 섬광과 더 강한 패링 섬광·방향성 스파크 및 연출 호출 경로. 방어·패링 게임 규칙이나 입력은 새로 추가하지 않음 |
| 슬라임 공격과 피격 | 검 진행 방향으로 늘어난 보라색 젤 방울과 짧은 절단 섬광. 슬라임 피격은 한 묶음만 발생하며 별도 금속 타격을 중복 생성하지 않음 |
| 플레이어 피격 | 슬라임의 확정 명중 시 별도 PlayerHit 효과. 실제 피해값·판정 시점은 유지 |
| 유리 파괴 | 기존 `BP_Glass`의 Chaos 파괴를 감지해 삼각 파편 생성. 임시 SimpleExplosion 참조만 제거하고 물리·소리 연결 보존 |
| 달리기 먼지 | 지면 위 이동 거리·속도로 발생. 공중·공격·회피·사망 상태에서 억제. 물 표면은 물결로 대체 |
| 동굴 | 국소 먼지·저층 안개·물방울·물결, 버섯 구간 포자. 카메라 거리로 발생 범위 제한 |

기존 학교 맵 `/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool`의 동굴 기준점 다섯 곳에 `VFX_Ambience_*`를 배치하고 `VFX_GlassFractureRelay`를 추가했습니다. 다른 맵에 기존 BP_Glass를 새로 배치한다면 `ConstellationGlassRelay`도 한 개 배치해야 파편 효과가 연결됩니다.

현재 유지 중인 `L_CombatCore`, `L_CombatEncounter`, `SlimeScout_v2/L_Preview`의 전투 캐릭터에서도 표시를 켰습니다. 해당 전투 컴포넌트 밖의 별도 캐릭터·블루프린트 전투 체계에 자동 연결되는 것은 아닙니다.

## 조절과 연출 연결

- 캐릭터 `CombatVFX`에서 Presentation Enabled, SwordColor, SlimeColor, FootstepDistance, MinimumDustSpeed 및 표면별 SurfaceEffects를 조절합니다.
- 지면 컴포넌트의 `FXNoDust` 태그는 먼지를 끄고, `FXWater`는 물결을 선택합니다. 기본 발자국은 이동 거리 방식이며 발 애니메이션 Notify와 완전히 일치하는 방식은 아닙니다.
- 동굴 액터에서 Radius, ActiveDistance, Mist, Spores, Drips, MistColor, SporeColor를 조절합니다.
- SceneDirector의 Actions 목록에 `ConstellationSceneFXAction`을 등록하고 대상 Object/NPC를 연결합니다. Identifier는 `SwordHit`, `SwordBlock`, `SwordParry`, `SlimeAttack`, `SlimeHit`, `PlayerHit`, `RunDust`, `GlassBreak`, `GlassReset`, `CaveEnable`, `StopEffects` 등을 사용합니다. 일반 효과는 Value가 크기, CaveEnable은 Flag가 켜짐 상태입니다.
- `GlassBreak`/`GlassReset` 연출 액션의 대상은 새 `ConstellationGlass` 액터입니다. 기존 `BP_Glass`는 자신의 OnBreakObject 물리 파괴 경로와 relay를 사용합니다.
- 연출 취소 시 새 유리의 파손 상태와 동굴 켜짐 상태를 시작 전으로 복원합니다. 정상 완료된 유리 파괴는 유지합니다. 동시에 다른 연출이 같은 유리를 제어하는 요청은 거절합니다.

소스는 `Plugins/ConstellationVFX`, 전투 연결은 `Plugins/ConstellationCombat`에 있습니다. 재질·삼각 파편·재사용 Niagara는 `/Game/Constellation/VFX`에 모았습니다. 전부 Niagara 그래프인 패키지는 아니며, 공통 입자는 수명이 제한된 네이티브 인스턴스 메시 방식으로 구현했습니다. 외부 유료 리소스 구매나 계정 가입은 하지 않았습니다.

## 전투 이펙트 폴리시

검 궤적, 절단 섬광, 금속 타격, 별 모양 충격 섬광, 젤 방울용 재질 5종을 추가했습니다. 입자 개수를 늘리기보다 접점·방향·짧은 수명으로 구분했습니다. 갤러리의 표시용 접점은 현재 관찰 Pawn 위치로 계산하여 구역 전환 직후 이전 카메라 때문에 효과가 몸 밖으로 떨어지던 문제도 수정했습니다.

이번 범위는 VFX 표현과 확정 명중 연결입니다. 타격음, 히트스톱, 새로운 피격 애니메이션은 추가하지 않았으며, 소울라이크 수준의 종합 타격감은 이 요소들을 함께 조정해야 합니다. 전투 리뷰 장면의 기존 슬라임 변형과 캐릭터 애니메이션도 이번 수정 대상에 포함하지 않았습니다. 슬라임의 실제 메시와 충돌 캡슐의 간격이 커서 전투 검토 장면의 접점은 추가 애니메이션·충돌 정합 작업이 필요합니다.

짧은 효과는 생성되기 전 프레임 시간을 수명에서 차감하지 않도록 보정했고, 입자 갱신에서 렌더 객체 전체 재생성을 제거했습니다. 플레이어 피격 섬광은 단일 메시로 표시하며 첫 0.065초 동안 접점 형태를 유지한 뒤 약 0.14초에 걸쳐 사라집니다. 초기의 즉시 감쇠 상태는 오프스크린 전투 캡처에서 표시가 불안정했고, 최종 일반 재생 캡처에서 비정지 상태의 붉은 피격 섬광을 확인했습니다. PSO/안티앨리어싱 옵션 변경은 진단 실행에만 사용했으며 프로젝트 설정에는 적용하지 않았습니다.

이전 파일과 비교용 캡처: `Saved/VFXImplementation/CombatPolishBefore`. 재질 재생성 도구: `tools/polish-combat-vfx-materials.py`.

## 가독성 재조정 (2026-10-06)

사용자 피드백에 따라 검 궤적 폭을 6cm에서 24cm, 수명을 0.10초에서 0.18초로 늘렸습니다. 폭과 투명도의 감쇠도 완만하게 바꾸고, 프레임마다 전체 인스턴스를 지우는 대신 기존 조각을 갱신합니다. 조각을 최소 0.012초 간격으로 기록해 높은 프레임률에서도 궤적이 검 끝에 몰리지 않도록 했습니다. 순간이동 연결 방지와 최대 15개 표시 조각 제한은 유지합니다. 검 궤적 재질의 양 끝을 부드럽게 감쇠하고 과도한 발광도 낮췄습니다.

공유 기준 크기: 검 명중 2.4배, 방어 2.8배, 패링 2.4배, 슬라임 공격 2.5배, 슬라임 피격 2.3배, 플레이어 피격 1.6배. 흙먼지는 입자 크기만 2배로 확대합니다. 갤러리와 실제 전투에 함께 적용하며 유리 파괴·동굴 효과의 크기는 유지합니다. 갤러리 검 시연은 카메라에서 호가 보이는 세로 평면으로 변경했습니다. 기존 수평 평면에서는 궤적 조각이 화면에 겹쳐 보였습니다. 실제 전투 애니메이션은 변경하지 않았습니다. 비교 전 원본은 `Saved/VFXImplementation/ReadabilityBefore`에 보관했습니다.

가독성 수정 빌드와 VFX/CombatVFX 검증 16개 통과. 로그: `Saved/Logs/VFX-readability-build.log`, `VFX-readability-tests.log`. 갤러리와 실제 전투의 재촬영 로그는 `VFX-gallery-render.log`, `VFX-readability-combat.log`입니다. 검증 도중 렌더러 작업 스레드의 접근 위반이 한 번 발생했으며, 이후 동일 조건의 갤러리 재실행은 정상 완료했습니다.

## 폴리시 검증 기록 (2026-10-06)

최종 개발 빌드: `Saved/Logs/VFX-polish-build.log`. 자동 검증: `Saved/Logs/VFX-polish-tests.log` (VFX 및 CombatVFX 16개). 신규 검증은 대상별 효과 분기, 중복 타격 이펙트 방지, 원본 명중 정보 보존, 검 궤적 순간이동 방지·수명·최대 조각 수를 포함합니다. 생성 직전의 긴 프레임이 새 효과의 수명을 소모하지 않는지도 검사합니다.

실제 전투 일반 재생: 검 명중 2회, 슬라임 명중 1회, PlayerHit 효과 1개, 달리기 먼지 3회, 공격 취소 정리 통과. `combat-runtime-review.json`의 `passed`는 동작 검증이며 미적 완성도 평가가 아닙니다. `combat-slime.png`는 슬라임의 공격으로 **플레이어가 맞는 장면**이고, `combat-sword.png`는 슬라임이 검에 맞는 장면입니다. 예전 `combat-slime-attack.png`는 이번 최종 실행에서 갱신하지 않아 최종 검증 근거로 쓰지 않습니다. 정지 진단 이미지 `combat-slime-frozen-probe.png`도 최종 일반 재생 결과와 구분합니다.

## 이전 통합 갤러리 검증

개발 빌드 및 VFX 자동 검증 5개 통과. 저장된 auto-review 옵션이 있어도 일반 플레이를 고정 카메라로 바꾸지 않는지, 별도 PlayerHit가 생성되는지, 유리 20회 즉시 재생에도 살아 있는 파편 묶음이 1개인지, 일반 재생에서 촬영 요청이 없는지 확인했습니다.

실제 1280×720 오프스크린 실행에서 10개 구역을 촬영하고 확인했습니다. 별도의 촬영 없는 실행에서는 Pawn이 이동 입력으로 실제 이동하고, 카메라가 Pawn을 따르며 이동·시점 입력이 잠기지 않았음을 확인했습니다. 유리 8회 반복에서 최초 4초를 제외한 5,336프레임은 평균 5.248ms, p95 8.162ms, 최대 11.431ms였습니다. 이 수치는 갤러리 전체 프레임 시간이며 게임 전체 성능 보장은 아닙니다.

결과: `Saved/VFXReview/gallery-probe.json`, `gallery-capture.json`, `gallery_00.png`~`gallery_09.png`. 검증 로그: `Saved/Logs/VFX-gallery-tests.log`, 빌드 로그: `Saved/Logs/VFX-gallery-build.log`.

## 이전 구현 검증 기록

Unreal Editor 개발 빌드와 최종 이펙트·전투·연출 연결 테스트 16개가 모두 통과했습니다. 최종 테스트 로그는 `Saved/Logs/VFX-final-scope-tests.log`입니다. 테스트는 확정 피해만 반응하기, 한 공격의 중복 타격 방지, 취소·사망 정리, 지면/물/공중 발자국, 실제 연출 재생·중단·재시작·완료, 유리 초기 상태 및 소유권 복구를 포함합니다.

실제 전투의 첫 사용 비교 재생은 검 2회·슬라임 1회 명중, 측면 달리기 먼지 3회, 공격 취소 정리를 확인했습니다. 첫 타격부터 표시되도록 공격이나 피해 없이 화면 밖에서 렌더 자원을 준비하며, 준비용 효과는 1.1초 이내에 소멸합니다. 기존 유리 블루프린트의 OnBreakObject를 실행해 실제 Chaos 이벤트와 relay 효과 발생도 확인했습니다. 스크린샷은 `Saved/VFXImplementation/combat-*.png`, 개별 효과·유리·동굴은 `Saved/VFXReview`에 있습니다.

동시 부하는 RTX 4070, 1280×720, 오프스크린 게임 실행에서 측정했습니다. 4초 준비·4초 기준 측정 후, 12종 효과 24개를 0.65초 간격으로 발생시키고 1초 안정화 뒤 6초 측정했습니다.

| 항목 | 측정값 |
| --- | --- |
| 기준 평균 프레임 시간 | 3.95 ms |
| 부하 평균 프레임 시간 | 5.91 ms |
| 부하 p95 프레임 시간 | 7.78 ms |
| 최대 동시 효과 액터 | 92 |
| 최대 파티클 인스턴스 | 1196 |

이는 해당 검증 장면의 전체 프레임 시간이며 GPU 이펙트 비용만 분리한 값이나 전체 게임의 성능 보장은 아닙니다. 효과 액터는 최대 160개로 제한했고, 검 보조 궤적은 최대 16조각으로 제한했습니다. 패키징용 VFX 디렉터리 cook 설정은 추가했으며 배포용 패키지 빌드는 이번 검증에 포함하지 않았습니다.

Unreal 5.8 Experimental NiagaraToolsets의 게임 실행용 Python 초기화 오류가 기존 환경에서 출력됩니다. 이번 이펙트 셰이더 실패와 구분했으며 실제 실행·이미지·테스트 결과로 확인했습니다.

## 보존과 재현

원본 코드·맵·BP_Glass·설정의 작업 전 백업은 `Saved/VFXImplementation/Before`에 있습니다. 기존 미커밋 변경을 보존했고 커밋하거나 프로젝트 전체를 정리하지 않았습니다.

재료 생성은 `tools/setup-vfx-materials.py`, 검토 맵은 `tools/setup-vfx-review.py`, 기존 장면 연결은 `tools/integrate-vfx-scenes.py`, 유리 임시 폭발 정리는 `tools/fix-vfx-glass-placeholder.py`에서 재현할 수 있습니다. 이들은 Unreal Python 스크립트입니다. 유리 정리는 정확히 확인한 노드만 수정하고, 다른 그래프 연결이나 에셋은 거절하도록 제한했습니다.

## 연속 궤적·방향별 피격 반응 (2026-10-06)

사용자 후속 지시에 따라 슬라임 모델링·애니메이션·충돌 캡슐 조정은 보류했습니다. 슬라임 에셋과 기존 전투 맵을 덮어쓰지 않고, 이번에는 검 궤적, 플레이어 피격 반응, 슬라임 타격 이펙트 접점만 수정했습니다.

- 검 궤적: 조각 평면 대신 꼭짓점을 공유하는 연속 곡면 띠를 사용합니다. 시간 샘플 사이를 곡선으로 보간하고 UV와 투명도를 띠 전체에 연결했습니다. 0.18초 수명, 16개 시간 샘플, 순간이동 연결 방지는 유지합니다. 기존 맵의 직렬화 호환성을 위해 원래 ISM 컴포넌트 안에 일시적인 ProceduralMesh 자식을 두며, 등록 해제·파괴 시 함께 정리합니다. 재질은 `M_FX_SwordRibbon`입니다.
- 슬라임 접점: 메시 전체 경계 상자 바깥으로 밀어내는 대신, 명중 순간 현재 뼈대 변형을 적용한 삼각형 표면을 찾습니다. 최대 1,024개 삼각형만 조사하며 GPU 읽기나 렌더 동기화는 하지 않습니다. 기존 명중 정보·피해·충돌 판정은 바꾸지 않습니다. 실제 전투 검사에서 원래 접점으로부터 약 5.0~6.4cm 보정되었습니다.
- 플레이어 피격: `Sword_Damaged`의 상체 회전 변화를 현재 유지 중인 Refined 뼈대에 변환한 Front/Back/Left/Right 4종을 추가했습니다. 이동·하체·발·치마 트랙은 기존 Relaxed 자세를 유지합니다. 에셋은 원본과 같은 24fps/1초이며 기존 피격 시간 0.35초에 맞춰 재생합니다. 앞/뒤/좌/우 최대 반응 방향을 실제 본 위치로 측정해 보정했습니다.
- 확정 피해만 피격 모션을 시작합니다. 무적·거절된 피해는 반응하지 않으며, 연속 피격·취소·복귀·사망 시 정리합니다. 취소된 공격 몽타주를 피격 종료 후 다시 재생하지 않고 대기 자세로 돌려줍니다.

확인은 `Play-VFX.cmd`로 기존 `L_VFXGallery`를 실행합니다. **1번**은 연속 검 궤적, **7번**은 플레이어 피격입니다. 7번에서 **H**로 Front → Back → Left → Right를 바꿀 수 있고, 화면에 현재 타격 방향을 표시합니다. **Enter** 재생, **R** 반복, **F** 구역 맞춤, 기존 WASD/마우스 자유 이동을 유지합니다. 새 검토 맵은 추가하지 않았습니다.

검증: 최종 개발 빌드 성공, `Constellation.VFX`, `Constellation.CombatVFX`, `Constellation.CombatCore` **74개 통과**. 로그는 `Saved/Logs/VFX-continuity-build.log`, `VFX-continuity-tests.log`입니다. 실제 전투 검사에서 검 2회·슬라임 1회 명중, PlayerHit 1개, 먼지 3회, 취소 정리가 통과했고 피격 캡처 시 새 Front 클립의 실제 재생을 확인했습니다. 갤러리 10개 구역과 4방향 반응/복귀 비교를 촬영했습니다. 방향 비교 촬영만 `-UseFixedTimeStep -FPS=60`을 사용하며 일반 플레이 설정에는 적용하지 않습니다.

재현 도구: `tools/generate-combat-hit-reactions.py`, `tools/audit-hit-reaction-directions.py`, `tools/polish-combat-vfx-materials.py -OnlySwordRibbon`. 통합 생성은 `tools/setup-vfx-continuity.py -OnlySwordRibbon`입니다. 신규 애니메이션은 `/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_Hit_{Front,Back,Left,Right}`에 있습니다. 기존 모델·원본 공격·원본 피격 애니메이션은 수정하지 않았습니다.

남은 표현 범위: 현재 피격은 짧은 상체 반응이며, 공격 중 피격으로 전환할 때 임의의 현재 포즈에서 부드럽게 섞는 전용 애니메이션 그래프는 아직 없습니다. 슬라임 접점의 삼각형 검사는 뼈대 변형만 반영하며 morph/WPO는 포함하지 않습니다. CPU 메시 데이터가 없는 패키징 에셋은 원래 접점으로 대체하므로 향후 슬라임 교체·패키징 단계에서 다시 확인해야 합니다. 타격음·히트스톱·카메라 흔들림과 슬라임 자체의 변형 품질은 이번 범위 밖입니다.

이전 비교 이미지는 `Saved/VFXImplementation/ContinuityBefore`에 있습니다. 검토 과정에서 기존 맵/컴포넌트 직렬화 불일치와 새 애니메이션 샘플링 설정 충돌이 발견되어 수정했습니다. 최종 갤러리는 원래 맵을 유지한 상태에서 정상 실행되었습니다.
