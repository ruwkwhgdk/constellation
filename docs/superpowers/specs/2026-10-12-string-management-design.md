# Constellation 문자열 검색·사용처 이동 도구 설계

작성: 2026-10-12 (Asia/Seoul). 상태: 분석을 근거로 작성한 설계 제안. 제품 코드는 구현하지 않았다.

## 목적과 범위

사용자는 현재 String Data의 관리 위치와 참조 방식을 분석하고, 기존 구조를 최대한 유지하면서 통합 검색과 사용처 이동이 가능한 도구의 구체적 설계를 요청했다.

권장안은 Unreal Editor의 `도구 > Constellation > 문자열 관리` 도킹 탭이다. 기존 DataTable, String Table, DataAsset, Blueprint를 원본으로 유지하고 재생성 가능한 검색 인덱스만 추가한다. 첫 버전은 검색, 참조 판별, 원본/사용처 이동을 완성하고 편집은 기존 에디터에서 수행한다. 이름 변경, 대량 이관, 자동 중복 병합, 번역 서버, CSV 재가져오기는 포함하지 않는다.

성공 기준: 사용자가 문구를 검색해 실제 수정 원본과 소비 위치를 구분하고, 테이블 행/키 또는 대사 노드로 이동할 수 있다. 확인하지 못한 참조를 '미사용'으로 오인시키지 않는다.

## 조사 방법과 한계

- 현재 작업 트리의 C++/Python/Blueprint 에셋을 조사했다. 미커밋 변경도 현재 상태로 포함한다.
- UE 5.8 Python commandlet으로 에셋 목록, DataTable JSON, String Table 키, Quest FText 참조를 읽었다. 에셋 저장 API는 호출하지 않았다.
- Blueprint는 기존 `UResourceRecoveryLibrary::ExportBlueprintGraphs`를 이용해 BP_HUD와 BP_RegionTrigger의 노드/핀을 읽었다.
- 감사 산출물: `Saved/StringManagementAudit/inventory.json`, `focused.json`, `BP_HUD.txt`, `BP_RegionTrigger.txt`, 실행 로그. Saved 산출물은 임시 증거이며 배포 원본이 아니다.
- 일부 캐릭터/애니메이션 의존 에셋의 로드 오류로 commandlet은 비정상 종료 코드를 남겼다. JSON이 생성된 항목과 개별 완료 로그만 근거로 사용한다. 프로젝트 전체 검사 통과를 의미하지 않는다.
- 모든 맵, Level Blueprint, World Partition 외부 액터, 동적 Blueprint 호출 인자는 전수 조사하지 않았다. Asset Registry referencer는 패키지 단위 후보이며 행 단위 증거가 아니다.
- 첫 inventory의 Scene Director 목록은 이름에 DIALOGUE가 포함된 종료 노드도 포함한다. 해당 목록 길이는 대사 수로 사용하지 않는다. 추가 조사는 Python에 EventGraphs 속성이 노출되지 않아 완료되지 않았다. 하위 EventGraphs 전수 조사 여부나 대사 총량을 이 보고서로 확정하지 않는다. 설계된 C++ 수집기는 해당 UPROPERTY에 직접 접근한다.

## 확인된 관리 위치

| 종류 | 에셋 | 실제 내용/참조 |
|---|---|---|
| UserDefinedStruct | `/Game/Constellation/Gameplay/Sequences/Data/ST_StringData` | String Table이 아니라 시퀀스·지역 DataTable의 행 구조체 |
| DataTable | 같은 폴더의 `DT_SequenceStringData` | 50행. Description FText에 NSLOCTEXT identity 포함 |
| DataTable | 같은 폴더의 `DT_RegionStringData` | 6행. ST_StringData 구조 |
| DataTable | 같은 폴더의 `DT_SpeakerData` | 4행. FDirectorSpeakerRow, DisplayName FText |
| String Table | `/Game/Constellation/Gameplay/Quests/Data/ST_QuestString` | 16키. Namespace ST_QuestString |
| String Table | `/Game/Constellation/Gameplay/Interaction/Data/ST_InteractionActions` | 16키. Namespace InteractionPrompt |
| String Table | 같은 폴더의 `ST_CarryMessages` | 4키. Namespace Carry |
| DataAsset | `/Game/SceneDirector/School/*`, `/Game/SceneDirector/Statue/*` | 대사/화자/선택지 직접 FText와 선택적 행 참조 |
| DataAsset | `/Game/Constellation/Gameplay/Quests/Data/DA_MainQuest_ExitSchool` | Title, Description[], Objective[]에 ST_QuestString 참조 확인 |

테이블 6개에는 합계 96개의 행/키가 있다. 프로젝트 전체 문자열 수가 아니며 직접 입력, 복수 텍스트 필드, UI/C++ 문구는 별도다. DT_RichTextStyles는 글꼴/스타일 테이블이므로 문구 목록으로 세지 않는다. 이름 접두어가 아닌 실제 UClass와 FProperty 타입으로 분류한다.

## 확인된 참조 경로

### 기존 시퀀스·HUD

`DT_SequenceStringData -> BP_HUD / Get String Element -> GetDataTableRow -> Description`

BP_HUD의 GetDataTableRow는 테이블은 고정이지만 RowName 핀이 연결되어 있다. 문자열을 Name으로 변환하는 노드도 있다. 조회 노드 위치는 확정할 수 있어도 함수 호출 인자까지 추적하지 않고 특정 행 사용으로 단정하면 안 된다. L_Title도 패키지 참조 후보지만 이번 조사에서는 내부 노드를 열지 않았다.

### 지역명

`DT_RegionStringData -> BP_RegionTrigger / Get String Element -> RegionName -> 표시 위젯`

여기도 RowName 핀이 연결되어 있으므로 동적 테이블 조회로 분류한다. 각 배치 액터가 어느 지역 행을 지정하는지는 맵 인스턴스 검사 범위에 속한다.

### 능력 획득 설명

`DT_SequenceStringData -> DA_AbilityAcquisition.Descriptions -> UAbilityAcquisitionArt::Description(Slot) -> UAbilityAcquisitionWidget`

`Source/Constellation/AbilityAcquisitionArt.cpp`에는 Jump/Combat/Metamorphosis에 해당하는 `AbandonedSchool_Star_Object_*` 세 행이 고정되어 있다. 일반 RowHandle 스캔으로 발견되지 않으므로 전용 규칙으로 수집한다. 실제 설정된 Descriptions 테이블과 결합할 때 행 단위 확정 참조가 된다.

### 퀘스트

`ST_QuestString -> DA_MainQuest_ExitSchool의 FText -> UQuestSubsystem의 FQuestDisplayInfo -> Quest UI`

Title 및 Description/Objective 각 7개 항목에서 실제 String Table ID/Key를 확인했다. 엔딩 관련 FText와 ProgressSteps.Description도 수집 대상으로 포함한다. 화면용 FQuestDisplayInfo는 복사된 실행 결과이므로 작성 원본으로 중복 수집하지 않는다.

### 상호작용·운반

- `ST_InteractionActions -> BP_Player_Heroine의 ActionStrings -> UInteractionPromptComponent::GetActionText`. enum 이름을 키로 조회한다.
- `ST_CarryMessages -> DT_CarrySettings.Messages -> UCarryComponent::GetCarryMessage`. TooHeavy, PickupUnreachable, PlaceBlocked, ThrowBlocked 호출이 C++에 존재한다.
- 설정 객체가 가리키는 실제 테이블과 알려진 키 규칙을 결합해 수집한다. enum 전체가 모든 배치에서 실제 실행된다는 뜻은 아니다.

### Scene Director

현재 소스의 `SceneDirectorText.cpp` 규칙:

1. DataTable과 RowName이 모두 미설정이면 직접 FText 사용.
2. 둘 중 하나만 설정되거나 행/텍스트 필드가 유효하지 않으면 오류. 직접 문구로 자동 fallback하지 않음.
3. 행에서 Description 또는 Description_ 접두 FText를 우선 선택. 없으면 정확히 한 개의 FText일 때만 사용.
4. 반환은 기존 FText 자체이므로 identity/history를 보존.

본문은 DialogueRow, 선택지는 TextRow, 선택 불가 사유는 DisabledReasonRow가 우선이다. 화자는 SpeakerSource에 따라 None/Direct/Table을 구분하며 Table은 FDirectorSpeakerRow.DisplayName을 사용한다. 컴파일된 Cues도 RowHandle을 보존하고 재생 시 ResolveDialogue/ResolveText를 호출한다.

현재 디스크에서 읽은 S0에는 행 연결이 비어 있는 직접 입력 항목이 확인됐다. `tools/link-s0-string-data.py`가 존재하지만 `Saved/S0StringTable`에는 실행 완료 보고서 linked.json이 없었고, 연결 완료를 전제할 수 없다. 관리 도구가 이 스크립트를 자동 실행해서는 안 된다.

## 대안 비교

| 대안 | 이점 | 비용 | 판단 |
|---|---|---|---|
| 기존 저장소 위에 Slate 검색 탭 | 구조 유지, 기존 에디터 활용, 노드 이동 확장 가능 | 참조 종류별 수집 로직 필요 | 권장 |
| Editor Utility Widget/Python 중심 | 표 형태 시제품은 빠름 | 정밀 FText/Blueprint 분석·Toolkit 이동에 C++ 브리지 필요 | 임시 조사용 |
| 전체 문구를 새 DB/String Table로 이관 | 저장 형식 통일 | 직접 대사/동적 조회/현지화 ID 마이그레이션 위험 | 현재 범위에 부적합 |

## 사용자 화면

상단: 검색어, 유형(DataTable/String Table/직접 입력), 용도(대사/선택지/지역/퀘스트/상호작용), 폴더, 새로고침, 검색 범위 표시.

왼쪽: 원본 저장소 트리. 가운데: 원문, 행/키, 원본 에셋, 종류, 확정 사용처 수. 오른쪽: 원문 전체, 현재 언어 표시값, 실제 수정 원본, 참조 경로와 사용처 목록.

하단: 검사한 에셋 수/실패/미검사/마지막 갱신 시각. 실패 로그 열기.

- 한글 문구, Key/RowName, 에셋명, 화자/이벤트명 검색을 지원한다. 공백 구분 검색어는 AND, 명시적 따옴표 검색은 연속 구문으로 한다.
- 원문과 현재 언어 표시값을 구분하고 모두 검색 가능하게 한다. 검색을 위해 얻은 FString으로 원본 FText를 덮어쓰지 않는다.
- 같은 문구라도 원본 locator가 다르면 별도 결과다. 동일한 NS/Key를 가진 복사본도 작성 위치별로 유지한다.
- 연결된 문구 아래에는 사용처를 표시한다. direct 필드가 행 참조에 가려져 있으면 '현재 표시에는 사용하지 않는 직접 값'으로 표시하고 기본 검색에서는 숨기되 필터로 볼 수 있다.
- 검색 결과 더블클릭은 실제 수정 원본을 연다. 사용처 더블클릭은 소비 노드를 연다. 두 행동을 하나의 모호한 '열기'로 합치지 않는다.
- 진단 필터: 연결 오류 / 직접 입력 / 동적 참조 / 미검사. '사용처 미발견'은 '미사용 확정'이 아니다.

예: '폐교 탈출' 검색 -> ST_QuestString/MQ1_ExitSchool_QuestName -> 사용처 DA_MainQuest_ExitSchool.Title -> 각각 키 편집기/Quest 속성으로 이동.
예: S0의 직접 대사 검색 -> DA_S0_Opening의 이벤트/Step.Id/DialogueText -> Scene Director에서 해당 노드 선택.
예: 특정 지역명 검색 -> 원본 지역 행으로 이동, BP_RegionTrigger의 동적 조회 노드는 후보 영역에서 표시.

## 인덱스와 데이터 모델

인덱스는 UObject 원본을 소유·복제하는 새 문구 DB가 아니다. 메모리에 검색용 snapshot을 보관하며 원본 수정/삭제/이름 변경 시 폐기·재수집한다. 1차 버전은 디스크 캐시 없이 시작한다.

`FTextSourceLocator`:

- Kind: DataTableCell / StringTableEntry / AssetText / BlueprintPinText
- AssetPath: FSoftObjectPath
- RowName(FName), StringKey(FString), FieldPath: 필요 유형에 따라 저장
- SceneDirector 작성 위치는 RootAssetPath, EventObjectPath, StepId(FGuid), ChoiceKey(FName), FieldName으로 저장
- Blueprint는 BlueprintPath, GraphGuid 또는 그래프 경로, NodeGuid, PinId/PinName을 저장

`FTextEntry`: Locator, 원문 snapshot, 표시값 snapshot, TextIdentity, 분류, 검사 generation.
`FTextUsage`: 원본 Locator, 소비 Locator, 참조 종류, 유효성, 증거 설명.
`FTextScanCoverage`: 검사 루트/대상 수/완료 수/실패 목록/미지원 유형/맵 검사 여부.

FName을 쓰는 DataTable 행과 대소문자를 구분할 수 있는 String Table 키를 동일한 정규화 규칙으로 합치지 않는다. locator 해석 시 배열 인덱스와 필드 이름이 아직 유효한지 검사한다. 순서가 바뀌면 최신 속성 경로를 다시 계산한다. 오래된 인덱스로 잘못된 항목에 이동하지 않는다.

DataTable의 FText 자체가 String Table을 참조하면 `StringTableEntry -> DataTableCell -> 소비 위치` 연결을 보존한다. 테이블 셀을 원문 복사본으로 잘못 취급하지 않는다.

## 수집 및 참조 정확도

초기 검색 범위는 `/Game/Constellation`, `/Game/SceneDirector`. Examples/Review는 토글로 구분하고 범위를 항상 표시한다. 엔진/외부 팩은 명시적 확장 시만 검사한다.

1. Asset Registry로 대상 UClass를 발견한다. hard/soft referencer는 후보 축소에만 사용한다.
2. DataTable의 struct/array/map/set 내 FText와 RowHandle을 리플렉션으로 수집한다. 오브젝트 참조를 무제한 재귀하지 않고 각 등록 수집기의 소유 범위만 방문한다.
3. String Table의 실제 ID, namespace, key, source와 FTextInspector::GetTableIdAndKey를 사용한다.
4. Scene Director의 Steps와 재귀 EventGraphs를 방문한다. Cues/생성된 Sequence/preview 객체는 원본 집계에서 제외한다. 순환/중복 방문을 방지한다.
5. Quest, AbilityAcquisition, Interaction, Carry는 작은 전용 수집기로 기존 조회 의미를 반영한다.
6. Blueprint는 소유 그래프의 텍스트 핀, row-handle 기본값, GetDataTableRow의 테이블/행 핀, String Table 조회 호출을 수집한다. 끊긴 입력 핀의 상수만 정적 확정한다. 연결된 입력 핀의 무시되는 default 값은 증거로 쓰지 않는다.
7. Blueprint CDO, component template, WidgetTree의 작성 FText도 제한된 소유 범위에서 수집한다. 상속 기본값과 인스턴스 override를 구분해 실제 작성 위치로 안내한다.

정확도는 두 축으로 저장한다:

- 대상 해상도: ExactEntry / KnownTableDynamicKey / PackageCandidate / Unresolved.
- 상태: ActiveField / ShadowedField / Broken / Unscanned. 'ActiveField'는 현재 설정에서 유효한 필드라는 뜻이며 실행 도달 가능성까지 증명하지 않는다.

UI는 '확정 2곳 · 동적 조회 1곳 · 미검사 에셋 3개'처럼 표시한다. 동적 키를 임의로 추정해 각 행에 참조 수를 더하지 않는다. C++ 문자열 검색만으로 모든 런타임 참조를 발견했다고 주장하지 않는다.

## 이동 구현

| 대상 | 동작 | 처리할 예외 |
|---|---|---|
| DataTable | UAssetEditorSubsystem으로 열고 FDataTableEditorUtils::SelectRow 호출 | 행 삭제/필터로 숨김/다중 텍스트 열: 실패 알림과 필드 경로 표시 |
| String Table | 열려 있는 IStringTableEditor를 확인하고 RefreshStringTableEditor(Key) | 지원 editor인지 확인 후 호출, 엔진 private 헤더 사용 금지 |
| Quest 등 DataAsset | 기존 에디터를 열고 소유 객체 및 속성 경로 제공 | 표준 toolkit이 세부 배열 선택을 지원하지 않으면 '에셋 열기 + 경로 복사'로 명확히 표시 |
| Blueprint | Blueprint/그래프/NodeGuid를 다시 찾아 FKismetEditorUtilities::BringKismetToFocusAttention 계열로 이동 | 노드 재구성/삭제 시 재검사 안내, 임의 이름 유사 매칭 금지 |
| Scene Director | 공개 탐색 브리지로 Root/Event/Step/Choice/Field 전달, 이벤트 선택 후 노드 선택·JumpToNode | Step 삭제, event 이동, preview 실행 상태 |
| C++ 규칙 사용처 | 실제 파일/심볼로 소스 에디터 이동 | 소스 에디터 미설정이면 경로와 심볼 복사 |
| 맵 액터 | 열린 월드에서는 actor GUID/소유 객체 경로로 선택 | 다른 맵으로 조용히 전환하지 않음. 표준 저장 확인 절차를 따르는 명시적 '맵 열기' |

SceneDirectorGraph::Load는 매번 Node->CreateNewGuid를 호출한다. 따라서 그래프 NodeGuid를 영구 locator로 쓰지 않는다. FDirectorStep.Id로 현재 그래프 노드를 찾는다. Choice는 배열 위치보다 Choice.Key를 사용한다.

현재 Toolkit의 SelectEvent와 GraphEditor는 private이다. 리소스 도구가 private 헤더에 의존하지 않도록 `SceneDirectorEditor/Public/SceneDirectorNavigation.h`에 공개 브리지 하나를 추가한다. 제안 계약:

`bool OpenDirectorTextLocation(USceneDirectorAsset* Root, const FSoftObjectPath& EventPath, FGuid StepId, FName ChoiceKey, FName FieldName, FText& OutError)`

브리지는 기존 열린 toolkit을 재사용한다. 다른 이벤트로 이동할 때 기존 SelectEvent 흐름을 재사용해 Graph->Sync와 preview 종료를 일관되게 처리한다. 탐색 때문에 새 asset을 만들거나 자동 저장하지 않는다. Details의 세부 선택지 필드 강조가 불가능하면 최소한 노드 선택과 ChoiceKey/필드 안내를 보장한다.

## 코드 배치와 의존성

기존 `ConstellationResourceTools` Editor 모듈 아래 `TextManagement/` 폴더를 추가한다.

- TextManagementTypes.h: locator, entry, usage, coverage.
- TextManagementIndex.h/.cpp: 수집 큐, invalidation, 검색 snapshot, 역참조.
- TextSourceCollectors.h/.cpp: DataTable, String Table, 직접 FText.
- TextUsageCollectors.h/.cpp: SceneDirector/Quest/게임별 규칙.
- BlueprintTextCollector.h/.cpp: 그래프 핀, CDO, WidgetTree 검사.
- TextManagementNavigation.h/.cpp: 원본과 소비 위치 이동.
- STextManagementPanel.h/.cpp: 검색/필터/목록/세부/오류 UI.
- Tests/TextManagementTests.cpp: 정확도, 이동, 갱신 회귀 검사.

현재 ResourceRecoveryLibrary.cpp에 있는 `IMPLEMENT_MODULE(FDefaultModuleImpl, ConstellationResourceTools)`는 별도 ConstellationResourceToolsModule.cpp의 실제 모듈 클래스로 옮겨 탭/메뉴 lifecycle을 등록한다. 기존 복구 함수의 동작은 변경하지 않는다.

Build.cs에는 실제 include에 필요한 Slate, ToolMenus, PropertyEditor, ContentBrowser, Kismet, StringTableEditor, SceneDirectorEditor 의존성을 추가한다. SceneDirectorEditor -> ResourceTools 역의존성은 만들지 않는다. .uplugin에는 사용하는 SceneDirector 플러그인 의존성을 명시한다. 런타임 모듈에 editor dependency를 넣지 않는다.

SceneDirectorToolkit.h/.cpp에는 공개 브리지가 호출할 좁은 탐색 메서드만 추가한다. 기존 대사 resolver, 테이블 구조, 키, 컴파일 산출물 형식은 유지한다. 향후 resolver 선택 규칙이 바뀌면 수집기와의 parity test로 차이를 검출한다.

## 갱신·성능·안전

- 검색 타이핑은 인덱스만 조회한다. 150ms debounce를 초기값으로 둔다.
- asset load와 UObject reflection은 game thread에서 작은 batch로 처리하고 진행률/취소를 제공한다. worker에는 문자열 snapshot만 넘긴다.
- 테이블부터 결과를 제공하고 무거운 소비 에셋은 점진 수집한다. 이번 감사처럼 하나의 대사 에셋이 캐릭터 의존성을 대량 로드할 수 있으므로 전체 동기 로드를 피한다.
- 자산 변경/추가/삭제/rename, DataTable 변경, 객체 property 변경, Undo/Redo, Blueprint compile/reinstance 후 해당 asset과 역참조 결과를 무효화한다.
- 열린 에디터의 미저장 메모리 값을 우선하며 UI에 '미저장'을 표시한다. commandlet/디스크 snapshot과 혼동하지 않는다.
- 로드 실패는 이전 결과를 최신처럼 남기지 않고 '실패/오래된 결과'로 표시한다. 한 에셋 오류가 전체 검색을 중단시키지 않는다.
- 현재 열린 월드만 기본 검사한다. 전체 맵/Level Blueprint/외부 actor 검사는 후속 범위로 표시한다. 검색창을 여는 것만으로 맵을 로드하지 않는다.
- 인덱싱에 Modify, MarkPackageDirty, SavePackage, FillDataTableFromJSON을 사용하지 않는다. 에디터 open 자체의 기존 post-load 동작과 도구의 쓰기를 구분해 검증한다.

## 구현 단계와 인수 기준

1. 원본 검색: 6개 테이블의 96행/키와 직접 FText를 종류별로 표시한다. prefix가 ST_라는 이유로 구조체를 String Table로 오분류하지 않는다. 검색 중 기존 asset 파일 해시와 dirty 상태가 변하지 않는다.
2. 확정 참조: Quest의 15개 Title/Description/Objective 필드 참조, SceneDirector RowHandle/direct 우선순위, 능력 3행, Carry/Interaction 규칙을 검증한다. 같은 문구/같은 NS-Key라도 다른 작성 위치는 합치지 않는다.
3. Blueprint 및 이동: BP_HUD/BP_RegionTrigger는 동적 행 조회로 표시한다. DataTable 행, String Table 키, Blueprint 노드, SceneDirector 이벤트/Step로 이동한다. 그래프 재생성·재정렬 후에도 Step 이동이 유지된다.
4. 최신성/오류: 원본 문구 수정/Undo, 행 삭제, asset rename, Blueprint 재컴파일, 검색 중 취소, 한 asset load 실패, 미저장 변경을 검증한다. 정확도·coverage 상태가 항상 결과와 함께 갱신된다.

검증용 데이터는 transient 또는 별도 test fixture를 사용한다. 실제 50행 테이블을 테스트로 변경·저장하지 않는다. 필수 회귀 사례: 참조가 깨졌지만 direct 필드에는 문자열이 남아 있는 경우, 두 FText 열이 있어 resolver가 거부하는 행, String Table을 참조하는 DataTable 셀, 동일 문구의 서로 다른 두 노드, 삭제된 선택지, 미검사 맵이 있는 상태의 참조 0건.

두 번째 버전에서만 통합 화면의 단일 문구 편집을 검토한다. 그때도 기존 원본을 transaction으로 수정하고 identity 유지/undo/저장 전 diff를 검증하며, 별도 복사 DB를 만들지 않는다.

## 참고 근거

- Source/Constellation/InteractionPromptComponent.cpp: GetActionText
- Source/Constellation/CarryComponent.cpp: GetCarryMessage
- Source/Constellation/AbilityAcquisitionArt.cpp: Description
- Source/Constellation/QuestDefinition.h, QuestSubsystem.cpp
- Plugins/ConstellationSceneDirector/Source/SceneDirectorRuntime/Private/SceneDirectorText.cpp, SceneDirectorSpeaker.cpp, SceneDirectorPlayer.cpp
- Plugins/ConstellationSceneDirector/Source/SceneDirectorEditor/Private/SceneDirectorGraph.cpp, SceneDirectorToolkit.cpp
- 로컬 UE 5.8: DataTableEditorUtils.h, IStringTableEditor.h, KismetStringTableLibrary.h
- Epic FTextInspector: https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Core/FTextInspector/GetTableIdAndKey
- Epic DataTableEditorUtils: https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Editor/UnrealEd/FDataTableEditorUtils
