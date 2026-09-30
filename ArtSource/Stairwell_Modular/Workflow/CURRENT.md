# 유지 산출물 · 2026-09-24

## Unreal

- **플레이 기준**: `/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2`. 사용자가 공간 크기 해결을 확인했다. 계단 폭480cm, 참 깊이360cm, 단 높이30cm, 디딤판60cm. 캐릭터 MaxStepHeight45cm. 문에 맞춘 추가 벽은 제거했다.
- **재생성 기준 장면**: `/Game/Constellation/Review/Stairwell/Maps/L_Stairwell_Reference`. 플레이용이 아니라 확장본의 소스다. 계단 폭240cm. 삭제하거나 최종 맵과 혼동하지 않는다.
- **채택 키트 카탈로그**: `/Game/Constellation/Review/Stairwell/Maps/L_Stairwell_KitReview`. ID01–22, 파생형 포함31개 메시. 사용하지 않은 파생형도 승인된 재사용 키트이므로 보존한다.
- 문 메시2개와 `BP_Stairwell_DoorAssembly`는 재사용용이다. 문 열기 입력/런타임 상호작용은 미구현이다.
- 주인공 `BP_Player_Heroine` 카메라 lag 설정은 저장 후 새 인스턴스에서 검증했다. 실제 계단 플레이 개선 체감은 사용자 재검증 대기다.

## 제작 소스

- 원화 `References/source_scene.png`, 채택 기록 `Review/`, 콘셉트 `Concepts/`.
- 원본 Tripo GLB와 보정 Blend: `Models/14_Door`, `Models/15_Light`. v001 light Blend는 v002 최적화 입력으로 보존한다.
- 문 반입 소스: `Export/DoorPair/door_pair_source.blend`와FBX/텍스처.
- 채택 키트: `Production/v001/stairwell_kit_review_v001.blend`, `FBX/`, `textures/`, `reports/`, `review.html`.
- CLI Blender: `Scripts/build_production_kit.py`와 `validate_production_kit.py`, 항상 프로젝트의 `tools/run-blender.ps1`로 실행.

## Unreal 재생성 순서

1. 필요한 경우 `Content/Python/import_stairwell_door.py`, `import_stairwell_review_kit.py`로 소스를 반입한다. 불필요한 재반입은 피한다.
2. `build_stairwell_scene.py`가 기준 장면을 만든다. `stairwell_lighting_settings.py`, `stairwell_material_settings.py`, `stairwell_reference_details.py`, `stairwell_finish_settings.py`가 단계별 최종 설정을 적용한다. 설정/활성화JSON은 `Scene/v001`에 있다.
3. `build_stairwell_scale2.py`가 기준 맵을 복제해 구조만2배로 만든다. **기존 목적지에 다시 실행하면 중단하도록 설계됐다.** 기존 맵을 수정하려면 별도 패치를 만들며 스케일을 중복 적용하지 않는다. 실행 전 사용자의 저장되지 않은 수정 여부를 확인한다.
4. `capture_stairwell_current.py`로 저장된 최종 맵을 읽기 전용 검사하고 렌더 갱신을 시도한다. 숨겨진 에디터에서는 캡처가 실행되지 않을 수 있으므로 보고서의 `screenshot_refreshed`와 이미지 수정 시각을 확인한다. 이번 정리 후 맵 검사는 통과했지만 이미지는 기존 캡처를 유지했다. 이 과정에서 맵을 재생성하지 않는다.

직접 플레이: 프로젝트 루트에서 `powershell -ExecutionPolicy Bypass -File tools/play-stairwell.ps1`. 채택한 `L_Stairwell_PlayScale2`를 연다.

## 검증과 한계

- `Scene/v002/scale2_verification.json`: 확장 시 측정. `current_verification.json`: 정리 후 저장맵 측정.
- `Workflow/asset_cleanup.json`, `file_cleanup.json`: 삭제 내역과 보호된 항목.
- 캐릭터가 직접 사용하는 이동/카메라 시각 검증과 타깃 기기 성능 측정은 별도다. 난간 세부 코너 연결과 문 상호작용은 완료로 간주하지 않는다.
- 타일 무늬 방향과 계단 선의 각도가 사용자의 요구임을 확인했다. 참/계단 본체의 추가 회전은 하지 않는다.
- 확장본의 일부 타일·점자 기하도 구조 스케일을 따라 커졌다. 월드 좌표 재질의 피치와는 구분해 재검토한다. 다음 제작은 구조 스케일 확정 후 실측 타일 모듈을 배치한다.
