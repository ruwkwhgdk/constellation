# OvergrownHall 현재 제작 상태

## 사용자 승인 · 2026-09-30

사용자가 최종 시각 결과를 승인했다. 다음 작업은 [재사용 제작 절차](Workflow/README.md)를 먼저 읽는다. 최종 TripoFull 맵과 v028 비교는 유지한다. 초기 런타임 프로토타입은 참조 검사 후 정리했으며 목록은 Workflow/asset_cleanup.json, 소스 임시파일은 Workflow/file_cleanup.json에 기록했다. 과거 생성 레시피는 이력/재생성 참고이고 폐기 맵의 존재를 보증하지 않는다. 플레이·성능 검증 상태는 별도다.


## 최신 유지 상태 · 원화 시각 기준 통과 (v028, 2026-09-29 22:27 KST)

유지 맵 `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`. 최신 비교 **`TripoReplacement/v028/review.html`**, 실제 렌더 `TripoReplacement/v028/unreal_acceptance.png`. 판정 근거는 `REFERENCE_ACCEPTANCE.md`. v023의 성급한 통과 판정은 철회했고 v024–028 실제 보정 후 다시 판정했다.

후면 창을 큰3칸+좌측 부분 창으로 보정하고 창/층 사이 띠·기둥 경계를 수정. 측면 상부 벽8개, 중간 보4개 재배치와 부착 잎4개, 후면 관목4개 교체·창 띠 잎3개, 하부 벽6개 색면 보정. 청록 수면과 우측 국소 채광을 보강하고 좌측 직사광 대비를 낮춘 뒤 기둥55개의 청록 중간 밝기를 복원했다. 최종755액터, 닫힌 천장50, 비둘기28/애니메이션140섹션, 후면 나무 제거 상태와 기준 카메라 유지.

저장 상태 검사/촬영: **`Content/Python/capture_hall_acceptance_color.py`**. 마지막 적용: `finish_hall_acceptance_color.py`. 누적 재현 순서는 `TripoReplacement/v028/STATUS.md`와 v027/STATUS.md. 상부 벽 소스는 `Scripts/build_hall_upper_wall_infill.py`와 v024의 최종 FBX454/462삼각형. Blender는 반드시 프로젝트 런처로 실행한다. 앞 단계 전체 재생성을 단독 실행하지 않는다.

통과 범위는 고정 카메라의 구도·명암·식생·물·폐허 형태다. 원화의 개별 붓터치·파손·광선/반사 윤곽과 동일하지 않고 사용자 최종 승인을 뜻하지 않는다. 원경·반사 일부와 식생/벽 밝기는 미술용 발광 보조를 사용한다. 직접 플레이는 사용자 담당이며 게임 성능/다른 플레이 시점/날개 충돌은 미검증. 평면 반사 해상도75%의 비용은 새로 측정하지 않았다.

## 유지 기반 · 원화 재현 판정 재검토 (v023, 2026-09-29)
유지 맵 `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`. 최신 비교 `TripoReplacement/v023/review.html`, 실제 렌더 `unreal_reference_final.png` (04:29:56 KST). v021 아치6·지붕틀3 파손/처진 부재6/비둘기28 실루엣, v022 잎127·기둥55 색면, v023 빛·수면 반사 균형/바닥과 이어지는 후면 잎4/측면 나무10을 X±1600으로 이동/창 너머 녹색 원경. 닫힌 천장50, 카메라, 공간 치수, 비둘기 리깅·경로·140애니메이션 섹션 유지. 총739액터. 최신 적용 `Content/Python/balance_hall_reference_final.py`, 저장 검사/촬영 `capture_hall_reference_final.py`. 형태 제작은 `Scripts/build_hall_silhouette_finish.py`(Blender 런처), 적용 `finish_hall_silhouettes.py`; 색면 `finish_hall_color_masses.py`. 이전 단계는 단독 재실행하지 않는다.
에이전트의 고정 카메라 시각 판정은 `REFERENCE_ACCEPTANCE.md`: 이전 통과 판정은 재검토로 보류. 큰 후면 창 구성과 중간 구조, 식생 덩어리, 안개광 차이에 대해 추가 보정 진행. 원화와 동일한 붓터치·창 구성·파손 위치는 아니며 사용자 최종 승인을 뜻하지 않는다. 실제 렌더 및 저장 검사 통과, 플레이·게임 성능·날개 충돌 미검증. 수면 일부와 원경·잎 밝기에는 미술용 발광 재질을 사용. 자세한 레시피·한계는 v023/STATUS.md.
## 최신 · 채광·식생 간격·잔잔한 수면 (v020, 2026-09-29)
유지 TripoFull 맵. 비교 `TripoReplacement/v020/review.html`, 실제 렌더 `unreal_atmosphere_finish.png`. 관목16배치 제거·51크기 보정·벽 잎13군집 확장. 좌측 직사광 완화, 우측 스포트 범위/밝기 보정, 벤치 보조광 추가, 원경 좌우 색온도/밝기 차이. 수면 노멀·평면 반사 왜곡을 낮추고 큰 발광 얼룩을 얇은 물결 마스크로 교체. 기존 카메라/공간 치수/천장50/비둘기28 유지. 적용 `Content/Python/refine_hall_light_foliage_water.py`, 조명만 `balance_hall_atmosphere_finish.py`, 저장 검사/실제 촬영 `capture_hall_atmosphere_finish.py`. 최종729액터 및 범위 밖 변환/메시 유지 확인. 03:54 KST 실제 렌더 확인. 플레이 미실행. 건축 측면 아치/천장 부재/비둘기 형태는 별도 보정 후보이며 원화의 따뜻한 광선·식생 붓터치도 완전 일치는 아님. 자세한 레시피·한계는 v020/STATUS.md.
## 최신 · 나머지 원화 보정 통합 (v019, 2026-09-29)
유지 TripoFull 맵, `TripoReplacement/v019/review.html`, 실제 렌더 `unreal_reference_finish.png`. v018 카메라 유지. 화면 우측(월드−X) 채광으로 수정하고 좌측 직사광 완화, 관목82개 낮춤/3개 제거·풀11/늘어진 잎15 추가, 청록 수면과 끊긴 크림색 하이라이트, 기둥18곳의 큰 박리2변형·기단/주두20곳 돌출 축소, 비둘기28 경로 재분산, 나무 없는 원경의 녹색 색면·우측 안개 보정. 닫힌 천장50개·정면 나무 제거 유지. 제작 `Scripts/build_hall_spalled_pillars.py`(Blender 런처), 적용 `Content/Python/complete_hall_reference_finish.py`, 조명/물만 `balance_hall_reference_finish.py`, 검증 `verify_hall_reference_finish.py`, 촬영 `capture_hall_reference_finish.py`. 전체 범위·재현·한계는 v019/STATUS.md. 플레이/게임 성능은 별도. 이전 단계 단독 적용은 최신 상태를 덮어쓸 수 있음.

## 최신 · 기준 카메라 구도 보정 (v018, 2026-09-29)
유지 TripoFull 맵. 최신 비교 `TripoReplacement/v018/review.html`, 실제 렌더 `unreal_composition.png`. `OH_ReferenceCamera` (0,200,155)→(0,100,112)cm, 수평 화각78.5788°→72.7°, 피치/요 유지. 벤치 크기를 유지하며 화면 위치와 후면 창 비율 보정. 다른720개 액터의 변환/정적 메시 경로 동일함을 저장 재로드 후 해시 검사. 플레이어 카메라/공간 치수/조명/재질 미변경. 적용 `Content/Python/apply_hall_composition.py`, 검사/촬영 `capture_hall_composition.py`. 미저장 두 후보와 변경 전 카메라는 v018에 보존. 다음 시각 우선순위는 우측 사선 채광/중앙 수면 밝기. 플레이 테스트는 사용자 담당.

## 최신 · 벽 식생·벤치 석판 접합 마감 (v017, 2026-09-29)
유지 TripoFull 맵. 최신 `TripoReplacement/v017/review.html`, 실제 렌더 `unreal_contacts.png`. 떠 보이던 벽 잎13군집을 기둥의 안쪽 범위에 연결하고 벤치 석판1개를 큰 가장자리 결손이 있는588삼각형 파생본으로 교체. 중앙 받침/위치/재질/닫힌 천장/정면 나무 제거/원경/조명/비둘기 유지. 제작 `Scripts/build_bench_shore_finish.py`는 Blender 런처로 실행, 적용 `Content/Python/finish_hall_contacts.py`, 검사 `verify_hall_contacts.py`, 촬영 `capture_hall_contacts.py`. 범위와 남은 사용자 플레이 확인은 v017/STATUS.md. 이전 전체 적용은 최신 접합을 덮어쓸 수 있음.

## 최신 · 원화 비교 통합 보정 (v016, 2026-09-29)
유지 TripoFull 맵. 최신 검토 `TripoReplacement/v016/review.html`, 실제 렌더 `unreal_finish.png`. 정면 나무 없이 흐릿한 색 원경, 따뜻한 초점 조명, 관목85개 비균일 배치, 벽 잎13군집·물가 석판6개, 구역별 수면 투과/반사, 천장과 기둥의 큰 색면, 비둘기28 분산/밝기 보정. v015 닫힌 천장/정면 나무 제거 유지. 적용 `Content/Python/refine_hall_painterly_finish.py`, 검사/촬영 `capture_hall_painterly_finish.py`, 읽기 검사 `verify_hall_painterly_finish.py`. 고정 노출 전용 원경 미술 표현과 제약은 v016/STATUS.md. 플레이 테스트는 사용자 담당. 이전 단계 단독 적용은 최신 상태를 덮어쓸 수 있음.

## 최신 · 천장 폐쇄·정면 후면 나무 제거 (v015, 2026-09-29)
사용자 요청으로 불연속 지붕18배치를 유지 Tripo 파생 지붕48개와 틈 막음 구조 면2개로 교체. 정면 후면 나무9·수관36을 레벨에서 제거하고 양옆 나무/낮은 식생은 보존. 유지 맵은 동일한 TripoFull. 최신 `TripoReplacement/v015/review.html`, 실제 렌더 `unreal_roof.png`. 적용 `Content/Python/close_hall_roof.py`, 검사/촬영 `capture_hall_roof.py`. 조명/노출/카메라 및 남은 v014 식생·수면·비둘기는 유지. 소스 애셋은 삭제하지 않음. 이전 단계는 제거한 배치가 있다고 가정하므로 단독 재실행 금지. 재현/범위는 v015/STATUS.md. 플레이 테스트는 사용자 담당.

## 최신 · 식생 바람·거리 LOD·렌더 비용 조정 (v014, 2026-09-29)
유지 TripoFull 레벨. 최신 검토 `TripoReplacement/v014/review.html`, 실제 렌더 `unreal_runtime.png`. 식생163개에 원래 LOD0/줄기/배치/충돌을 유지하는 Runtime 파생본과 3단계 LOD, 잎 전용 미세 바람 적용. 작은/먼 식생36개 및 초점 보조광의 중복 그림자를 줄이고 평면 반사 해상도75→60%로 조정하되 매 프레임 반사는 유지. 적용 `Content/Python/refine_hall_foliage_runtime.py`, 저장본 검사 `capture_hall_runtime.py`. 수치·한계·재현은 v014/STATUS.md와 performance_comparison.json. **플레이 테스트는 사용자 담당**. 이전 v010/v013 전체 적용을 단독 재실행하면 최신 메시/그림자가 되돌아갈 수 있음.

## 최신 · 후면·조명·접합 식생·물가 보정 (v013, 2026-09-29)
유지 TripoFull 레벨. 최신 비교 `TripoReplacement/v013/review.html`, 실제 렌더 `unreal_final_art.png`. 후면 벽/창/보10곳 파손, 국소 이끼4영역과 부착 덩굴9·잎군집5, 물가 석판9·잔해6, 청록 그림자와 따뜻한 수면 초점 조명 보정. 기존 식생/측면아치/투명수면/침수바닥/비둘기 유지. 소스 `Scripts/build_hall_final_details.py` → `Content/Python/finish_hall_art.py`, 새 프로세스 검사/촬영 `capture_hall_final_art.py`. **플레이 테스트는 사용자 담당**으로 지정됨. 자세한 재현·검증·범위는 v013/STATUS.md. 이전 단계 단독 재적용은 최신 보정을 덮어쓸 수 있음.

## 최신 · 바닥이 비치는 얕은 수면 (v012, 2026-09-29)
유지 TripoFull 레벨. 최신 비교 `TripoReplacement/v012/review.html`, 실제 렌더 `unreal_shallows.png`. v011 수면 메시/잔물결을 유지하고 반투명 Surface Forward 재질·DepthFade로 바닥 투과 구현. 기존 침수바닥47개에 5cm 미만의 비균일 추가 깊이, 벤치 석판1개 가장자리 파손. 식생·아치파손·빛·비둘기28 유지. 소스 `Scripts/build_shore_slab.py` → `Content/Python/apply_shallow_water.py`, 새 프로세스 검사/촬영 `capture_shallow_water.py`. `v012/baseline.json`은 누적 방지용 v011 바닥 위치. 실제 굴절/수중 모델/캐릭터 파문·직접 플레이/성능 검증은 별도. 세부 재현·한계는 v012/STATUS.md.

## 최신 · 수면 잔물결과 아치 파손 (v011, 2026-09-28)
유지 TripoFull 레벨. 최신 비교 `TripoReplacement/v011/review.html`, 실제 렌더 `unreal_water_ruins.png`와 시간차 `water_later.png`. v010 식생·빛·비둘기를 보존하고 수면 UV/분할·최대±0.12cm 변위·월드 노멀 잔물결을 추가, 아치3곳에 큰 결손 적용. 물은 여전히 불투명 반사 기반이며 실제 바닥 투과/굴절은 미구현. 유지 소스 `Scripts/build_water_ruins.py` → `Content/Python/apply_water_ruins.py`, 새 프로세스 검사/촬영 `capture_water_ruins.py`. 세부 수치·재현·한계는 v011/STATUS.md. 플레이/성능은 별도. 아래 v010 이전 적용 스크립트의 단독 재실행은 최신 결과를 덮어쓸 수 있음.

## 최신 · Tripo 수목의 회화풍 잎 재작업 (v010, 2026-09-28)
유지 TripoFull 레벨. 최신 비교 `TripoReplacement/v010/review.html`, 실제 렌더 `unreal_foliage.png`. Tripo 줄기/가지와 원래 UV를 보존하고 날카로운 잎 껍질을 회화풍 마스크 잎 카드로 교체. 나무19·관목85·원경수관54에 적용, 배치/빛/물/비둘기는 유지. 유지 제작 `Scripts/build_painted_hall_foliage.py` → `Content/Python/apply_painted_hall_foliage.py`, 검사/촬영 `capture_painted_hall_foliage.py`. 새 텍스처와 프롬프트·수치·한계는 v010/STATUS.md 및 TEXTURE_SOURCE.md. 같은 폴더 SM_OH_Rounded*는 비채택 볼륨 실험으로 반입하지 않았음; 최신 메시 접두사는 SM_OH_Painted*. 플레이/성능·바람/LOD는 별도.

## 최신 · 숲·수면·원화 연출 통합 보정 (v009, 2026-09-28)
현재 맵은 동일한 TripoFull. 최신 비교 `TripoReplacement/v009/review.html`, 통합 실제 렌더 `unreal_reference.png`. Tripo 파생 수관54개와 후면 덩굴6개 추가, 기존관목69개 군집 보정. 우측 후면 역광·색감, 불규칙 수면 및 바닥47개 높이−1cm, 선택적 파손8곳, 상부 아치창 높이, 비둘기28마리 분산 연출 적용. 기존532배치+추가식생53은 유지. 제작 `Scripts/build_hall_refinement.py`(Blender 런처) → `Content/Python/finish_hall_reference.py`, 최신 검사/촬영 `capture_hall_reference.py`. v009/baseline.json은 누적 방지용 원배치 입력. 물은 불투명 반사+미술적 색 보조이며 물결 변형·투과는 없음. 직접 플레이/성능은 별도. 자세한 재현·한계는 v009/STATUS.md. 예전12마리 전용 검사는 현재28마리 연출과 맞지 않으므로 최신 검사를 사용.

## 최신 · 불균일 이끼·Tripo 잎 보정·역광 (v008, 2026-09-28)
유지 TripoFull 레벨, 최신 비교 `TripoReplacement/v008/review.html`. 건축317배치의 이끼를 비대칭9개 습윤 구역 중심으로 바꾸고, 기존 덩굴24+추가식생53의 크기/위치를 불균일하게 보정. Tripo 관목·덩굴·나무3종의 잎 끝을 제한적으로 둥글게 수정하며 UV/토폴로지 유지. 따뜻한 후면 빛과 청록 실내 명암 보정, 노출1024 유지. 제작 `Scripts/soften_hall_foliage.py` → `Content/Python/refine_hall_atmosphere.py`, 검사/촬영 `capture_hall_atmosphere.py`. v008/baseline.json은 재실행 누적 방지용 유지 입력. 세부와 한계는 v008/STATUS.md. 직접 플레이/성능 검증 별도.

## 최신 · 회화풍 표면 텍스처 (v007, 2026-09-28)
유지 맵은 `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`. 최신 검토 `TripoReplacement/v007/review.html`. 새 광물질 색상 텍스처를 건축10종에 월드 좌표로 투영하고 이끼 범위·식생 명암을 보정. 기존532배치+추가식생53배치의 재질585개를 교체했으며 형태·조명·물반사·비둘기는 유지. v006 뒤 `Content/Python/paint_hall_surfaces.py`로 재적용, `capture_hall_pigment.py`로 저장 검사와 실제 렌더. 생성 프롬프트는 v007/TEXTURE_SOURCE.md, 재생성/한계는 STATUS.md. 아래 v006 이전 재질 스크립트는 최신 표현을 덮어쓰므로 단독 재실행하지 않는다. 직접 플레이·성능 측정은 별도.

## 최신 · 건축 이끼·덩굴과 수면 (v006)
유지 맵은 동일한 TripoFull. 최신 검토 `TripoReplacement/v006/review.html`. 기존532개 메시 유지,307개 배치에 이끼 재질,Tripo 덩굴/잎53개 추가. 최종 수면은 동적 평면 반사를 사용하는 불투명 스타일 표현으로 실제 바닥 투과와 잔물결 애니메이션은 생략. `Config/DefaultEngine.ini`의 실제 평면 반사 설정 `r.AllowGlobalClipPlane=1` 사용. 재적용은 v005 다음 `apply_hall_growth_water.py` → `refine_hall_water_reflection.py` → `finalize_hall_reflective_water.py`. 새 프로세스 검증/촬영은 `capture_hall_growth_water.py`; 보고서·제약·재현은 v006/STATUS.md. 물/추가 식생 NoCollision,직접 플레이와 성능 측정은 미실시.

## 최신 · 형태와 건축 모서리 보정 (v005)
유지 맵은 `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`. 검토는 `TripoReplacement/v005/review.html`. 건축·가구16종을 Tripo 원본 기준으로 리토폴로지하고 색을 재투영했으며, 식생·돌무더기5종은 작은 돌기를 보정했다. 532개 배치의 메시·재질,21종 치수,바닥/나무 충돌과 비둘기 시퀀서 검사 기록은 v005/verification.json. 소스는 `Scripts/clean_tripo_shapes.py`, 반입은 `Content/Python/apply_clean_hall_shapes.py`. 재생성 세부 사항은 v005/STATUS.md. v005 뒤에 v004 재질 스크립트만 실행하면 UV가 맞지 않으므로 현재 CleanMaterials를 사용한다. 아래는 이전 단계 이력이다.

## 최신 · 따뜻하고 부드러운 재질 보정 (v004)
현재 맵은 TripoFull. 최신 검토는 `TripoReplacement/v004/review.html`. 21종 재질을 새로 만들어 532개 배치에 적용하고 미세 텍스처 대비·노멀·반사를 줄였다. 석재/식생 팔레트와 광원 부드러움 보정. 원본 텍스처와 메시 재질 슬롯은 보존. 재생성 순서는 v002 전체 반입 → v003 건축 보정 → `Content/Python/style_tripo_hall.py`. 설정·검증·한계는 v004/STATUS.md와 JSON 보고서에 기록. 실제 플레이/성능 검증은 미실시.

## 원화 비교 보정① · 최신 화면
현재 레벨은 동일한 TripoFull이다. 최신 검토는 `TripoReplacement/v003/review.html`이며 창틀8개·측면아치8개·주두 축소·지붕잔해14개를 보정했다. 소스와 재적용 순서는 v003/STATUS.md. v002 전체 반입 뒤에는 refine_tripo_hall_structure.py를 다시 실행해야 한다. 카메라·식생·조명·수면·새 연출은 다음 단계다.
## 최신 유지 작업본 · 전체 Tripo 전환 (2026-09-25)
- 현재 Unreal 레벨: `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.
- 검토: `TripoReplacement/v002/review.html`. 재생성/검증: 같은 폴더 `STATUS.md`.
- 신규19종 + 유지 Tripo 기둥·나무·비둘기. 새 모듈499배치, 기존Tripo 나무19그루, 비둘기12마리. 이전 시각용 메시0 확인(물 효과 제외).
- 원본114파일/해시,19개 보정Blend/FBX/2K PBR,모듈명세·배치JSON 보존.
- tools/play-overgrown-hall.ps1은 이 레벨을 실행한다. 기존 Layout 및 v001 TripoReview는 비교용이다.
- 저장맵 치수/재질/충돌/시퀀서 및 실제 Unreal 렌더 검증. 캐릭터 직접 플레이와 성능 측정은 아직 하지 않았음.
- 아래 내용은 이전 제작 이력이며 최신 유지 작업본은 위 경로다.
## 기준 파일
- 원화: References/source_scene.png
- 채택 콘셉트01–20: Concepts/modules_v001.png
- 난간25·지붕26 및 비둘기 리깅 명세: Design/GAP_REVIEW.md
- 검토 입구: Design/review.html
- 치수 검토 기준: Blockout/v002/overgrown_hall_blockout.blend
- 최신 외형 제작본: Production/v001/overgrown_hall_detail.blend
- 최신 교환 파일과 렌더: Production/v001/overgrown_hall_detail.glb, reference.png, overview.png

## 재생성 순서
모든 Blender CLI는 tools/run-blender.ps1을 사용한다.
1. Scripts/build_blockout.py: 유지 블록아웃 v002 생성.
2. Scripts/build_detail_pass.py: v002를 읽어 잎·줄기·가지 메시와 표면 재질을 보강한 Production/v001 생성.
3. Scripts/export_detail_unreal.py: Production FBX와 재질/치수 manifest 생성. 공통 내보내기 로직은 export_blockout_unreal.py. PowerShell 런처에서는 별도 --detail 인자를 전달하지 않는다.
4. Content/Python/import_overgrown_hall_detail.py: 별도 Production 레벨 반입. 공통 반입 로직은 import_overgrown_hall_blockout.py.
5. Content/Python/verify_overgrown_hall_detail.py: 저장 레벨 재검사. 공통 검증은 verify_overgrown_hall_blockout.py.

## Unreal 경로
- 치수 블록아웃: /Game/Environment/OvergrownHall/Blockout/Maps/L_OvergrownHall_Blockout
- 외형 보강본: /Game/Environment/OvergrownHall/Production/Maps/L_OvergrownHall_Detail
- 두 레벨은 독립적이다. 기존 블록아웃 플레이 도우미는 계속 블록아웃을 연다.
- 구조는 정적 complex collision. 물과 식생은 NoCollision 프로필. 시작 Pawn은 BP_Player_Heroine.

## 상태와 한계
식생 다면체 대신 개별 잎·줄기·가지 메시로 표현한다. 현재 잎은 절차적으로 만든 형태이며 최종 식생 채택이나 최적화 완료 상태가 아니다. 바람·LOD·인스턴싱 최적화가 남았다.
벽/바닥은 낮은 대비의 절차적 색·거칠기 변화다. 원화의 큰 박리 면·습기 흐름·이끼 분포는 별도 마스크 정교화가 필요하다. 물은 불투명 반사 근사다. Blender의 미세 범프와 Unreal의 단순 표면 표현은 동일 셰이더가 아니다.
화면 이미지는 Blender 렌더다. 실제 UE 외관과 캐릭터 이동은 별도 검증해야 한다. NullRHI 검사만으로 렌더 통과라고 하지 않는다.
비둘기 첫 리그와 날갯짓·활공·전환 클립을 Bird/v001에 제작했다. 비행 경로와 상태 제어는 아직 없다.

## 고정 스케일
홀16×20×12m 가정. 벤치 폭1.8m. 카메라(0,2,1.55), 시선(0,17,3.15), 렌즈22mm. 후면 창 영역 폭84%로 보정. 실제 플레이 치수 승인 전이므로 원화만으로 확정하지 않는다.

## 검증 기록
각 폴더 verification.json은 Blender 기하 검사, unreal_import.json은 UE 반입/바운드, unreal_saved_verification.json은 별도 프로세스 저장 레벨 검사다. 파일이 존재하고 status가 통과일 때만 해당 검증 완료로 간주한다.


검증 결과: Production의21개 메시 그룹 저장/재로드 검사 통과, 누락0, 충돌 설정 및 벤치180cm 유지. SM6 렌더 진단은 엔진 기본 셰이더 초기 컴파일이 길어 해당 진단 프로세스만 종료했으며, UE 시각 검증/셰이더 전체 통과를 주장하지 않는다.


## 비둘기 유지 소스
- Scripts/build_pigeon.py → Bird/v001/pigeon_rig.blend 및 스켈레탈/애니메이션 FBX.
- Scripts/render_pigeon_preview.py → 실제24프레임 렌더. Bird/v001/review.html에서 재생.
- Content/Python/import_overgrown_pigeon.py 및 verify_overgrown_pigeon.py → /Game/Environment/OvergrownHall/Bird/Meshes 및 Clips.
- Fly0.5초, Glide1초 고정 자세, 전환각0.25초. 지정 위상에서만 끝점 연결 검증; 임의 위상 전환은 상태 제어 추가 필요.
- 가까운 시점의 몸통 연결/깃 배열 다듬기, 경로 배치, 실제 UE 재생·화면 검토가 남았다.


비둘기 검증: 별도 UE 프로세스에서 저장 스켈레톤·4클립 길이·shoulder_L의 서로 다른 시점 회전값을 검사해 통과. 초기 오인식으로 생긴 미사용 Animations/A_OH_Pigeon_Fly 메시1개는 참조0 확인 후 삭제. 정상 클립은 Clips 폴더에 있다.


## 최신 비둘기 방향 변경
사용자가 Bird/v001의 외형을 거절했다. 기존 절차적 모델은 최종 제작 기준에서 제외하며 Tripo 웹 생성으로 교체 중이다. Bird/Tripo_v001/STATUS.md를 먼저 읽는다. 기존 리그/클립은 참고용만 보존한다.


Tripo 교체 후보 생성·다운로드·실측 완료: Bird/Tripo_v001/review.html. 실제19038삼각형과2K PBR, 스켈레톤 없음. 사용자 외형 채택 검토 대기. 이후 리깅은 이 원본을 새 소스로 시작한다.


## 채택 Tripo 비둘기 리그 (2026-09-24)
사용자가 Tripo_v001 외형을 채택했다. 유지 원본은 Bird/Tripo_v001/OH_Pigeon_Tripo_v001.glb, 현재 리그는 Bird/Tripo_Rig_v001/pigeon_rig.blend이다. 이전 Bird/v001은 미채택 참고본이다.
- Scripts/rig_tripo_pigeon.py → 원본 UV/19038삼각형/2K PBR 보존, 17본과4클립. 원본 자세 날개 폭68cm로 균일 축소.
- Scripts/render_tripo_pigeon_preview.py → 실제24프레임. Bird/Tripo_Rig_v001/review.html.
- Content/Python/import_overgrown_tripo_pigeon.py 및 verify_overgrown_tripo_pigeon.py → /Game/Environment/OvergrownHall/Bird/Tripo.
- GLTF roughness=G/metallic=B 채널 유지, Unreal normal green 반전.
- 루프·전환 끝점 검사 통과. 전환은 지정 위상용. 비행 경로/상태 제어 및 실제 Unreal 화면 검토는 아직 남음.

Tripo 리그 검증 완료: 별도 UE 프로세스에서 전용 스켈레톤·4클립 길이·날개 회전 변화·PBR 재질 슬롯 재로드 통과. 실제24프레임 모두 서로 다른 이미지로 검증. 화면 검토는 Blender 렌더이며 UE 시각/게임플레이 확인은 아직 없음. Unreal 구조체 배열 수정은 항목을 인덱스에 다시 대입한 뒤 저장해야 유지됨.

## 비둘기 비행 연출 (2026-09-24)
- Content/Python/build_overgrown_flock.py: Production 상세 레벨에 Tripo 비둘기12마리와 LS_OvergrownHall_Flock 시퀀스 추가. 20초 자동 반복, 48fps, 개체별 위상 차이, 날갯짓/전환/활공/전환 연결.
- 비행은 고정 경로 연출이며 플레이어 반응/동적 장애물 회피 AI는 아님. 플레이어 카메라는 시퀀서가 제어하지 않음.
- Content/Python/verify_overgrown_flock.py: 저장 후12개 바인딩·재질 모델·NoCollision·자동 반복과 실제 시퀀서 시간 평가에 따른 위치 변화 확인. 검사에서는 레벨을 다시 저장하지 않음.
- Scripts/preview_overgrown_flock.py: Blender 구조물과1452개 경로 표본의 표면 거리 및 배치 이미지. Bird/Flock_v001/reference.png는 Blender 렌더, Unreal 화면 아님.
- tools/play-overgrown-hall.ps1은 이제 최신 Production/Maps/L_OvergrownHall_Detail을 실행.
- 비행 위치/회전은 Sequencer 편집 가능. 다시 제작하면 OH_Flock_ 접두사 액터와 해당 시퀀스만 교체됨.

## 최신 원화 배치 (2026-09-25)
현재 작업 레벨: /Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout
현재 검토: Scene/v001/review.html. Production 상세 레벨은 이전 배치로 보존.
1. Scripts/build_hall_layout.py: Production 소스를 읽어 창/기둥/벤치/식생/물가 배치. Scene/v001/overgrown_hall_layout.blend.
2. Scripts/export_hall_layout.py: 공통 exporter의 SOURCE_DIR/SOURCE_BLEND 인자로 내보내기.
3. Content/Python/import_overgrown_hall_layout.py: 새 Scene 경로 반입, 원화 카메라와 전용12마리 비행 시퀀스 저장.
4. Content/Python/verify_overgrown_hall_layout.py: 새 프로세스21그룹 재질/충돌/180cm 벤치 및12마리 비행 평가 통과.
5. Scripts/preview_hall_layout.py: 통합 Blender 배치 렌더와 경로1452표본 검사. 구조물 표면 최소거리2.26m, 새 간격 유지.
실제 게임플레이와 Unreal 화면 검증은 아직 없음. 다음은 우측 역광/청록 명암, 파손 실루엣, 식생과 수면 재질 개선. 배치 이미지를 최종 외형으로 간주하지 않음.

## Unreal 과노출 수정 (2026-09-25)
사용자 보고: Unreal 레벨/플레이 화면이 과도하게 밝음. audit_hall_exposure.py에서 프로젝트 ExtendDefaultLuminanceRange=0, 태양25000, 고정 노출min=max10, 기본bias+1 확인. EV 단위로 가정한 값이 선형 밝기로 해석되는 반입 오류였다.
Content/Python/hall_exposure_settings.py는 프로젝트 단위를 판별하여 white point1024를 저장하고 bias0을 명시한다. 프로젝트 전역 설정은 바꾸지 않음. 공통 반입 스크립트도 이 함수를 사용하므로 재생성 시 되돌아가지 않음.
fix_hall_exposure.py로 현재 Scene 레벨에 적용. 최초 저장은 사용자가 연 에디터의 파일 잠금으로 실패했고, 사용자가 에디터를 닫은 뒤 저장 성공. exposure_audit.json은 수정 전, exposure_fix.json은 저장값 기록. 실제 렌더 결과는 exposure_render_verification.json과 unreal_exposure_fixed.png에서 별도 확인.

노출 수정 후 새 Unreal 렌더 프로세스에서 저장값1024/bias0 확인 및 실제1200×640 스크린샷 촬영 성공. unreal_exposure_fixed.png에서 기둥·창살·식생 가시성 확인. 캐릭터 플레이는 미실시. 검토 페이지에 Blender 화면과 구분하여 추가.

## 원화 비교 보정 (2026-09-25, 후속)
- Scene 전용 export_hall_layout.py는 MATCH_CAMERA_HANDEDNESS=True. Blender X가 화면 오른쪽인 반면 UE +Y 카메라의 오른쪽은 -X이므로, 메시 X를 반전하고 면 순서도 변환의 handedness에 맞춤. manifest 바운드 역시 변환된 좌표로 검사. 기존 Blockout/Production exporter 기본값은 유지.
- 구조: 측면 아치2곳의 중간 세그먼트 제거, 보의 완벽한 직선 반복 완화. 외부 지면과 수목12묶음으로 검은 수평선/빈 창밖 보완.
- Content/Python/polish_hall_reference.py: Scene 반입 후 유지되는 전용 조명·재질 설정. 태양18000/yaw-37/따뜻한 색, sky0.65, 옅은 volumetric fog. 벽·바닥의 둥근 고대비 얼룩을 낮은 대비의 넓은 변화로 교체. 수면metallic0.05/roughness0.23으로 과한 거울 반짝임 완화.
- verify_overgrown_hall_layout.py에 벤치 camera-right 음수, 안개와 노출1024/bias0 회귀 검사 추가. 180cm 벤치/21그룹/12마리 시퀀서 평가 통과.
- capture_hall_reference.py → unreal_reference_pass.png 실제 Unreal 렌더. 이전 unreal_exposure_fixed.png는 비교용으로 보존.
- 아직 남음: 실제 벽 박리/균열/젖은 자국 텍스처, 더 큰 지붕 파손, 식생 형태/색 변주, 최종 물 셰이더, 새 무리 크기/밀도, 실제 플레이 검증. 이 보정은 완성 선언이 아님.

실제 보정 렌더 확인 후 실내 암부가 너무 짙어 sky를1.1로 변경하고 후면창에950×500cm RectLight 보조광 추가. 이전 실제 렌더와 신규 렌더는 Scene/v001/review.html에서 전환 비교. Blender는 배치 소스이며 최종 외관 판단은 Unreal 렌더 기준.

## 제작 방식 변경 (2026-09-25)
사용자가 Blender 절차적 나무·기둥 품질을 부적합으로 판단. TripoReplacement/v001/STATUS.md 기준으로 Tripo 생성→Blender 보정→Unreal 실제 교체를 진행한다. 기존 배치와 캐릭터 스케일은 유지하며 기존 저품질 외형을 새 채택 모델로 간주하지 않는다.

### Tripo 교체 검토본
사용자 제공 FBX를 Blender 보정 후 검토맵 `/Game/Environment/OvergrownHall/TripoReplacement/Maps/L_OvergrownHall_TripoReview`에 적용. 기둥30구간/나무19그루. 상세: TripoReplacement/v001/STATUS.md 및 review.html. 나무 잎 외형/기둥 접합/남은 구조는 최종 승인 대기. 유지 Layout은 아직 기존 맵이며 검토본으로 자동 전환하지 않음.

### 전체 Tripo 전환 (사용자 요청 2026-09-25)
남은 모델19종 모두 Tripo 생성 완료. 작업 IDs/상태: TripoReplacement/v002/jobs.csv, STATUS.md, review.html. 기존02/19/20 Tripo는 유지. 현재 다운로드 단계가 막혀 신규19종 Blender 보정/Unreal 적용은 미완료. 사용자 요청으로 자동 다운로드를 우선 조사했으며 FBX 및 공식 Bridge ZIP 링크 모두 로컬파일 미확보. v001 검토맵과 유지 Layout을 완료본으로 바꾸지 않음.
