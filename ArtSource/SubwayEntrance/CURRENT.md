# 지하철역 입구 · 현재 유지본

입구 기준 액터는 `SE_EntranceRoot`, 좌표 `(3900,-19500,10530)`입니다. 정면은 +Y, 진입은 -Y입니다. 지정 `subway_station`만 제거했고 `subway_station2` 및 공유 원본 애셋은 유지했습니다.

## 2026-09-30 · 어두운 통로와 스트리밍 연결 (최신)

확인 맵은 동일하게 `/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland`입니다. 기존 내부는 `/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2`에 유지합니다. 최신 검토는 `Connection/v002/review.html`입니다. 이전 페이드/OpenLevel 구현은 현재 동작이 아닙니다.

- 입구 하부 참 뒤에 추가 경사와 오른쪽으로 꺾인 폐쇄 통로를 추가했습니다. 기존 끝벽만 열린 파생 E09로 교체했고, 섬 전용 파생 메시의 지하 홈을 확장했습니다. 지상 지면과 통로 바닥을 유지합니다.
- 내부 상부 참 뒤에도 대응 통로를 추가했습니다. 기존 내부 구조물은 보존했습니다.
- 외부 전환 기준면 `(4700,-20500,9640)`, 진입 +X. 내부 전환 기준면 `(-1500,-800,360)`, 복귀 진입 -Y. 기준면 위치는 바닥 높이이며 캡슐 높이/측면 오프셋은 상대 변환으로 보존합니다.
- 40m 이내 접근하면 목적지를 비동기 로드합니다. 활성화와 준비 여유 시간 후 목적지 보행 바닥·캡슐 여유를 검사합니다. 캐릭터/컨트롤러를 교체하지 않고 위치·시선·속도를 회전 변환합니다. 입력 잠금, 화면 페이드, OpenLevel 호출은 없습니다.
- 검은 통로 끝의 안전 장벽은 준비 지연/충돌 검증 실패 때 전진을 막습니다. 뒤로 돌아갈 수 있습니다. 60초 로딩 실패 시 언로드 후 10초 여유를 두고 최대1회 재시도합니다. 재시도까지 실패하면 해당 세션에서는 통로가 닫힌 채 유지됩니다.
- 양쪽 전역 SunSky/비한정 후처리는 현재 점유 레벨만 활성화합니다. 통로의 후처리는 범위가 제한되며 기존 측광 방식을 유지한 채 노출을 낮춥니다. 기존 발소리/캐릭터 오디오는 월드 교체로 끊지 않습니다. 별도 환경음 크로스페이드 에셋은 추가하지 않았습니다.
- 첫 번째로 연 맵이 persistent이고 상대 맵은 세션 중 상주하며 재사용됩니다. 두 공간이 동시에 메모리에 남는 비용이 있습니다. 별도 맵을 스트리밍하는 방식이며 물리적인 거리로 두 공간을 붙인 것은 아닙니다.

### 유지 소스와 검사

- `Scripts/build_dark_connection.py` → `Connection/v002/dark_connection.blend` 및 `FBX/`. 실행은 항상 `tools/run-blender.ps1`.
- `Content/Python/apply_subway_dark_connection.py`: 지정 액터만 교체, 두 맵 백업, 반입 치수/볼록 충돌 검사, 지면·통로 보행 쿼리12개, 관계없는 액터 변환/메시 보존 검사 후 저장.
- `Content/Python/capture_subway_dark_connection.py`: 새 저장본을 읽고 transient 카메라로 촬영. PIE/맵 저장 없음.
- `Source/Constellation/SubwayTravelSubsystem.*`, `SubwayTravelVolume.*`, `SubwayTunnelEnvironment.*`, `SubwayPortalTransform.h`, `SubwayStreamingGate.h`.
- 독립 검사 `tools/test-subway-streaming.cmd`: 준비 지연·도착 검사 실패 재시도·재진입·로딩 재시도 한도. 엔진 편집기 수학 검사 `Constellation.Subway.PortalPose`: 위치/시선/속도 및 왕복 보존.
- 결과 `Connection/v002/applied.json`, `fresh_validation.json`; 수학 검사 `Saved/SubwayTests/PortalReport/`.
- 최초 어두운 통로 변경 전 백업 `Saved/SubwayEntranceRecovery/20260930_213555_dark/`. 중간/최종 적용 백업도 유지합니다. 자동 복원하지 않습니다.

빌드와 편집기 정적 검사/수학 검사는 실제 이동을 검증한 것이 아닙니다. 사용자 확인 대상: 양방향 걷기·달리기, 뒤돌아보기, 카메라 회전, 프레임 끊김, StartIsland의 스트리밍 BeginPlay와 NPC/퀘스트 반응, 두 레벨 상주 메모리 비용. 멀티플레이를 대상으로 구현하지 않았습니다. Git 커밋/푸시는 이번 요청에서 실행하지 않았습니다.

### 통로 미술 마감 재현 순서

`apply_subway_dark_connection.py` 다음에 `finish_subway_dark_connection.py`를 실행합니다. 후자는 `polish_subway_tunnel_shading.py`로 통로 전용 명암 재질을 적용하고, 안내등과 범위 제한 후처리의 노출 Bias를 명시 저장한 뒤 촬영합니다. 선행 반입 스크립트만 다시 실행하면 이 재질 할당이 이전 기본 재질로 돌아갈 수 있습니다.

깊은 벽/바닥에는 빛 누출 방지용 검정 Unlit 재질을 사용합니다. 진입부는 월드 좌표 깊이에 따라 반사색이 완만하게 낮아집니다. 통로 후처리는 기존 측광 방식과 물리 카메라 설정을 유지하고, 노출 보정 Bias -16만 공간적으로 혼합합니다. 프로젝트의 ExtendDefaultLuminanceRange 설정이 없으므로 Histogram Min/Max에 EV 값을 넣지 않습니다. 화면 페이드 호출 없이 통로 위치에 따라 노출/표면을 처리합니다. 꺾이는 지점에는 왕복 길찾기를 돕는 낮은 바닥 안내등을 두었습니다.


## 최종 저장본 확인

2026-09-30 22:17 최종 촬영 완료. 외관·하강·바닥 안내등·양쪽 전환 암부·내부 출구 6장을 확인했습니다. 양쪽 암부는 정지 캐릭터 모델도 가려지고 내부 출구는 과노출 없이 나타납니다. 빌드, 상태 검사, 왕복 변환 검사, 바닥 쿼리12개가 통과했습니다. 실제 플레이는 실행하지 않았습니다.

## 유지 소스와 재실행

- 채택 원화 `Concepts/v002/entrance_only.png`, 모듈 `Design/module_sheet.png`.
- Blender 제작 소스 `Scripts/build_production.py`, 제작본 `Production/v001/entrance_kit.blend`, `FBX/`, `textures/`.
- 정밀 간판 `Scripts/create-signs.ps1`; 내용 사당/1번은 교체 가능한 임시 역명이다.
- FBX cm 보정 재출력 `Scripts/reexport_centimeters.py`. Blender는 항상 프로젝트 `tools/run-blender.ps1`로 실행한다.
- 반입 `Content/Python/import_subway_entrance.py`.
- 최초 배치 `Content/Python/apply_subway_entrance.py`, 편집기 틱 실행 래퍼 `run_subway_placement_editor.py`. 이미 적용된 맵에서는 중단한다. 수정하려면 별도 범위 한정 패치를 만든다.
- 읽기 전용 촬영 `Content/Python/capture_subway_entrance.py`.
- 최신 이동 소스와 검사는 위 스트리밍 연결 절을 따릅니다. 이전 페이드 방식 검사는 현재 런타임 검사가 아닙니다.
- 적용 전 맵 백업은 `Saved/SubwayEntranceRecovery/20260930_040909/`. 최신 사용자 작업을 덮어쓰는 자동 복원은 하지 않는다.

이전 블록아웃은 검토 근거로 유지한다. 도시·차량·나무 등 사진 배경은 제작 범위에 포함하지 않았다. Git develop에서 작업했고 이번 단계의 커밋/푸시는 아직 하지 않았다.



## 최신 · 난간/안내선 주변 조명/후면 차단 (2026-09-30)

최신 검토는 `Connection/v003/review.html`입니다. 유지 맵과 전환 기준면은 그대로입니다.

- 입구 `SE_E10` 조립 난간 배치를 제거하고 내부 ReviewKit의 `10_RailSlope`, `10_RailSlope60`, `19_RailReturnSlopeRight` 총14개를 재사용했습니다. 재질은 내부의 `M_Kit_RailSteel_Weathered`입니다. 수평 길이540cm와 입구 경사16/30에 맞추기 위해 Z배율16/15를 적용하여 세로 간격은 약26.7cm입니다. 공유 난간 메시 원본은 수정하지 않았습니다.
- `SE_RearClosure`: 중심(3900,-19920,10185), 크기460×20×390cm. 지상 반대편을 막고 지하 통로는 유지합니다. BlockAll 충돌을 사용합니다.
- 안내선 주변에 빛을 받는 짙은 무광 통로 재질과 양쪽2개씩 보조광을 적용했습니다. 검은 후처리 영역은 전환면 가까이로 좁혔습니다. 안내선의 발광은 외부/내부 노출에 맞춰 별도 유지합니다.
- 적용 소스 `Content/Python/refine_subway_access.py`, 촬영/검사 `capture_subway_access.py`. 기존 통로 반입과 finish 스크립트를 재실행한 경우 이 보완 스크립트를 마지막에 적용해야 합니다.
- 이전 v002의 전체 깊은 표면 검정 Unlit 설명은 이번 보완으로 대체됩니다. 전환부의 국소 노출 Bias -16은 유지하며 안내선 주변만 읽기 쉬워졌습니다.
- 저장/검사 기록은 `Connection/v003/applied.json`, `fresh_validation.json`입니다. 실제 이동 및 카메라 체감은 사용자 플레이 확인 대상입니다.
