# 전투 개편 첫 구현 계획
> 실행: superpowers:executing-plans로 이 세션에서 수행한다. 사용자가 기획서대로 작업 시작을 승인했다.

**Goal:** 최신 전투 기준을 보존하고, 별도 시험장에서 GAS 공격·피해·사망·취소와 실제 종료를 기다리는 AI 태스크를 검증한다.
**Architecture:** 기존 런타임과 분리한 ConstellationCombat 플러그인. CombatRuntime은 데이터·GAS·판정·테스트용 캐릭터, CombatEditor는 시험 자산 생성만 담당한다.
**Tech Stack:** UE 5.8.0 CL 55116800, C++, GAS, 몽타주 Notify State, Unreal Python, Automation.
**Spec:** docs/2026-10-04-combat-ai-direction.md

## 범위와 제약
- 승인된 단계 0~1을 첫 실행 단위로 한다. 회피·콤보·궁극기·편집 화면 양산은 후속 단계다.
- 현재 develop 작업 폴더의 미커밋 캐릭터·들기·연출 자산을 보존한다. 별도 플러그인과 /Game/Constellation/Review/CombatCore에 격리한다.
- 기존 BP·맵·캐릭터·기본 게임모드를 바꾸지 않는다. 기존 공격 모션은 복제해서 시험용 알림만 추가한다.
- 싱글플레이 PC 시제품이며 네트워크 지원을 주장하지 않는다.
- 판정 시제품은 전방 구체 sweep. 최종 검 소켓 궤적·고급 취소 창·밸런스 검증은 이후다.

## 검토 초점
- 취소 뒤 늦은 알림이 도착해도 종료한 실행의 판정이 재개되지 않아야 한다.
- 다수 콜리전·복수 프레임에서도 같은 구간의 같은 대상은 한 번만 맞아야 한다.
- 유효하지 않은 모션·자원 부족·이미 사망한 대상은 비용·피해를 발생시키지 않아야 한다.
- 사망과 Ability 종료 이벤트 재진입에서 중복 종료·AI 대기 잔류가 없어야 한다.
- 시험 자산을 다시 생성해도 사용자 자산을 덮어쓰지 않아야 한다.

## Task 1 최신 현황과 기준
파일: tools/audit-combat.py, Saved/CombatAudit/20261004, docs/2026-10-04-combat-core-progress.md.
- [x] 기존 에디터 플러그인의 ExportBlueprintGraphs를 사용해 읽기 전용 스냅샷 생성.
- [x] 현재 회피 곡선과 BTT_Attack 종료 경로 확인.
- [x] 기존 들기 자동화 3개 성공 확인. 기존 전투 영상 기준선은 후속 과제로 명시.
인터페이스: inventory.json에 path, class, sha256, graph_file, nodes를 기록. 게임 자산 저장 없음.

## Task 2 GAS 공통 실행
파일: Plugins/ConstellationCombat/Source/CombatRuntime/{Public,Private}.
인터페이스: UCombatActionDefinition, UCombatAbilitySystem::TryStartAction/CancelAction/ApplyHit,
UCombatActionAbility, UCombatAttributes, UCombatHitWindow, FCombatHitLedger.
- [x] 먼저 CombatCoreTests.cpp에 구간 중복·잘못된 입력·피해·사망·취소 테스트 작성.
- [x] 빌드 실패로 아직 구현이 없음을 확인.
- [x] 실행 ID와 구간별 적중 기록 구현. Begin → Open → Claim → Close → End 계약.
- [x] GAS AttributeSet과 단일 피해 처리 구현. 체력 0 이하면 공격 취소.
- [x] 하나의 데이터 정의당 능력 Spec을 부여하고 몽타주 종료로 EndAbility 처리.
- [x] Notify State가 현재 실행에만 구간을 열고 닫도록 연결.
- [x] 빌드 및 Constellation.CombatCore 테스트를 실행해 결과 확인.

핵심 기대:
```cpp
Ledger.Begin();
Ledger.Open("Swing");
TestTrue("first hit", Ledger.Claim("Swing", Target));
TestFalse("duplicate", Ledger.Claim("Swing", Target));
Ledger.End();
TestFalse("after cancellation", Ledger.Claim("Swing", Target));
```

## Task 3 시험장과 AI 연결
파일: CombatLabCharacter.*, BTTask_CombatAction.*, CombatLabEditorLibrary.*, tools/setup-combat-lab.py, tools/test-combat.ps1.
- [x] 인스턴스별 BT 태스크가 ActionEnded를 기다리고 Abort에서 해당 공격만 취소하도록 구현.
- [x] 별도 시험 캐릭터에 GAS·입력·디버그 표시 연결. 공격·취소·체력·사망을 확인 가능하게 구성.
- [x] 원본 모션과 외형을 복제·참조하여 시험 데이터와 맵 생성. 기존 에셋 변경 금지.
- [x] commandlet 재로드와 몽타주 알림 확인, 엔진에서 실행 경로 검증.
- [x] 독립 코드 리뷰를 받고 주요 결함 수정 후 필요한 테스트만 재실행.

## 완료와 후속
- [x] docs/2026-10-04-combat-core-progress.md에 실제 검증·한계·사용법 기록.
- [x] 기술 검증과 사람의 체감 평가를 구분해 보고.
- 단계 2 이후는 이번 코어 결과를 기준으로 다음 실행 단위로 세분화한다.
