# Constellation 리소스 경로 정리 계획

작성: 2026-09-30. 상태: **제안 / 경로 변경 미실행**.

목표는 리소스를 찾고 수정하는 위치를 예측할 수 있게 만들면서 게임, 맵 스트리밍, 재반입, 제작 재현을 유지하는 것이다. 이번 요청은 계획 수립이며 에셋 이동·이름 변경·삭제·커밋은 수행하지 않는다. 이후 실행은 이 계획과 이동 명세를 기준으로 기능별로 나눈다.

## 확인한 현재 상태

- 현재 디스크 Content 패키지 3,559개, 맵 27개. 이후 동시 작업으로 수치는 달라질 수 있으므로 실행 직전 재집계한다.
- 환경 제작물이 `Art` 362개, `Environment` 530개, `Resources/Environments` 347개로 나뉜다. 일부는 서로 참조하거나 구매 팩의 파생본이다.
- `Blueprints` 181개 안에 게임 기반, 캐릭터, 상호작용, UI, 데이터, 반입 파이프라인이 섞여 있다.
- `Data`와 `Blueprints/System/Data`에 이름이 같은 구조체·테이블 경로가 있다. 실제 클래스, Redirector, 참조 대상을 확인하기 전에는 중복으로 합치지 않는다.
- `LuosCaves` 763개, `ModulAbandJPSchool` 506개 등 외부 팩이 상당 부분을 차지한다. 구매 팩처럼 보이는 폴더도 프로젝트 수정 여부는 별도 확인한다.
- `/Game/` 문자열을 포함하는 Python 파일은 Content/Python 124개, ArtSource 26개, dev 208개다. 숫자는 수정할 파일 수가 아니라 경로 영향 조사 범위다. 과거 감사/카탈로그 파일과 현재 제작 레시피를 구분해야 한다.
- 기존 대용량 미사용 에셋 232개 삭제는 별도 완료된 작업이다. 이번 재배치에서 삭제를 추가로 섞지 않는다.
- 지하철 최신 연결은 페이드/OpenLevel 방식이 아니라 두 맵의 비동기 스트리밍과 상대 좌표 전환이다. 예전 문서의 플레이 테스트 항목을 재사용하지 않는다.

## 기준과 선택

Epic은 에셋 이름 규칙을 권장하지만 모든 프로젝트에 단 하나의 폴더 트리를 강제하지 않는다. 아래 구조는 Epic의 이름/참조 관리 원칙과 프로젝트 전용 최상위 폴더를 사용하는 실무 스타일을 이 프로젝트에 적용한 제안이다.

| 접근 | 장점 | 이 프로젝트에서의 판단 |
|---|---|---|
| 유형별 최상위 분리: Blueprints/Meshes/Textures | 단순하고 유형별 작업이 쉬움 | 한 캐릭터·소품의 수정 위치가 계속 분산되므로 비추천 |
| 기능·콘텐츠별 묶음 + 공용 라이브러리 + 외부 팩 분리 | 관련 작업과 소유권이 명확함 | **추천** |
| 구매 팩까지 모두 새 트리로 완전 재배치 | 최상위 폴더 수가 가장 적음 | 업데이트·문서·원본 대조 비용이 커 후순위 선택 작업 |

큰 원칙은 **프로젝트 소유 / 외부 원본 / 제작 원본 / 검토·실험**의 구분이다. 프로젝트 소유 에셋은 기능과 콘텐츠가 1차 분류이며, 에셋 유형은 필요한 하위 폴더에서 구분한다. Shared는 여러 소유 영역이 실제로 공유하는 리소스만 넣는다.

## 제안 Content 구조

```text
Content/
  Constellation/
    Core/                  # GameInstance, GameMode, 프로젝트 공통 기반
    Gameplay/
      Combat/
      Interaction/
      Quests/
      Travel/
      Sequences/           # 대화·진행 시퀀스 시스템 및 데이터
    Characters/
      Heroine/
      NPC/
      Enemies/
      Shared/              # 실제 공유 애니메이션·리그 등
    Environments/
      School/
      Cave/
      Stairwell/
      OvergrownHall/
      SubwayEntrance/
      Shared/
    Worlds/
      Title/Maps/
      StartIsland/Maps/
      AbandonedSchool/Maps/
      Stairwell/Maps/
      OvergrownHall/Maps/
    UI/                    # Widgets, Fonts, Icons 등
    Input/
    Audio/                 # 여러 기능에 공통인 오디오
    VFX/                   # 프로젝트 공용 효과
    MaterialLibrary/       # 공용 마스터 재질·함수·기본 텍스처
    Procedural/            # 여러 환경에서 공유하는 PCG 규칙
    Editor/                # Import 파이프라인·유틸리티 에셋
    Review/                # 팀이 유지하는 검토·카탈로그 맵
  LuosCaves/               # 외부 팩: 초기에는 기존 경로 유지
  ModulAbandJPSchool/      # 외부 팩: 초기에는 기존 경로 유지
  <OtherVendorPack>/      # 출처 확인된 외부 팩, 해당 팩의 기존 루트
  Developers/             # 개인 실험
  Collections/            # 에셋을 복사하지 않는 분류
  Python/                 # Unreal Python 검색 경로, 초기 유지
  __ExternalActors__/     # Unreal 관리
  __ExternalObjects__/    # Unreal 관리
```

위 트리는 분류 체계다. 내용 없는 폴더를 미리 모두 만들지 않는다. `<OtherVendorPack>`은 새로 만들 이름이 아니라 현재 팩별 위치를 유지한다는 표기다. 예를 들어 기존 VFX 팩의 중첩 경로도 1차 작업에서는 그대로 남길 수 있다.

`Environments/School/Props/Desk`처럼 소품 단위로 메시·재질·텍스처를 함께 둔다. 대규모 Stairwell 키트나 Heroine처럼 내용이 많은 경우 내부에 `Meshes`, `Materials`, `Textures`, `Animations`, `Blueprints`를 둔다. 모든 소품에 세 폴더를 강제로 만들지는 않는다.

캐릭터의 Base/새 제작본을 이름만 보고 합치지 않는다. 스켈레톤·애니메이션 호환성을 확인하고 각 리그 계열을 유지한다. `CommonAnimation`도 여러 캐릭터가 공유하는지 확인한 뒤 Characters/Shared 또는 Heroine으로 귀속시킨다.

## 현재 → 목적지 배치 규칙

| 현재 범위 | 목적지 | 판정 규칙 |
|---|---|---|
| Blueprints/System | Core, Gameplay의 해당 기능 | GameMode/GI는 Core, BattleManager는 Combat, SequenceManager는 Sequences |
| Blueprints/Actor | Gameplay/Interaction 또는 해당 콘텐츠 묶음 | 범용 동작은 Gameplay, 특정 소품 전용 Blueprint는 그 소품 옆 |
| Blueprints/Character + Resources/Characters | Characters | 캐릭터의 Blueprint·메시·애니메이션을 같은 소유 영역에 배치 |
| Blueprints/Widget + Resources/UI + Resources/Fonts | UI | Widgets/Fonts/Icons 등의 내부 구분 |
| Data/Quests | Gameplay/Quests/Data | C++ 기본 DB 경로, AlwaysCook, 관련 데이터 에셋을 한 배치에서 변경 |
| Data + Blueprints/System/Data | Gameplay/<기능>/Data | 클래스·실제 참조로 소유 기능 결정; 동명 에셋 자동 병합 금지 |
| Inputs | Input | InputAction/MappingContext 연결 유지 |
| Art/<지역> | Environments/School 또는 Cave의 해당 세트 | 지역명·사용 맵·제작 출처 확인. 맵 전용 생성물은 Worlds/<월드>/Generated |
| Environment/<세트> | Environments/<세트> | 재사용 키트와 유지 제작 입력을 함께 보존 |
| Resources/Environments | Environments/<세트> 또는 Shared | 팩 원본은 팩 정책 적용, 프로젝트 파생본은 소유 세트에 배치 |
| Landscape | Environments/Shared 또는 관련 지형 세트 | 외부 식생 팩 원본은 기존 위치 유지. Foilage 오타는 자체 에셋 재배치 때 해결 |
| PCG | Procedural 또는 Environments/<세트>/Procedural | 범용 규칙과 맵/환경 전용 그래프 구분 |
| Resources/Common | MaterialLibrary 또는 실제 소유 기능 | Common 전체를 새 Shared에 일괄 이동하지 않음 |
| Resources/VFX | VFX 또는 관련 기능 | FXVarietyPack/LightShaftGenie 같은 외부 원본은 일단 유지 |
| Resources/LevelSequence | Worlds/<월드>/Sequences 또는 Gameplay/Sequences | 시네마틱 에셋과 게임 진행 시스템을 구분 |
| Resources/Weapons | Characters/Shared/Equipment 또는 해당 캐릭터 | 무기 모델과 전투 시스템 코드의 소유권은 구분 |
| Levels의 플레이 맵 | Worlds/<월드>/Maps | 맵 이름은 1차 이동 시 유지 |
| 제작용 KitReview/Reference/Preview 맵 | Review/<세트>/Maps | 제작·검수에 필요한 맵으로 유지, 실제 패키징 참조는 별도 검사 |

특수 사례: `OldKoreanBuildingA/B`는 이름만으로 구매 원본인지 직접 제작물인지 단정할 수 없다. 반입 메타데이터/소스/사용처를 조사해 외부 팩이면 그대로 유지하고 자체 제작이면 해당 건물 세트로 옮긴다. 나머지 분류 불명 항목도 임의 Misc 폴더로 몰지 않고 이동 명세에서 원위치 유지 및 이유를 남긴다.

목표 경로 예시:

- `/Game/Levels/L_StartIsland` → `/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland`
- `/Game/Environment/StairwellModular/Scene/Maps/L_Stairwell_PlayScale2` → `/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2`
- `/Game/Data/Quests/DA_QuestDatabase` → `/Game/Constellation/Gameplay/Quests/Data/DA_QuestDatabase`
- `/Game/Blueprints/Widget/WBP_PlayerHUD` → `/Game/Constellation/UI/Widgets/WBP_PlayerHUD`

첫 이동에서 `PlayScale2`, `TripoFull`, `player_heroine_new` 같은 기존 에셋 이름까지 한 번에 바꾸지 않는다. 안정화 후 현재 의미를 조사하고 별도 명칭 변경 명세로 처리한다. 목표 중복 경로가 생기면 덮어쓰기/자동 통합하지 않고 해당 묶음을 보류한다.

## 외부 팩과 탐색 방식

LuosCaves 등은 업데이트·원본 비교를 위해 패키지 내부 트리와 경로를 초기 유지한다. 프로젝트 전용 파생 재질·수정 메시·전용 Blueprint는 Constellation 아래에 두고 원본을 참조한다. 이미 원본을 직접 수정한 에셋은 출처와 변경 내용을 먼저 기록한다.

외부 팩을 덜 보이게 하는 목적에는 Constellation 폴더 즐겨찾기와 공유 Collections를 사용한다. `Production`, `Review`, `ThirdParty`, `School`, `Cave`, `Heroine` 같은 컬렉션은 경로를 바꾸거나 에셋을 복사하지 않는다. 컬렉션·폴더 이름 자체는 Cook 포함/제외 정책이 아니다.

업데이트하지 않을 것으로 확정한 팩만 마지막 단계에서 `Content/ThirdParty/<Pack>` 이동을 검토한다. 전체 프로젝트 재배치와 동시에 팩을 플러그인으로 바꾸지 않는다. `/Game`에서 플러그인 마운트로 바뀌는 것은 별도 작업이다.

## 명명 규칙

- 자체 폴더는 PascalCase 영문/숫자, 에셋은 `유형접두사_대상_설명_변형`을 기본으로 한다. 공백·모호한 새 이름은 금지한다.
- `SM_`, `SK_`, `SKEL_`, `PHYS_`, `M_`, `MI_`, `T_`, `BP_`, `ABP_`, `WBP_`, `DT_`, `AS_`, `AM_`, `BS_`, `LS_`는 기본 접두사로 사용한다.
- 이 프로젝트의 `BPI_`, `ST_`, `NS_`, `IA_`, `L_` 등은 채택 규칙으로 명시한다. Epic 샘플의 BI_/F_/FXS_ 표기와 다르다는 이유만으로 기존 전체 이름을 바꾸지 않는다.
- 신규 `final`, `new`, `temp`, `Copy`, 의미 없는 번호를 최종 자산명에 넣지 않는다. LOD·의도된 변형과 제작 버전은 구분한다.
- 기존 이름의 정리는 경로 이동 검증을 끝낸 다음 별도 배치로 한다. 특히 PrimaryAssetId, FName 기반 조회, DataTable 행 이름, SaveGame 문자열이 걸린 이름은 단순 파일명 규칙으로 변경하지 않는다.

## Content 밖의 원본·도구

제작 원본의 장기 분류는 `ArtSource/Characters`, `ArtSource/Environments`, `ArtSource/Shared`다. 각 세트의 References/Source/Export/Review/Workflow를 명확히 하되, 현행 폴더를 지금 템플릿에 억지로 맞추지 않는다.

1. Unreal 에셋 경로를 먼저 안정화한다. ArtSource/FBX/Blend 경로는 첫 이동 배치에서 고정한다.
2. 원본 이동 배치에서는 Import Source 메타데이터, Blender 외부 텍스처/링크, 스크립트 상대 경로, 원본→중간본→최종본 의존성을 함께 갱신한다. 이전 v001이 최신본의 입력일 수 있으므로 버전 번호만 보고 정리하지 않는다.
3. `Content/Python`은 Unreal의 검색 경로를 유지한다. 현재 사용 스크립트는 기능별 모듈화를 별도 작업으로 고려하고, 임포트 경로 변경을 검증한다. 운영 경로 상수는 기존 스크립트부터 단계적으로 공통 설정으로 모은다.
4. `dev`는 전체 이동하지 않는다. 재사용 도구는 tools, 유지 제작 소스는 ArtSource, 유지 설명은 docs로 승격하고 나머지는 이력/실험으로 표시한다.
5. 과거 로그·감사 JSON·검증 스크린샷의 경로는 역사적 증거다. 일괄 치환하지 않고 이전/이후 경로 명세와 현재 CURRENT 문서에서 연결한다. 폐기된 파괴적 정리 스크립트는 새 경로로 바꿔 재사용하지 않는다.
6. Binaries/Intermediate/DerivedDataCache/Saved는 이 콘텐츠 재배치 범위에서 옮기지 않는다. 복구 자료가 포함된 Saved를 일괄 삭제하지 않는다. `tools/run-blender.ps1`의 위치와 실행 규칙도 유지한다.

## 실행 순서와 단계별 산출물

| 단계 | 작업과 산출물 | 다음 단계로 넘어가는 조건 |
|---|---|---|
| 0. 기준 고정 | 지하철 등 진행 중 변경과 조율, 저장된 기준 커밋/LFS 확보, 현재 패키지·참조·Import Source·Cook 대상·맵 목록 저장 | 다른 작업 변경과 재배치가 같은 바이너리를 덮어쓰지 않는 작업 구간 확보 |
| 1. 이동 명세 | 전 에셋을 자체/외부/제작입력/검토/엔진관리로 분류. `old_package,new_package,owner,reason,batch,referencers,source_files,path_consumers,rollback` 이동표 작성 | 모든 행에 이동 또는 유지 이유, 목적지 충돌 0, 승인 키트·원본 보호 |
| 2. 소규모 시험 | 특정 맵에서 쓰는 자체 소품 한 묶음 5–20개를 선정. 메시·재질·텍스처·소품 BP 이동과 참조자 저장 | 새 프로세스에서 메시/재질 정상, 이전 경로로 회귀 생성 없음, 재반입 경로 유지 |
| 3. 환경 자체 제작물 | Art/Environment/Resources의 자체 환경 세트를 작은 배치로 통합. 맵 파일은 아직 고정 | 세트별 참조 차이 검사, 지정 화면 비교, 제작 레시피 경로 수정 완료 |
| 4. 캐릭터·UI·공유물 | 캐릭터 구성품을 리그 계열별로, UI 묶음을 UI로 이동. 공용 재질/Input 등을 별도 배치 | Skeleton/AnimBP/몽타주/블렌드스페이스/Widget/Input 연결 검증 |
| 5. 핵심 기능·데이터 | Core/Interaction/Combat/Quests/Sequences 정리 | C++/설정 수정과 컴파일, 기능 검사. 같은 이름 데이터는 정체 확인 후 이동만 수행 |
| 6. 맵·스트리밍 | 플레이 맵은 관련 참조를 가장 많이 받으므로 마지막에 이동. StartIsland와 Stairwell은 하나의 배치 | 두 방향 스트리밍·위치/시선/속도·도착 충돌·지연/실패 처리 및 패키징 확인 |
| 7. 원본·도구 | ArtSource/dev/운영 스크립트 재분류, 현재 Workflow/CURRENT/AGENTS 경로 갱신 | 유지 소스 로딩·재반입·허용된 재현 경로 확인. 과거 증거 보존 |
| 8. 최종 정착 | 외부 팩 예외 기록, 필요한 별도 명칭 변경, Collection/즐겨찾기, 에셋 검사 규칙 | Cook/패키징·회귀 검증과 경로 정책 통과, 의도치 않은 Redirector/옛 활성 경로 없음 |

각 배치에서 경로 이동 외의 기하·재질·게임 로직 변경을 섞지 않는다. 자산 유형·맵 사용 관계에 따라 배치를 조절하며 파일 개수만으로 쪼개지 않는다. 배치별 원래 경로와 새 경로, 갱신된 참조자, 설정/코드/문서 변경을 같은 복구 단위로 기록한다. 미커밋 사용자 작업을 덮는 Git reset은 사용하지 않는다.

## 이동 방식 및 프로젝트 고유 수정 지점

- `.uasset/.umap`은 Content Browser 또는 Unreal AssetTools의 에셋 이동/이름 변경 기능으로 처리한다. 탐색기 이동·바이너리 문자열 치환은 사용하지 않는다. Migrate는 주로 프로젝트 간 이관 도구이므로 이번 동일 프로젝트 재배치의 기본 수단으로 쓰지 않는다.
- 이동 후 Redirector가 생긴다. 참조자를 저장하고 경로 문자열 소비자를 고친 다음 해당 배치의 Fix Up을 수행한다. 저장에 실패한 참조자가 있으면 Redirector를 강제로 지우지 않는다. 모든 Redirector가 영구 유지되는 구조도 피한다.
- World Partition/외부 액터/LevelInstance 맵인지 먼저 조사한다. 일반 에셋 이동을 보장하지 못하는 경우 엔진의 WorldPartitionRenameDuplicateBuilder 등 해당 맵 지원 경로로 처리한다. `__ExternalActors__`, `__ExternalObjects__`, `_GENERATED`를 사람이 보기 좋은 이름으로 직접 재배치하지 않는다. 필요한 Generated 콘텐츠 이동은 엔진 소유 관계를 확인한 별도 범위에서만 수행한다.
- `Config/DefaultEngine.ini`: 기본 GameMode/GameInstance, GameDefaultMap, EditorStartupMap.
- `Config/DefaultGame.ini`: MapsToCook 4개, 퀘스트 DirectoriesToAlwaysCook, AssetManager 검색/개별 자산 규칙.
- `Source/Constellation/QuestSubsystem.cpp`: 기본 QuestDatabase 문자열 경로. 관련 h 문서도 갱신.
- `Source/Constellation/SubwayTravelVolume.h`의 DestinationMap은 TSoftObjectPtr<UWorld>다. C++ 타입을 바꿀 필요 없이 저장된 두 맵의 인스턴스 값과 스트리밍 실행 결과를 검증한다. SubwayTravelSubsystem/테스트 및 저장 데이터에 남은 문자열도 검색한다.
- `tools/play-stairwell.ps1`, `tools/play-overgrown-hall.ps1`: 실행 맵 경로.
- 현재 Content/Python 반입·캡처·검증 레시피: 하드코딩 목적지를 변경해 옛 폴더를 재생성하지 않도록 한다. 이전 실험 스크립트 전체 재실행은 검증으로 쓰지 않는다.
- `ArtSource/Stairwell_Modular/Workflow/CURRENT.md`, `ArtSource/OvergrownHall/CURRENT.md`, `ArtSource/SubwayEntrance/CURRENT.md`, `ArtSource/Heroine_Tripo_Review/AnimationWorkflow/SKILL.md`와 이를 가리키는 AGENTS.md: 실행 단계별 현재 경로를 반영한다.

## 완료 판정

1. 이동 명세의 모든 현재 에셋이 목적지에 정확히 하나씩 존재한다. 의도치 않은 복제/누락/덮어쓰기 0개다.
2. 기존 하드·소프트 참조 그래프를 이전→이후 경로로 변환해 새 그래프와 대조한다. 기존부터 있던 누락과 이번에 생긴 누락을 구분하며 새 끊김은 0개여야 한다.
3. Config/C++/현재 제작 스크립트/저장된 Blueprint·데이터의 활성 옛 경로가 없다. 일반 문자열·이름 조합 로딩은 Asset Registry만으로 검증했다고 주장하지 않는다.
4. 영향받는 Blueprint/AnimBP를 컴파일하고 클래스/스켈레톤/입력/퀘스트/시퀀스 연결을 검사한다. 에셋 검증과 대표 맵 저장 재로드가 통과한다.
5. 최초 타이틀 진입, StartIsland, AbandonedSchool, 양방향 지하철 스트리밍, 주인공 주요 동작, 퀘스트 데이터 로딩을 확인한다. OvergrownHall과 Stairwell의 사용자 플레이 검토 영역은 현재 Workflow의 사람 검토 규칙을 존중한다.
6. 실제 패키징 대상에 대해 Cook/패키징 검증 및 패키징 실행 확인을 한다. 현재 패키징 목록에 없는 검토 맵을 이름만 보고 자동 포함하지 않는다.
7. 원본 이동 단계는 Blender 링크와 대표 재반입을 별도 검증한다. Unreal에서 화면이 정상이라는 사실만으로 제작 재현까지 통과했다고 하지 않는다.
8. Review/Developers가 프로덕션에서 불필요하게 참조되는지, Cook 규칙이 맞는지 검사한다. 폴더 이름/컬렉션만으로 EditorOnly나 Cook 제외가 되는 것으로 간주하지 않는다.

이 계획은 경로와 작업 구조의 개선이다. 파일을 옮기는 것 자체로 용량이나 프레임 성능이 좋아지는 것으로 보고하지 않는다. 정확한 이동 개수와 실행 시간은 1단계 전수 이동표와 2단계 시험 결과로 산정한다.

## 근거

- Epic 권장 명명 규칙: https://dev.epicgames.com/documentation/en-us/unreal-engine/recommended-asset-naming-conventions-in-unreal-engine-projects
- Epic Redirectors 및 Fixup: https://dev.epicgames.com/documentation/en-us/unreal-engine/asset-redirectors-in-unreal-engine
- Epic Working with Assets: https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-assets-in-unreal-engine
- Epic Collections: https://dev.epicgames.com/documentation/unreal-engine/filters-and-collections-in-unreal-engine?lang=en-US
- Epic World Partition Rename/Duplicate Builder: https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Editor/UnrealEd/UWorldPartitionRenameDuplicateBu-
- Epic Auto Reimport: https://dev.epicgames.com/documentation/unreal-engine/reimporting-assets-automatically-in-unreal-engine?lang=en-US
- Allar/Gamemakin Style Guide: https://github.com/Allar/ue5-style-guide — 외부 커뮤니티 실무 지침이며 Epic 강제 표준이 아니다. 프로젝트 전용 루트·소유 영역 분류를 참고하고 유형별 폴더 금지 등의 의견은 프로젝트에 맞게 조정한다.
