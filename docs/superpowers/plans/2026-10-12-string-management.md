# String Management v1 Implementation Plan

**Goal:** 기존 원본을 수정하지 않는 문자열 검색과 원본/사용처 탐색.
**Spec:** ../specs/2026-10-12-string-management-design.md
**Architecture:** ResourceTools editor module에 snapshot index, type-specific collectors, Slate tab, navigation 추가. SceneDirector editor에 Step.Id 기반 공개 브리지 추가.
**Execution:** 사용자의 구현 요청에 따라 현재 세션에서 순차 구현한다. 기존 미커밋 대사 기능과 실제 에셋을 사용해야 하므로 현재 checkout을 유지하며 기존 변경을 보존한다. 별도 worktree로 HEAD만 복제하면 승인된 현재 구조가 누락된다.

## Tasks
- [x] 실제 transient StringTable/DataTable/Director/Blueprint로 읽기 전용 수집과 참조 구분 테스트 작성, 실패 확인.
- [x] typed locator, 원본/사용처 수집, 게임별 C++ 참조 규칙, 점진적 검사와 coverage 구현.
- [x] 기존 편집기 탐색 및 SceneDirector Step.Id 탐색 구현.
- [x] 도킹 창/필터/두 종류 이동/미검사 목록/변경 후 재검사 구현.
- [x] editor build, automation tests, production inventory smoke, 변경 검토와 사용자 안내 작성.

## Review focus
- Direct value must never mask a broken row handle.
- Linked Blueprint row pins must not count as exact entry references.
- StringTable-linked cells must navigate to their true source, preserving the intermediate cell usage.
- Opening or scanning must not save or rewrite source assets.
- Deleted nodes, changed row keys, stale/partial scans must be explicit.

## Evidence ledger
- Baseline: existing modified and untracked files preserved. Test artifacts/logs go in Saved/TextManagementTests.
- Native implementation chosen; no content migration, no automatic save, no branch integration requested.

- RED: `Saved/TextManagementTests/red-test.log` (Sources); `review-red-test.log` (missing String Table and unset table speaker). Expected failures were observed before fixes.
- GREEN: `Saved/TextManagementTests/verified-build.log` — ConstellationEditor Win64 Development, UE 5.8, Result Succeeded.
- GREEN: `Saved/TextManagementTests/verified-test.log` — 7/7 Success: TextManagement DynamicBlueprint, InvalidReferences, ProductionSources, Sources, StringTableChain, WindowAndNavigation; SceneDirector GraphRoundtrip.
- Production smoke: six current source tables contributed 16/16/4/124/12/4 searchable text entries respectively. These are text entries, not row counts. DataTable full JSON and package dirty state remained equal before/after collection. BP_HUD and BP_RegionTrigger dynamic row references and unchanged dirty state passed.
- Read-only review completed, followed by re-review after fixes; no remaining blocking finding. Source collectors contain no save, Modify, or MarkPackageDirty calls.

## 사용 방법
1. 새 모듈을 사용하도록 Unreal Editor를 다시 열고 **도구(Tools) → Constellation 섹션 → 문자열 관리**를 선택한다.
2. 문구, 행·키, 에셋 경로 또는 화자를 검색한다. 공백은 AND 검색, 큰따옴표는 구문 검색이다.
3. 결과를 선택한 뒤 **원본 에디터 열기**로 실제 문구 원본을 연다. 테이블 행의 FText가 String Table을 참조하면 String Table 키가 원본이다. **이 작성 위치로 이동**은 중간 테이블/노드로 이동한다.
4. 오른쪽 사용처 버튼은 테이블 행, Blueprint 노드, Scene Director 이벤트의 Step.Id로 이동한다. 일반 에셋 속성은 기존 에디터를 열고 속성 경로를 안내한다.
5. 문구는 기존 에디터에서 수정한다. 원본 변경 감지 후에는 **다시 검사**해야 이동할 수 있다.

## 첫 버전의 범위와 제한
- /Game/Constellation 및 /Game/SceneDirector의 지원 에셋을 한 프레임에 하나씩 읽는다. 개별 에셋의 동기 로드 자체는 잠깐 UI를 멈출 수 있다.
- 확정 참조, 동적 참조, 패키지 후보, 연결 오류를 분리한다. 확정은 정적 연결의 증거이며 실제 실행의 증거는 아니다.
- 미검사·실패 목록을 제공한다. 맵/Level Blueprint/배치 액터, 동적으로 선택되는 테이블, RowHandle 구조체 핀 기본값은 전수 해석하지 않는다. C++는 현재 프로젝트의 알려진 조회 규칙만 지원한다.
- 취소한 검사는 부분 결과다. 사용처 0건은 미사용 판정이 아니다. 예제/Review 및 가려진 직접 값은 별도 포함 옵션이다.
- 복잡한 Blueprint 데이터 흐름, 임의 함수 내부의 키 생성, 런타임 실행 추적은 이번 버전에 포함하지 않는다.
- 자동화 검증은 NullRHI에서 수행했다. 창 생성과 실제 에디터 API 이동은 검증했으며 화면의 시각적 배치 및 전체 프로젝트 검사 시간은 별도 실사용 확인 대상이다.


## 2026-10-12 추가 구현: 분류 및 문구 편집
사용자 요청으로 첫 버전의 검색 전용 범위를 확장했다. 아래 내용이 위의 '편집은 기존 에디터에서 수행' 제한을 대체한다.

- 자동 분류: 실제 원본 경로에 따라 대사/화자/퀘스트/지역/UI/상호작용/기타를 제안한다. 분류 필터와 결과 목록의 분류 표시를 추가했다.
- 직접 분류: 상세 창에서 분류명을 입력해 저장하거나 자동 분류로 복원한다. 원본 위치의 UTF-8 해시를 키로 `Config/StringManagement.ini`에 저장한다. 동일 원본을 참조하는 결과는 분류를 공유한다. 원본 에셋을 이동/이름 변경한 경우 수동 분류를 다시 지정해야 한다.
- 문구 수정: 상세 창의 여러 줄 입력 → 문구 적용 → 적용된 원본 저장 순서. 적용은 Undo 가능한 에셋 변경이고, 저장은 디스크 저장이다. 저장에는 해당 에셋의 다른 미저장 변경도 포함된다. 입력 취소는 미적용 초안을 버린다.
- 지원: DataTable FText(직접 필드/중첩 구조체/배열), String Table 원문, 닫혀 있는 Scene Director의 직접 입력 대사/화자/선택지, Blueprint의 수정 가능한 단일 텍스트 입력 핀, 일반 에셋의 지원되는 FText 속성.
- String Table 참조는 실제 String Table 원문을 수정하며 참조를 일반 문자열로 바꾸지 않는다. 기존 FText namespace/key 및 String Table 개발자 메모를 보존한다.
- Blueprint CDO/위젯/컴포넌트 기본값, map/set 등 복잡한 경로, 가려진 직접 값 및 연결 오류는 원본 에디터로 안내한다. 열려 있는 Scene Director는 그래프 복사본과의 충돌을 막기 위해 해당 에디터에서 수정하도록 안내한다.
- 초안은 작성 시작 시점의 snapshot과 함께 보관한다. 외부에서 원문이 변경되면 적용을 거부한다. 입력 내용을 보관한 뒤 입력 취소로 최신 원문을 다시 불러온다.
- 검증: `Saved/TextManagementTests/edit-red-test.log`에서 기능 미구현 상태의 신규 테스트 실패 확인. `edit-build3.log` 빌드 성공. `edit-verified-test.log` TextManagement 9/9 성공. 분류 영속화/복원, 원문 수정, namespace/key 보존, 오래된 snapshot 거부, Undo, 공유 String Table 참조 및 메모 보존 검증. 기존 검색/이동 회귀 포함. 코드 리뷰 지적 2건 수정 후 재검토 완료.
- 검증 환경은 NullRHI 자동화이며, 전체 편집 화면의 시각적 배치와 모든 원본 종류의 수동 편집을 전수 검증한 것은 아니다.
