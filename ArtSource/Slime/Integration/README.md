# Slime Unreal integration

2026-10-14: 신규 젤 슬라임 적용, 실제 엔진 재생/전투 검증, 이전 모델 리소스 제거 완료.

## 현재 리소스

Unreal 폴더: `/Game/Constellation/Characters/Enemies/Slime_Liquid`

- `SKM_Slime_Liquid`: 게임용 스킨 메시. 14본, 26,700 triangles. 기존 Root/Center/Top 바인드 호환.
- `SM_Slime_Liquid`: 정적 메시 및 공용 재질의 미리보기 메시 대체.
- `AS_Slime_Liquid_Idle`: 신규 Idle 원본, 24fps / 4초.
- `AM_Slime_Liquid_Idle`: 실제 4초 길이의 새 Idle 몽타주.
- `Materials/`: 외피, 내부 밀도, 물방울, 눈 및 노란 슬라임 외피 변형.
- 검토 맵: `/Game/Constellation/Review/Slime/L_Slime_Liquid`.

게임에서 참조하던 `Slime_Normal/Animation/AS_Slime_Idle`도 같은 새 Idle로 갱신했다.
기존 Move/Attack/Damaged/Dead/Jump와 몽타주 참조 및 타이밍은 유지했다. 새 몸체가
공격/사망 시 접히던 문제는 Top 변형을 Center 변형에 맞춰 보정했다. Root/Center,
클립 길이, 노티파이/몽타주를 보존했다.

Base/Patrol/Boss/Yellow, 플레이어 Slime, NPC Slime 및 사용 중인 검토/학교 맵을 갱신했다.
기존 캡슐 크기와 충돌 설정은 유지하고 새 메시 바닥이 캡슐 바닥과 맞도록 메시 높이를 보정했다.
CombatRecipes 및 관련 생성/감사 도구의 메시 경로도 새 리소스로 변경했다.

## 원본과 유지 방법

모델 원본은 `../Production/Slime_Liquid.blend` revision 10이며 변경하지 않았다.
Unreal에는 이 폴더의 `SKM_Slime_Liquid.fbx` / `SM_Slime_Liquid.fbx`를 사용한다.
`export_compatible.py`가 원본을 cm 단위와 기존 게임 바인드로 변환하고 Idle을 샘플링한다.
Blender 실행은 반드시 프로젝트 `tools/run-blender.ps1` 보호 런처를 사용한다.

`import_unreal.py`, `materials_unreal.py`, `retarget_gameplay.py`, `ground_fit.py`가 각각
임포트, 엔진 재질, 전투 동작 호환, 접지를 담당한다. `replace_unreal.py`와
`cleanup_unreal.py`는 완료된 일회성 마이그레이션 기록이다. 삭제된 구 리소스를 전제로 하므로
전체 스크립트를 무조건 재실행하지 않는다. 복구본은 `before-integration.zip`에 보존했다.

Cycles의 실제 볼륨/투과 셰이더는 FBX로 전달되지 않는다. 엔진 외피 투명도와 별도 내부
밀도 메시로 젤을 근사했다. Unreal 조명과 투명 정렬에 따라 Blender 렌더와 차이가 있다.
노란 변형은 외피 색을 유지하며 내부/물방울에는 기본 보라색 재질을 공유한다.
물방울은 초기 수직 낙하, 몸체 접선 정렬, 하단 수직 낙하, 웅덩이 내부 복귀를 유지한다.
크기를 0으로 줄이지 않고 내부/바닥 잠김을 재질에서 처리한다.

## 검증 결과

- `delivery-verification.json`: FBX 재임포트, 14본, 치수/변형 검사 통과.
- `asset-verification.json`: 6개 Blueprint 생성/컴파일, 메시/재질, 애니메이션 스켈레톤,
  4초 Idle, 97개 샘플의 낙하 및 일정 크기 검사 통과.
- `playback-report.json`: 실제 PIE에서 Idle 두 루프와 Move/Attack/Damaged/Dead/Jump 재생 통과.
  `Preview/`에 실제 엔진 캡처 보존. 공격 시 몸체 접힘 보정 후 다시 확인했다.
- `saved-verification.json`: 새 프로세스에서 저장된 검토 맵과 AbandonedSchool을 다시 로드해
  슬라임 참조 및 새 Idle 몽타주 길이 확인.
- `post-cleanup-verification.json`: 구 리소스 삭제 후 새 메시/정적 메시 로드,
  Blueprint/맵 재검사, 남은 구 메시/재질/텍스처 참조 없음.
- `combat-test-post-cleanup.json`: 삭제 후 실제 렌더링 게임에서 SlimeScout_v2 18초 시나리오 통과.
  장애물 우회, 추격, 공격, 귀환, 액션 취소, 체력 100 회복 확인.
  원본 로그: `Saved/CombatAudit/PlayRuns/8bbdc80eda0b4ebda990d9f54b972474/`.
- 전투 레시피 Python 테스트 13개 통과. 전체 게임 패키징과 플레이어의 모든 벽타기 경로는
  이번 검증 범위에 포함하지 않았다.

## 제거 및 보존

제거한 `Slime_Normal` 리소스:
`SKM_Slime_Normal`, `SM_Slime_Normal`, `SKM_Slime_Normal_CtrlRig`,
`MI_Slime_Normal`, `MI_Slime_Yellow`, `T_Slime_Normal`, `T_Slime_Yellow`,
`Animation/AM_Slime_Idle`.

언리얼 참조 교체/삭제 후 남았던 참조 없는 ObjectRedirector 파일 두 개도 정리했다.
최종 결과는 `cleanup-report.json`에 기록했다. 기존 모델은 Content에 남아 있지 않다.
공용 `SK_Slime_Normal`(14본으로 확장), `PHM_Slime` 및 사용 중인 전투 애니메이션은
기능 호환을 위해 유지한다. 복구 ZIP은 Content 밖에 있어 게임 리소스에 포함되지 않는다.
