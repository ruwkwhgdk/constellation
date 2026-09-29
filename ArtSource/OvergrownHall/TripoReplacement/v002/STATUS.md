# 전체 Tripo 교체 · 적용본

## 현재 Unreal 레벨
`/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`

사용자가 제공한 `C:/Users/User/Downloads/OvergrownHall_3D_Model_Resources`의19종을 보정·임포트했다. 기존 Tripo 기둥 몸통, 나무, 비둘기는 재사용. 원본 ZIP의 FBX/텍스처114파일은 각 Original 폴더와 source_hashes.json으로 보존.

## 적용
- 새19종 PBR 메쉬, BaseColor/Normal/RM 57텍스처. 새 모듈499배치 및 기존 Tripo 수목19그루. 비둘기12마리는 새 레벨 전용 시퀀스로 재바인딩.
- 이전 OH_SM_OH_Blockout 시각용 메시를 모두 제거. 21물만 셰이더 효과로 유지.
- 측면 아치 문살 제거, 상부 창 반원 분리, 창살 끝장식 제거, 벤치180cm와 방향 교정. 바닥은 평탄한 별도 Box 충돌.
- 바닥 UCX가 초기 반입 후 비어 있는 것을 저장맵 검사로 발견해 에디터 StaticMeshEditorSubsystem으로1개Box를 추가 저장. 재반입 후 capture_tripo_full_hall.py가 누락 여부를 확인한다.

## 재생성
1. Python Scripts/prepare_tripo_textures.py 완료를 기다린다.
2. tools/run-blender.ps1로 Scripts/prepare_tripo_full_kit.py 실행. 각 prepared.blend/FBX/inspection.json 및 kit_manifest.json.
3. 같은 런처로 Scripts/plan_tripo_full_scene.py 실행. 유지 Scene/v001 Blend 배치에서 placements.json 생성.
4. Content/Python/import_tripo_full_hall.py 반입. 기존 목적지의 OH_FULL 액터를 재생성하므로 수동 배치 수정 후 무심코 재실행하지 않는다.
5. GUI Unreal에서 capture_tripo_full_hall.py: 바닥 충돌 보완, verify_tripo_full_hall.py 검사, 실제 렌더 촬영. NullRHI 결과와 구분.
6. Scripts/write_tripo_full_review.py로 review.html 갱신.

## 검증 및 남은 품질 작업
검증 보고서 verification.json에서19메시 치수/재질,499개 배치,벤치180cm,이전 시각용 메시0,식생 NoCollision,바닥 단순 충돌,비둘기 시퀀스 검사를 확인했다.
실제 플레이 및 성능 측정은 아직 미실시. Tripo 원본의 큰 풍화 요철과 잎 두께가 남아 있다. UV/탄젠트 미세 경고, LOD/인스턴싱 최적화 및 원화 스타일 일치 검토는 후속 작업이다. 모든3D 모델의 출처 전환과 최종 아트 품질 승인은 구분한다.

## 최종 확인
벤치180도 방향 보정 후 새 프로세스에서 검증 재통과. 실제 Unreal 렌더 `unreal_full.png` 갱신(2026-09-25 18:47). tools/play-overgrown-hall.ps1은 전체 Tripo 레벨을 연다. 최종 화면에서 모델 전환과 개구부/벤치 방향을 확인했으며 원화의 빛·물·식생 분위기까지 최종 승인된 것은 아니다.
