# v010 · 주요 수목 형태 재작업

유지 레벨: `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`.
검토: `review.html`. 실제 Unreal 렌더 `unreal_foliage.png`; `Tree_painted.png`, `Shrub_painted.png`는 Blender 단품 렌더.

## 유지 제작 방식

- 채택된 Tripo v008 나무19/관목17의 녹색 잎 영역을 원본 텍스처에서 판별. 줄기·가지 기하는 보존하고 원래 UV와 재질을 별도 슬롯1에 유지.
- 뾰족한 잎 껍질을 제거하고 같은 잎 분포 위치에 살짝 휘어진 교차 잎 카드를 구성. 각각3방향, 카드당8삼각형. 생성한 회화풍 RGBA 잎 무리 텍스처는 슬롯0에 사용. 이는 Tripo 구조와 새 잎 텍스처/카드를 결합한 보정이며 새 Tripo 생성 모델이 아님.
- 나무532개 잎 무리, 총17103삼각형(이전29879); 관목215개 잎 무리, 총6157삼각형(이전14970). 원경용 수관도 같은 나무의 상부 잎 분포에서 파생. 실측 `painted_shapes.json`.
- Unreal 마스크 임계값0.3, 양면 식생 셰이더와 약한 투과 색. 소스1254px를UE1024px로 빌드하며 알파 피복률을 유지하는 밉맵 사용. 실제 투명 픽셀 확인 `alpha_check.json`. 원경은 밉 편향1과 낮은 색 대비.
- 기존 위치/스케일 그대로 나무19·관목85·수관54 교체. 새 배치를 추가하거나 광원 밝기를 올린 방식이 아님. 줄기 단순 충돌 복사, 관목과 수관 NoCollision. v009의 물·조명·비둘기28마리 보존.

## 재생성

1. `tools/run-blender.ps1 -b -P ArtSource/OvergrownHall/Scripts/build_painted_hall_foliage.py`로 유지FBX/Blend 재생성. 정상 사용자 프로필 가드 준수.
2. v009 유지 맵 이후 `Content/Python/apply_painted_hall_foliage.py`로 텍스처·잎재질2종·메시3종 반입 및 실제 배치 교체.
3. `capture_painted_hall_foliage.py`로 저장 상태를 다시 읽어 메시/슬롯/마스크/충돌/1024빌드·밉맵/물·빛·비둘기 보존과 실제 렌더 확인.
4. 텍스처 원본과 정확한 built-in image_gen 프롬프트는 `TEXTURE_SOURCE.md`. 원본 알파 보존. 이후 이전 단계 제작을 재실행하면 v010도 마지막에 다시 적용.

## 비채택 실험

`rework_hall_canopies.py`, `SM_OH_Rounded*`, `Tree_after.png`, `Shrub_after.png`, `shapes.json`은 매끈한 덩어리처럼 보여 제외한 볼륨 시안. Unreal에 반입하지 않았으며 유지 소스로 사용하지 않는다. 최신은 **SM_OH_Painted***와 **build_painted_hall_foliage.py**, **painted_shapes.json**이다.

## 검증과 한계

저장된 나무19/관목85/수관54, 잎과 줄기2개 재질 슬롯, 줄기 충돌, 식생 NoCollision,1024텍스처 및 알파 밉맵 검사 통과. 실제 Unreal 화면에서 잎 마스크와 반사에 비친 수목을 확인. 상세 `verification.json`, `exposure_render_verification.json`.

새 프로세스 `Saved/HallPaintedFoliageVerify.log`에서 Python 오류·재질 컴파일 실패 없이 통과. 2026-09-28 23:00:29 실제1200×640 화면 재촬영,23:00:47 촬영 성공 보고서 기록 및 자체 에디터 정상 종료 확인.

삼각형 감소가 곧 성능 향상을 의미하지 않음: 교차 잎 카드의 마스크 오버드로 비용이 있으므로 대상 기기에서 별도 측정 필요. 바람·거리별LOD·직접 플레이 검증은 미실시. 가까이 접근하면 카드 구조가 드러날 수 있으며 원화의 모든 붓질/수관 실루엣과 동일한 최종 승인을 의미하지 않음. 물 투과/실제 잔물결, 큰 건축 파손 등은 이번 수목 집중 패스에서 변경하지 않음.
