# 환경 제작 정리 · 2026-09-30

사용자가 OvergrownHall의 시각 결과를 승인하고 제작 절차 정리, 불필요 리소스 제거, 기존 develop 커밋/푸시를 요청했다.

## 포함 범위

- OvergrownHall 최종 TripoFull 환경, Tripo 비둘기/리깅/애니메이션, 유지 제작 소스와 승인 비교.
- 같은 환경 제작 작업에서 만든 StairwellModular 유지 맵·키트·소스·검사 도구.
- 제작 워크플로/현재 상태, Blender 안전 실행 도구, 환경용 Python 도구.
- 평면 반사를 위한 `r.AllowGlobalClipPlane=1`, Blend/GLB/JPEG LFS 규칙, 임시파일 제외 규칙.

## 정리 결과

- 프로젝트 전체 하드/소프트 참조와 최종 맵 의존성을 조사했다.
- 초기 Blockout/Production/Scene/TripoReview 및 초기 비둘기에서 폐기 패키지106개 제거. 외부 참조가 남은 `Scene/Materials/M_Proxy_Stone`은 보존.
- Unreal API로 일반 애셋102개 제거. API가 성공으로 반환했으나 남았던 레벨4개는 정확한 대상/참조와 SHA256을 사전 검사하고 복구 사본을 만든 후 파일 단위로 제거했다. 사본은 Git에서 제외된 `Saved/EnvironmentCleanupRecovery`에 있다.
- 로그/Blender 자동 백업/비채택 Rounded 실험/진단 이미지 등32파일, 약12.68MB 제거. `file_cleanup.json`에 해시/경로 기록.
- TripoFull 원본 재질/메시 중 현재 화면에서 미사용인 일부는 파생 레시피 입력/채택 재사용 키트라 유지. 원본 Blend/FBX/텍스처·채택 기록과 검사 JSON도 유지.

## 검증

- 삭제 후 새 Unreal 프로세스에서 최종 맵 재로드:755액터, 기둥55재질, 닫힌 천장50, 비둘기28, 기존 변환/메시와 후면 나무 제거 상태 통과.
- 2026-09-30 00:43 KST 실제 렌더 갱신 후 육안 비교. Python/재질 컴파일 오류 없이 작업 프로세스 정상 종료.
- 최종 맵의 재귀 의존성에서 환경 폴더 밖의 미추적 리소스가 없는지 확인. 기존 추적된 게임 공용 리소스를 사용한다.
- 직접 플레이/성능 검사는 사용자 담당으로 남음. 과거 성능 수치를 최신 반사 해상도에 적용하지 않는다.

## 추가 승인된 별도 작업

사용자가 이어서 다른 작업 변경분도 커밋하도록 승인했다. `BP_MovingPlatform`, `BP_Player_Heroine`, `AbandonedSchool`, Heroine_Rebuild/Heroine_Tripo_Review/player_heroine_new 등의 캐릭터·폐교 변경도 별도 커밋으로 포함한다. 환경 렌더 검증을 이들 게임플레이·애니메이션의 새 검증으로 주장하지 않는다. 캐릭터의 기존 README와 검사 결과/한계를 보존하고 자동 백업·크래시 덤프·로그는 제외한다.

다음 작업자는 [재사용 절차](README.md)와 [현재 상태](../CURRENT.md)를 먼저 읽는다.
