# 폐교 환경 개선 및 리소스 정리

## 목표
- 학교와 동굴이 뒤섞인 환경을 원화에 맞게 구성하고 재질·조명·프랍의 일관성을 높인다.
- 통로/발판/계단의 연결, 추락 복귀 및 이동 장치의 외형을 개선한다.
- 시계탑과 TV 교실, 체육관의 최종 피드백을 반영한다.
- 사용되지 않는 시각 리소스를 제거하고 develop에 목적별 변경 이력을 남긴다.

## 변경 분류
| 분류 | 대상 | 내용 |
|---|---|---|
| 공유 재질 | CaveStart, CaveJumpTop, SchoolCave, Landscape/Cliff | 동굴 돌·이끼·학교 표면·빛 표현의 누적 재질 조정 |
| 학교 및 동굴 구역 | AVClassroomSide, ArtClassroomSide, CaveJumpBottom, CheckpointCave, ClassCheckpoint, ClassroomJumpBottom, ClassroomJumpTop, Dump, Dustchute, EntranceSlime, Hollow, MiddleCorridor, MushroomJump, MusicClassroom, Sector4Slime, SlimeCorridor | 구역별 암벽·통로·학교 구조·환경 효과와 프랍용 애셋 |
| 엘리베이터 허브 | ElevatorHubBasement, ElevatorHubGround, ElevatorHubUpper | 층별 환경, 플랫폼, 기둥과 승강기 외형 |
| Sector 5 | ClassroomDiary, LargeCave, LargeCavePassage | 교실과 동굴의 연결, 암벽·개구부, 이끼·물·발광 표현 |
| 시계탑 | ClockTowerExterior, ClockTowerInterior, ClockTowerRoof | 벽돌/콘크리트 외벽과 백색 wall_line 구분, 창문, 내부 학교 재질, 회전 계단, 막힌 기어 중심축, 뾰족한 지붕 |
| Sector 3 | ClassroomTV, GymArena, GymCorridor | TV 교실과 기존 칠판 기반 경고 표면, 체육관 지붕·벽 중첩·푸른 암흑과 절벽 깊이 표현 |
| 게임플레이 요소 | BP_FallTrigger, BP_MovingPlatform, BP_FallingElevator, BP_Fluorescent_Light, BP_School_Gate, BattleGate | 기존 상호작용 요소의 누적 변경 및 연관 외형 |
| 레벨 통합 | AbandonedSchool.umap, AbandonedSchool_BuiltData.uasset | 모든 구역 배치·재질·광원·충돌·연결부 조정을 포함한 최종 레벨 |
| 렌더링 설정 | DefaultEngine.ini | Planar Reflection용 r.SupportGlobalClipPlane 활성화 |

## 커밋 구성
1. 공유 재질 개선.
2. 일반 학교/동굴 구역 애셋 추가.
3. 엘리베이터 허브 애셋 추가.
4. Sector 5 동굴/시계탑 애셋 추가.
5. Sector 3 TV 교실/체육관 애셋 추가.
6. 게임플레이 Blueprint 및 전투 게이트 관련 변경.
7. 최종 레벨과 렌더링 설정 통합.
8. 미사용 리소스 제거 및 전체 변경/검증 목록.

레벨 파일은 바이너리이므로 과거 구역별 상태를 인위적으로 복원하지 않고 최종 통합 커밋으로 저장한다. 애셋 선행 커밋 후 레벨을 반영한다.

## 삭제 판정
리소스 카탈로그의 648종은 외형 중심 목록이므로 삭제 화이트리스트로 사용하지 않았다. 전체 Asset Registry에서 hard/soft package, searchable name, management 참조를 추적했다. 모든 맵(테스트/쇼케이스 포함), Blueprint, 데이터·애니메이션·기타 기능성 애셋을 보존 루트로 삼았다. Source/Config의 명시 경로 및 런타임 애셋에 기록된 문자열 경로도 보존했다.

삭제 대상은 이 루트 집합에서 도달할 수 없으며 후보 집합 바깥의 referencer가 없는 StaticMesh/Material/MaterialInstance/MaterialFunction/Texture 계열이다. 동적 로드 여부가 불명확한 기능성 애셋은 제거하지 않았다. 개별 삭제 경로·종류·바이트 크기·SHA-256은 `2026-09-13-removed-resources.csv`에 기록한다.

로컬 복구 백업: `dev/unused-resource-backup-2026-09-13.zip`. dev는 Git에서 제외하며 백업에는 미추적 애셋도 포함한다. Git LFS의 과거 버전 저장 용량은 이번 삭제로 줄어들지 않는다.

## 검증 결과
- 조사 애셋 4,130개 → 보존 3,317개. 미사용 시각 리소스 813개, 1,881,295,622 bytes (약 1.75 GiB) 제거.
- StaticMesh 461, Texture2D 216, MaterialInstanceConstant 117, Material 17, MaterialFunction 2.
- Git 추적 애셋 759개 삭제, 미추적 중간 애셋 54개 로컬 삭제. 전부 복구 ZIP에 포함.
- 별도 UnrealEditor-Cmd 프로세스에서 Asset Registry 재스캔: 보존 애셋 → 삭제 애셋 참조 0건.
- 변경 애셋과 L_Title/L_StartIsland/AbandonedSchool을 포함한 309개 로드 성공, 실패 0건.
- 변경 Blueprint 5개 컴파일 성공. 새 프로세스에서 검사한 Blueprint 6개 모두 BS_UP_TO_DATE.
- 이전 리소스 카탈로그 648개 항목과 삭제 목록 교집합 0개.
- 검증 commandlet 종료 코드 0, 오류 0건. 기존 BP_Player_Heroine의 DodgeTimeline/DodgeTrack invalid curve 경고가 있으며 정리 전 로그에서도 확인됨. 나머지 경고는 MCP 플러그인 안내.
- 에디터의 개별 삭제 호출 지연으로 저장된 에디터를 종료하고, 백업 해시와 일치하는 잔여 파일만 오프라인 삭제했다. 검증은 기존 메모리 캐시를 사용하지 않는 새 프로세스에서 수행했다.
- 전체 게임 진행과 Shipping 패키징 검증은 이번 작업 범위에 포함하지 않았다.
