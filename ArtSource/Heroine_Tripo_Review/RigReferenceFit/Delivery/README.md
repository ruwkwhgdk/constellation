# Heroine Reference Fit — 2026-09-20

기존 Player_Heroine 모델을 160cm로 정규화해 비교하고, 새 모델의 비율과 어깨 변형을 보정한 수정본입니다.

- 머리 폭: 28.76cm → 25.60cm (기존 모델 25.43cm).
- 어깨 관절 높이: 124.54cm → 128.06cm (기존 모델 128.02cm).
- 어깨 관절 간격: 24.33cm → 22.82cm. 허리, 골반, 치마와 다리 비율도 기존 모델을 참고해 조정했습니다.
- 어깨 주변 992개 정점의 웨이트를 기존 모델을 참고해 보정하고 소매 볼륨과 뒤쪽 머리 실루엣을 다듬었습니다.
- 눈·눈썹·입의 기존 디테일과 UV, 토폴로지, 텍스처를 보존했습니다. 머리는 비율 조정을 위해 축소했습니다.

## 파일

- Heroine_AnimationRig.blend: 작업용 컨트롤 리그.
- Heroine_GameSkeleton.blend / Heroine_Skeletal.fbx: 게임용 스켈레톤과 메시.
- PreviewRelaxed.fbx: 팔을 내린 비교 검사용 짧은 포즈 애니메이션.
- bone_mapping.json / retarget_chains.json: 본 매핑과 리타기팅 체인.
- validation.json: 내보내기 검증 결과.

160cm, 70,030 triangles, 94 bones, 정점당 최대 4개 영향 본. 미할당 정점과 누락 텍스처가 없는지 확인했습니다. FBX는 이 프로젝트의 Legacy FBX 임포터에서 Import Uniform Scale 100을 사용했습니다.

## Unreal

메시: /Game/Resources/Characters/PC/player_heroine_new/SK_player_heroine_new

비교용 레벨: /Game/Resources/Characters/PC/player_heroine_new/Preview/L_player_heroine_new_ReferenceFit

기존 Player_Heroine 리소스와 게임플레이 구현은 유지했습니다. 동봉 애니메이션은 포즈 검사용이며 이동 애니메이션이 아닙니다. Physics Asset은 기존 초기 설정을 유지했으며 최종 래그돌 조정은 별도 작업입니다.

비교 이미지의 순서는 REFERENCE(기존 모델), BEFORE(수정 전), AFTER(수정 후)입니다.
