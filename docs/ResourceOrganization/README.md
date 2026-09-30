# Constellation 리소스 경로 정책

프로젝트 자체 에셋의 기준 루트는 `/Game/Constellation`이다. 파일 이름은 이번 경로 정리에서 유지한다. 이동 명세는 `move_manifest.csv`, 과거 패키지→현재 패키지 대응은 `package_paths.json`에 기록한다.

| 영역 | 소유 리소스 |
|---|---|
| Core | GameMode, GameInstance, 공용 인터페이스·타입 |
| Gameplay | Combat, Interaction, Quests, Sequences 및 데이터 |
| Characters | Heroine/Base와 Refined, NPC, Enemies, Shared |
| Environments | School, Cave, Stairwell, OvergrownHall, SubwayEntrance, KoreanBuildings, StartIsland, Shared |
| Worlds | Title, StartIsland, AbandonedSchool, Stairwell, OvergrownHall의 플레이 맵 |
| Review | 제작 기준·키트 검토·캐릭터 프리뷰 맵 |
| UI, Input, VFX, MaterialLibrary, Procedural, Editor | 각 기능의 공유 자원과 제작 도구 |

환경 세트 내부의 Meshes/Materials/Textures 등 기존 하위 구성은 보존한다. 다른 세트에서도 공유하는 자산은 Shared에 두며, 편의를 위해 복제하지 않는다. Base와 Refined 캐릭터는 서로 다른 유지 계열이며 임의로 통합하지 않는다.

## 외부 팩 및 엔진 관리 예외

LuosCaves, ModulAbandJPSchool, Landscape의 StylizedGrassByMayu와 Stylized_PBR_Nature, Resources/VFX의 FXVarietyPack·LightShaftGenie·SwordTrailVFX_Resources는 원래 경로를 유지한다. 외부 팩 갱신과 출처 추적을 위한 예외다. 컬렉션은 탐색용이며 Cook 포함/제외 규칙이 아니다.

`__ExternalActors__`, `__ExternalObjects__`, `_GENERATED`는 엔진 관리 경로다. 파일 탐색기로 직접 이동하거나 고립 파일이라는 이유만으로 삭제하지 않는다. 에셋 이동은 Unreal AssetTools 또는 Content Browser로 수행한다.

## 제작 원본과 과거 기록

| 소유 영역 | 유지 원본 위치 |
|---|---|
| Heroine | `ArtSource/Heroine_Tripo_Review/` — AnimationWorkflow/SKILL.md가 작업 시작점 |
| Stairwell | `ArtSource/Stairwell_Modular/` — Workflow/CURRENT.md |
| OvergrownHall | `ArtSource/OvergrownHall/` — CURRENT.md와 Workflow/README.md |
| SubwayEntrance | `ArtSource/SubwayEntrance/` — CURRENT.md |
| KoreanBuildings | `ArtSource/OldKoreanBuildingA/`, `ArtSource/OldKoreanBuildingB/` |

DCC 원본 경로는 유지한다. Blender 링크·FBX/텍스처·재현 레시피 검증 전에는 보기 좋은 분류만을 위해 원본을 옮기지 않는다. 위 표가 현재 소유 영역 색인이다. 승인된 미사용 키트와 유지 입력 소스도 보존 대상이다.

과거 감사 JSON·스크린샷·버전별 결과 파일은 당시 증거로 보존한다. 현재 Unreal 제작 스크립트에서 과거 JSON을 읽을 때 `Content/Python/resource_paths.py`가 패키지 경로를 현재 위치로 해석한다. 원본 JSON 자체를 덮어쓰지 않는다. 폐기·삭제·cleanup 스크립트는 새 경로로 재활성화하지 않는다. `dev`의 실험 스크립트는 현재 제작 진입점이 아니며 그대로 재실행하기 전에 경로와 범위를 재검토한다.

## 새 리소스와 다음 이동

새 폴더는 PascalCase, 에셋은 프로젝트 유형 접두사와 의미 있는 이름을 사용한다. 기존 이름·PrimaryAssetId·DataTable 행 이름 정리는 경로 이동과 별도 작업이다. `final`, `new`, `temp`, `Copy` 같은 이름을 새 최종 산출물에 추가하지 않는다.

이동 전 참조·문자열 소비자·반입 원본과 복구 지점을 기록한다. 이동 후 참조자를 저장하고 C++/설정/제작 레시피를 갱신한 다음 엔진 Fixup으로 리디렉터를 정리한다. 새 프로세스의 참조 검사·맵 로드·Cook 결과와 실제 플레이/시각 검토를 구분해 기록한다.

이번 작업의 복구 기준은 `Saved/ResourceOrganization/20260930/recovery.json`이다. 미변경 바이너리는 검증된 로컬 Git LFS 객체, 현재 미커밋 파일은 recovery_files 복사본을 사용한다. 완료 기록을 확인하기 전 이 Saved 하위 폴더를 삭제하지 않는다. 다른 작업의 미커밋 파일을 Git reset으로 복구하지 않는다.

## 실행 기록 — 2026-09-30 ~ 2026-10-01

자체 패키지 1,786개를 이동했다(환경 1,427, 캐릭터·UI 235, 핵심 기능·데이터 112, 맵·BuiltData 12). 외부 팩과 DCC 원본 위치는 유지했다. 이동 후 비어 있는 이전 에셋 폴더 213개를 제거했다. 파일 이름이나 게임 로직은 이번 정리 대상이 아니다.

`verification/`의 새 프로세스 검사 결과:
- 새 누락 참조, 중복 원본, 자체 리디렉터, 반입 원본 경로 변경, 복구 도구 의존성: 모두 0.
- 전체 World 27개 유지. 이동한 11개 맵의 액터 6,517개와 지하철 목적지·도착 Transform이 이동 전 기록과 일치.
- Blueprint 167개 컴파일, 애니메이션 계열 72개의 Skeleton 연결, 퀘스트 원본 값 대조 통과.
- 외부 액터·오브젝트 47개 파일의 SHA256 유지. 기존 외부 팩·엔진 관리 리디렉터 78개 유지.
- 경로 도구·현재 맵 소비자 테스트 14개 및 지하철 전환 상태 테스트 두 묶음 통과. 변경된 Python 145개 문법 검사 통과.

탐색 컬렉션 6개는 현재 소스 관리 체크아웃을 사용하지 않는 작업 환경에 맞춰 **Local**로 생성했다. 다른 작업자에게 자동 공유되는 설정이 아니다.

대량 이동 중 엔진 참조 갱신 지연·StringTable 저장 문제를 발견하여 해시로 검증한 원본에서 재질 8개, 애니메이션 1개, 퀘스트 1개의 영향을 받은 필드를 복구했다. 애니메이션은 205개 뼈/시간 샘플을 대조했다. 임시 CoreRedirects는 참조자 저장 후 제거했으며 최종 검사는 임시 보정 없이 수행했다. Blueprint 컴파일과 맵 로드는 엔진의 재인스턴싱 상태가 섞이지 않도록 별도 프로세스로 검증했다.

`Plugins/ConstellationResourceTools`는 Python에 노출되지 않은 누락 Skeleton 복구용 **Editor 전용** 보조 코드다. 기존 Skeleton을 교체하지 않으며 런타임 에셋에서 이 모듈을 참조하지 않는 것을 검사했다.

Win64 에디터·게임 빌드와 전체 Cook이 통과했다(실제 Cook 패키지 2,251개, 플랫폼 제외 7개). 최초 패키징은 종료 코드 0이었지만 Cook과 Stage가 서로 다른 Zen 데이터 저장소를 사용하여 예전 패키지를 읽는 문제가 실행 검사에서 발견됐다. 검증 실행 스크립트의 프로세스 환경 `UE-ZenSubprocessDataPath`를 통일하고, 완료된 Cook 결과로 재패키징하여 2,251개가 포함된 것을 확인했다. 최종 패키징 종료 코드는 0이다.

타이틀 기본 진입·StartIsland·AbandonedSchool·Stairwell의 패키징 실행 파일에서 각 15초 NullRHI 시작 검사를 통과했다. 네 맵 모두 실제 World 진입·맵 로드 완료·시간 제한 정상 종료를 확인했으며 오류/누락 패키지 로그는 0개였다. 종료 코드만으로 성공을 판단하지 않는다. 결과와 원본 로그 경로는 `verification/packaging.json`, 실행 결과물은 `Saved/ResourceOrganization/20260930/Packaged/Windows/`에 있다.

실행 경고는 타이틀 2건, 시작 섬 6건, 학교 134건, 계단실 6건으로 별도 보존했다. 인증서 저장소 접근, 빈 SpawnActor 클래스, 시계탑·기둥의 정적/비정적 컴포넌트 부착, NavMesh 관련 경고를 포함하며 이번 경로 정리에서 게임 동작을 바꾸어 없애지 않았다. 경고가 전부 이동 전부터 존재했다는 뜻은 아니며, 별도 플레이 검토 대상으로 남긴다.

위 자동 검사는 실제 화면 품질이나 이동 감각의 사용자 플레이 검토를 대신하지 않는다. Stairwell·OvergrownHall의 현행 Workflow에 따른 사람 검토와 DCC 원본 재배치는 별도 범위로 남는다.

독립 검토의 중요 지적 3종(프리뷰 맵 저장/보고, 계단실 재현 입력, 현재 작업 문서 경로)을 수정했다. 실제 레시피의 정적 문자열 조합과 맵 입출력을 이동 명세와 비교하는 회귀 검사에서 수정 전 실패를 확인했고, 수정 후 전체 14개 테스트가 통과했다. 과거 감사 JSON과 스크린샷은 수정하지 않았다. 상세 판단은 `verification/review_result.json`에 기록했다.

## 추가 디스크 공간 관찰

패키징 중 `.git/lfs/tmp`가 약 87GiB까지 누적된 것을 확인했다. 15분 이상 지난 비사용 임시 파일을 최대 45GiB 정리하는 제안은 자동 승인 검토가 별도 승인이 필요하다고 거부하여 실행하지 않았다. 사용자 승인 질문은 별도로 전달했다. 정식 LFS 객체 및 이번 복구 자료는 삭제 대상이 아니다. 이 추가 정리는 위 리소스 이동과 패키징 검증의 완료 여부와 별개다.
