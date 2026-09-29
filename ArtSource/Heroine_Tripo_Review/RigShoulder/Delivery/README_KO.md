# Heroine — 어깨 비율 보정 리깅본

승인된 DetailFinish2 모델에 애니메이션 제작용 리그와 게임용 스켈레톤을 추가했습니다. 기본 마네킹의 체형을 복제하지 않고 이 캐릭터에 맞췄습니다. 기존 Constellation의 Content, 소스 코드, Animation Blueprint는 교체하지 않았습니다.

## 파일

- `Heroine_AnimationRig.blend`: 애니메이터용. Rigify 컨트롤, 원본 메시와 패킹된 텍스처 포함.
- `Heroine_GameSkeleton.blend`: 컨트롤을 제거한 게임용 메시와 스켈레톤. 전방 +X, 위 +Z.
- `Heroine_Skeletal.fbx`: 위 게임용 파일의 바인드 포즈. 새로운 Unreal Skeleton으로 임포트.
- `export_game_rig.py`: 조작 리그에서 게임용 뼈로 움직임을 베이크하여 FBX로 내보내는 스크립트.
- `bone_mapping.json`, `retarget_chains.json`: 조작/변형 뼈 대응과 후속 IK Retargeter 구성 정보.
- `renders/`: 실제 포즈 테스트 렌더. `QA_*` Action은 검사 포즈이며 완성된 게임 애니메이션이 아닙니다.
- `*_validation.json`, `validation.json`, `surface_preservation.json`: 실제 검사 결과.

## 구성

- 키 160cm, 70,030삼각형. 93개 변형 뼈와 1개 root, 총 94개 게임용 뼈.
- 정점당 최대 4개 웨이트. 미할당 정점 없음.
- 골반, 몸통, 목, 머리, 양팔/양다리, 손가락, 발가락 컨트롤.
- 팔·다리 IK/FK 전환, 손·발 목표점과 발뒤꿈치/발 회전 컨트롤. 스트레치 기본 비활성.
- 팔다리 분할 변형 뼈. 게임으로 전달되지 않는 B-Bone 곡선 변형과 비균일 스케일을 배제했습니다.
- 치마 8방향 × 2개 뼈: 허벅지 추종 및 굽힘 시 여유 공간 보정, 추가 수동 조절 가능.
- 머리카락 4체인 × 2개 뼈: 측면/뒤쪽 FK. 앞머리와 정수리는 눈을 가리는 형태를 유지하도록 주로 머리에 고정.
- 팔찌는 손목 쪽 전완에 연결. 눈·눈꺼풀은 머리에 고정하여 얼굴과 함께 이동.

## 블렌더 사용

Blender 5.2.1에서 제작/검증했습니다. `Heroine_AnimationRig`를 선택하고 Pose Mode로 전환합니다. 생성된 Rigify UI 스크립트가 실행돼야 리그 전용 패널과 스냅 도구를 사용할 수 있습니다. 이 파일의 스크립트를 검토한 뒤 해당 파일에서 실행을 허용하세요. 전역 보안 설정은 변경하지 않았습니다.

`root`는 전체 이동, `torso`는 몸통 이동, `hips`/`chest`는 골반/가슴, `head`/`neck`은 머리/목입니다. `upper_arm_parent.L/R` 및 `thigh_parent.L/R`의 `IK_FK`는 **0=IK, 1=FK**입니다. 기본 파일은 FK 1입니다. IK에서는 `hand_ik.L/R`, `foot_ik.L/R`를 이동합니다. FK에서는 `upper_arm_fk`, `forearm_fk`, `thigh_fk`, `shin_fk`를 회전합니다. Rigify의 스냅 기능으로 현재 자세를 맞춘 뒤 전환하고 전환 값을 키로 기록하세요.

손가락은 각 마디 컨트롤과 `*_master`를 사용합니다. `skirt_XX.01/02`와 `hair_*`는 추가 조절용입니다. `DEF-`, `ORG-`, `MCH-` 뼈는 직접 애니메이션하지 않습니다.

조작 파일의 리그 오브젝트에는 모델 원본 크기에서 160cm로 맞추기 위한 균일 스케일이 있습니다. 이를 임의로 Apply 하지 마세요. 게임용 파일은 스케일을 지오메트리/스켈레톤에 반영해 오브젝트 변환을 정리했으며, 제공된 exporter가 좌표와 크기를 처리합니다.

## 내보내기

애니메이션을 저장한 조작 파일을 별도 Blender 백그라운드 프로세스에서 엽니다. 스크립트는 입력 blend를 덮어쓰지 않습니다. 이 폴더의 게임용 blend와 매핑 파일도 함께 유지해야 합니다.

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -b --enable-autoexec --python './export_game_rig.py' -- --source './Heroine_AnimationRig.blend' --out './Heroine_Motion.fbx' --bake --start 1 --end 60
```

현재 활성 Action/NLA를 매 프레임 평가하여 변형용 뼈에 베이크합니다. Rigify 드라이버나 치마 추종 제약 자체가 Unreal로 넘어가는 것은 아닙니다. 바인드 포즈만 내보내려면 `--bake`를 생략합니다. 실행 폴더에 맞춰 경로를 지정하세요.

## 언리얼 적용 원칙

이것은 **캐릭터 전용 스켈레톤**이며 Manny/Quinn 및 기존 Player_Heroine Skeleton과 동일한 스켈레톤이 아닙니다. 새로운 Skeleton으로 임포트하고, 기존 동작 재사용은 IK Rig/IK Retargeter로 처리합니다. 엔진 설치 버전 5.8의 별도 검증 프로젝트에서 임포트했습니다. 현재 게임의 구현 변경은 하지 않았습니다.

메시/스켈레톤 생성과 160cm 크기 확인은 통과했습니다. Blender 재입력에서도 94개 뼈, 단일 root, 삼각형 수와 텍스처 로딩을 확인했습니다. Epic Interchange에는 `FbxCluster vs FbxPose` 바인드 행렬 경고가 남아 있습니다. Blender 베이크 왕복 오차는 0.01mm 미만이지만, 이것만으로 Unreal에서의 모든 애니메이션 재생을 보증하지는 않습니다. 실제 프로젝트 통합 시 엔진에서 기준 포즈와 베이크 애니메이션을 함께 확인해야 합니다.

## 보존 및 검증 범위

어깨 관절 간격을 약 32.0cm에서 27.2cm로 좁히고 약 0.64cm 낮췄습니다. 상부 가디건을 부드럽게 좁히며 팔과 손은 형태를 유지한 채 안쪽으로 옮겼습니다. UV, 면의 재질 지정과 패킹 텍스처는 유지했습니다. 얼굴, 머리카락, 하체 좌표는 보존했습니다. 얼굴, 눈 디테일, 무표정 입은 재조형하지 않았습니다.

기본 자세, 팔 내리기, 팔꿈치 굽힘, 손가락 굽힘, 머리 회전, 중간 깊이의 앉기 자세를 렌더로 검사했습니다. 양손·양발 IK 목표점 도달, 웨이트 정규화, 드라이버 유효성, 게임용 뼈 자세 전달과 베이크 FBX 왕복을 수치 검사했습니다. 세부 수치는 JSON에 있습니다.

**아직 포함되지 않은 작업:** 눈동자 시선/눈깜빡임/말하기 등 표정 리깅, 깊은 스쿼트·큰 다리 벌림·격한 액션 전 범위의 의상 충돌 보정, 런타임 헤어/치마 물리 및 Physics Asset, Unreal Control Rig/IK Retargeter 에셋, 기존 게임 코드/ABP 연결. 표정 리깅에는 현재 얼굴의 변형용 토폴로지와 눈 구조에 대한 별도 설계가 필요합니다.

공식 참고: [IK Rig Retargeting](https://dev.epicgames.com/documentation/unreal-engine/ik-rig-animation-retargeting-in-unreal-engine), [FBX Skeletal Mesh Pipeline](https://dev.epicgames.com/documentation/unreal-engine/fbx-skeletal-mesh-pipeline-in-unreal-engine).
