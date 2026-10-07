# 전투 공통 코어 1차 구현 결과

작성일: 2026-10-04
기준: [전투·몬스터 AI 개편 기획](2026-10-04-combat-ai-direction.md), [첫 구현 계획](superpowers/plans/2026-10-04-combat-core.md)

> 최신 조작 설정: [프로젝트 기본값 동기화](2026-10-04-combat-project-controls.md).

> 후속 업데이트: [이동·카메라·잠금 구현 결과](2026-10-04-combat-movement-progress.md). 현재 조작과 최신 검증은 이 문서를 참고한다.

## 이번에 만들어진 것

소울라이크 기본 전투와 액션 RPG형 스킬·궁극기를 같은 실행 규칙으로 확장하기 위한 첫 코어를 만들었다. 현재는 기본 공격 하나와 정지형 몬스터의 공격을 시험하는 기술 검증 단계다. 기존 플레이 캐릭터·몬스터 BP를 교체한 상태가 아니다.

새 플러그인 `Plugins/ConstellationCombat`에 런타임과 에디터 보조 기능을 분리했고, 시험 자산은 `/Game/Constellation/Review/CombatCore`에 생성했다. 현재 작업 폴더의 미커밋 캐릭터·들기·연출 작업을 보존하기 위해 별도 경로에 추가했다.

| 항목 | 실제 동작 |
|---|---|
| 공격 정의 | Data Asset에서 몽타주, 피해, 스태미나 비용, 재사용 시간, 재생 속도, 판정 거리·반경 편집 |
| 실행 | 플레이어와 몬스터 모두 GAS의 동일한 Ability 실행 경로 사용 |
| 판정 구간 | 몽타주의 Combat Hit Window Notify State가 판정을 열고 닫음 |
| 중복 방지 | 실행 ID·구간 ID·대상별로 한 번만 피해 적용 |
| 취소 | 몽타주 중단·능력 취소·사망·캐릭터 제거 시 판정과 실행 종료 |
| 오래된 알림 | 같은 몽타주를 재실행해도 이전 몽타주 인스턴스의 알림은 무시 |
| 피해·사망 | Health Attribute를 한 경로에서 차감, 체력 0에서 공격 취소·사망 이벤트 한 번 |
| AI 태스크 | 실제 ActionEnded를 기다림. 고정 Delay로 공격 완료를 추정하지 않음 |
| AI 중단 | 태스크가 맡은 실행만 취소하고 완료 이벤트 구독 해제 |
| 데이터 검사 | 잘못된 모션·비용·판정 구간·스켈레톤, 자원 부족, 사망 상태에서 실행 거부 |

피해 처리 후 기존 `OnTakeAnyDamage` 리스너에 알림을 보내지만 `ApplyDamage`를 다시 호출하지 않는다. 검증 캐릭터의 TakeDamage도 같은 Attribute 경로로 전달한다.

## 기획자가 지금 시험하는 방법

1. UE 에디터의 콘텐츠 브라우저에서 `/Game/Constellation/Review/CombatCore/L_CombatCore`를 열고 Play한다.
2. 또는 프로젝트 루트 PowerShell에서 `./tools/play-combat-lab.ps1`을 실행한다. 로컬 UE 5.8 에디터 빌드가 필요하다.
3. WASD는 카메라 기준 이동(후속 수정 반영), 마우스는 시점, Tab은 잠금/해제, 왼쪽 마우스는 공격, 오른쪽 마우스는 강제 취소, R은 시험장 초기화다. 화면에 HP·SP·실행 상태가 표시된다.
4. 슬라임 가까이 접근하면 슬라임이 공격한다. 쌍방 피해와 취소 후 판정 잔류 여부를 관찰한다.
5. SP 회복은 아직 없으므로 반복 시험 시 R로 초기화한다. 죽은 캐릭터는 현재 메시를 숨긴다.

조정할 자산:

- `DA_PlayerSlash`: 피해 20, 비용 10, 재사용 시간 0.2초.
- `DA_EnemyStrike`: 피해 15, 비용 0, 재사용 시간 1.2초.
- `AM_DA_PlayerSlash`: 복제한 여주인공 공격. 판정 구간 0.35~0.50초.
- `AM_DA_EnemyStrike`: 복제한 슬라임 공격. 임시 판정 구간은 모션 길이의 40~55%. 이 타이밍은 체감 평가와 시각적 접촉 검토를 아직 거치지 않았다.

Data Asset을 열어 수치를 바꾸고, 몽타주 에디터에서 Combat Hit Window 길이를 바꾸면 된다. 한 몽타주에 여러 타격을 넣을 때는 구간마다 서로 다른 WindowId를 쓴다. 자산 우클릭의 데이터 검증으로 잘못된 정의를 확인할 수 있다. 이 단계의 판정은 캐릭터 정면 구체 sweep이며 실제 검 궤적을 따라가지 않는다.

`tools/setup-combat-lab.py`는 기존 시험 자산을 재사용한다. 사용자 편집 수치나 Notify를 덮어쓰는 초기화 도구가 아니다. 빈 몬스터 메시 복구, 최초 생성 시 잘못된 90도 기울기 복구, 시험장 조명·GameMode 분리와 PlayerStart 확보만 보정한다. 원본 전투 모션에는 저장하지 않는다.

## 검증 결과와 증거

엔진: UE 5.8.0, CL 55116800. Windows Development Editor.

| 검증 | 결과 | 증거 |
|---|---|---|
| 에디터 전체 빌드 | 성공 | `Saved/Logs/Combat-build.log` |
| 신규 전투 자동화 | 10/10 성공 | `Saved/Logs/Combat-tests.log` |
| 기존 들기 자동화 | 3/3 성공 | `Saved/Logs/Combat-carry-baseline.log` |
| 시험 자산 재로드 | 두 캐릭터의 메시·액션·스켈레톤·직립 배치와 GameMode 일치 | `Saved/CombatAudit/20261004/lab-verification.json` |
| 실제 게임 실행 | 공격·피해·종료 통과 | `Saved/CombatAudit/20261004/play-review.json` |
| 원본 전투 자산 보존 | 감사 대상 41개, 해시 변경 0개 | `Saved/CombatAudit/20261004/source-preservation.json` |
| 생성 스크립트 재실행 | 기존 5개 자산 재사용 | `Saved/CombatAudit/20261004/lab-setup.json` |
| 독립 코드 리뷰 | 발견한 취소 API·비용 콜백 재진입·공격 교체 문제 수정 | 각 회귀 테스트와 최종 리뷰 |

실제 플레이 자동 검증에서는 플레이어 공격 1회로 적 HP 100→80, 적 공격으로 플레이어 HP 100→70, 플레이어 SP 100→90, 최종 공격 비활성 상태를 확인했다. 화면 캡처는 `Saved/CombatAudit/20261004/combat-core.png`다. 이는 기능 검증이며 전투의 재미·모션 품질에 대한 사용자 승인으로 간주하지 않는다.

자동화 테스트 10개:

1. HitLedger — 구간·대상별 중복, 종료 후 적중 차단.
2. DamageAndDeath — 음수·비정상 피해 거부, 체력 하한과 사망 한 번.
3. InvalidAction — 잘못된 정의 실패와 비용 보존.
4. MontageLifecycle — 실제 GAS 몽타주 시작, 비용·적중·취소·늦은 알림·사망.
5. CostCooldownAndValidation — 자원 부족, 재사용 시간, 중복 구간 검사.
6. NaturalMontageCompletion — 실제 몽타주 완료 시 성공 이벤트 한 번.
7. ReentrantCostCancellation — 스태미나 변경 콜백에서 즉시 취소해도 충돌·상태 잔류 없음.
8. AutomaticWindowsAndOcclusion — 실제 Notify로 한 번 적중, 벽 너머 피해 차단.
9. ReentrantReplacement — 취소 콜백에서 다른 공격이 시작되어도 원래 공격의 성공으로 오인하지 않음.
10. BehaviorTreeAbortAndDestroy — 실제 트리의 공격 대기·중단·재시작과 대기 중 Pawn 파괴 시 종료.

재실행:

```powershell
./tools/test-combat.ps1
# 이미 최신 빌드를 완료했다면
./tools/test-combat.ps1 -SkipBuild
```

스크립트는 프로세스 종료 코드만 믿지 않고 10개 테스트의 개별 성공을 확인한다. 시간 초과 시 자신이 시작한 테스트 프로세스만 종료한다. 테스트 로그가 일부만 생성되어도 실패로 보고한다. 다른 UE 실행이 DLL을 사용 중이면 빌드가 실패할 수 있으므로 사용 중인 에디터는 사용자가 저장 후 닫고 재실행한다.

초기 구현의 실패를 재현한 뒤 고쳤다. 대표 증거는 `Combat-tests-red3.log`(취소 잔류), `Combat-reentrant-red.log`(비용 콜백 중 취소), `Combat-replacement-red2.log`(교체 공격 오인)다. 최종 성공 근거는 위 표의 최신 로그다.

## 최신 프로젝트 감사

`tools/audit-combat.py`로 기존 에디터의 Blueprint 그래프 내보내기를 사용해 읽기 전용 감사 자료를 다시 만들었다. `Saved/CombatAudit/20261004/inventory.json`과 `graphs`에 경로·클래스·해시·그래프를 보관했다.

- BP_Player_Heroine: 324개 노드. DodgeTrack의 curve=None 재확인.
- BTT_Attack: 7개 노드. 정상 경로가 DoAttack → Delay(AttackDelay) → FinishExecute다. 실패 종료 경로는 현재 자산에 이미 있다.
- Ac_Dodge 기본 cooldown=5.0.
- 이 기존 시스템의 결함을 이번 패치에서 직접 변경하지 않았다. 향후 이식 시 원본과 새 코어를 비교할 수 있도록 보존했다.

## 아직 남은 작업

- 기존 플레이 캐릭터로 이식, 무기 소켓 궤적 판정, 피격 반응·경직·타격 정지·카메라·효과음.
- 입력 버퍼·콤보 연결·회피 무적/취소 창·스태미나 회복. 무제한 강제 취소는 시험 기능이며 최종 전투 규칙이 아니다.
- 추적·거리 유지·공격 선택·패턴·보스 페이즈와 다수 몬스터 전투.
- 액션 RPG형 스킬·궁극기, 자원/쿨다운 UI.
- 기획자용 통합 작성 화면, 자연어→변경안→검증→시험→되돌리기 흐름.
- 패키징, 네트워크, 성능·장시간 플레이, 사람의 조작감 평가. 현재 Health·Stamina 최대치는 각각 100인 시제품이다.
- 기존 전투의 영상 기준선과 최종 모션 접촉/체감 검토는 미실시. 시험장 조명·외형·이동 애니메이션은 완성도 승인 대상이 아니다.

다음 구현 단위는 기획서의 단계 2로, **플레이어 기본 공격·입력 버퍼·회피를 시험장에 연결하고 피격 반응을 추가**하는 것이다. 그 후 기존 캐릭터에 점진적으로 이식한다. 기획자가 AI로 모든 전투를 혼자 제작하는 최종 목적까지는 위 후속 기능과 작성 도구가 필요하다.
