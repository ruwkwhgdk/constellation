# 전투 입력 예약과 후속 공격 연결

## 구현 범위
프로젝트 기본 이동·카메라 설정을 유지한 채 전투 시험장에 단일 슬롯 입력 예약을 추가했다. 기존 게임 캐릭터에 최종 이식하기 전의 검증용 구현이다.

- 공격 중 지정된 몽타주 시간 구간에서 LMB를 누르면 다음 공격 하나를 예약한다.
- 기본 입력 구간은 0.50~0.65초이며 실제 몽타주 재생 위치를 기준으로 판단한다.
- 현재 공격이 자연 종료되면 다음 틱에 예약된 공격을 실행한다. 0.65초에 현재 모션을 잘라 전환하는 기능은 아직 없다.
- 같은 구간의 반복 입력은 한 슬롯을 공유한다. 자연 종료 직후 전환 대기 중의 추가 클릭도 예약을 유지한다.
- 실행 시 스태미나·쿨다운을 다시 검사한다. 예약했더라도 자원이 부족하면 후속 공격은 실행되지 않는다.
- 취소·사망·소유 해제·다른 실행으로 교체되면 오래된 예약이 실행되지 않는다.

## 기획자가 조정하는 데이터
콘텐츠 브라우저의 /Game/Constellation/Review/CombatCore 에서 CombatActionDefinition 데이터 에셋을 연다.

| 항목 | 의미 |
|---|---|
| Next Action | 이어질 공격 데이터. 비우면 해당 공격에서 종료 |
| Input Window Start / End | 다음 입력을 받는 몽타주 시간(초) |
| Montage / Play Rate | 공격 모션과 재생 배속 |
| Damage / Stamina Cost / Cooldown | 피해량·스태미나 비용·재사용 대기 |
| Reach / Radius | 타격 탐색 거리·반경 |

시험장 기본 연결은 DA_PlayerSlash → DA_PlayerFollowUp02 → DA_PlayerFollowUp03이다. 각 타격 비용 10, 피해 20이다. 2·3타는 1타 모션을 복제한 기계적 연결 검증용으로, 완성된 3타 애니메이션이 아니다. 공격 중 전진, 모션 블렌딩, 다른 방향의 후속 베기는 후속 제작 범위다.

setup-combat-lab.py는 최초 초기화에만 기본 연결을 채운다. 이후 기획자가 Next Action을 변경하거나 비워도 재실행으로 덮어쓰지 않는다. 이동·카메라 설정은 기존 정책대로 프로젝트 원본과 동기화한다.

## 시험 방법
tools/play-combat-lab.ps1로 시험장을 실행한다. WASD 이동, 마우스 시점, Tab 잠금, LMB 공격, RMB 취소, R 초기화. 1타와 2타가 시작된 뒤 각각 약 0.5초 시점에 LMB를 눌러 후속타를 예약한다. 화면의 Follow-up input / buffered 상태로 입력 수락 여부를 확인한다.

## 검증 기록
- Development Editor 전체 빌드 성공.
- 전투 자동화 18/18 성공. 입력 구간 전후, 중복 입력, 자연 종료, 전환 순간 추가 입력, 취소·사망·실행 교체, 자원 부족·쿨다운, 잘못된 입력 구간을 포함한다.
- 전환 순간 추가 입력 회귀는 수정 전 실패를 확인한 뒤 수정했다. 읽기 전용 코드 리뷰에서 후속 주요 결함 없음.
- 실제 LMB 입력 주입: executions=3, stamina=70, enemy_hp=40, buffered=false, passed=true.
- 저장본을 다시 열어 3개 공격 연결·스켈레톤·입력 구간과 원본 조작 설정을 비교했다. walk_speed=500, camera_lag_speed=10, yaw_scale=2.5, pitch_scale=-2.5, matched=true.
- 실제 플레이 스크린샷에서 3타 진행 및 HUD 상태를 확인했다. 이 검증은 손으로 플레이한 체감 평가를 대신하지 않는다.

증거: Saved/Logs/Combat-build.log, Combat-tests.log, Combat-input-handoff-red.log, Combat-combo-verify.log, Combat-combo-play.log 및 Saved/CombatAudit/20261004/combo-review.json, lab-verification.json, combat-combo.png.

실제 게임 로그에는 엔진 NiagaraToolsets Python 초기화의 NiagaraToolset_Info 속성 오류가 별도로 발생했다. 전투 검증 시나리오는 정상 완료했으며 이 엔진 플러그인 오류는 이번 작업에서 수정하지 않았다.

verify-combat-lab.py의 3개 공격 기대값은 기본 시험장 검사용이다. 기획자가 체인을 의도적으로 변경한 뒤에는 해당 검증 기대값도 함께 조정한다.

## 다음 단계
기본 교전의 남은 회피·무적 구간·피격 반응을 같은 실행/취소 규칙에 연결하고, 이후 몬스터 판단 규칙과 기획자용 제작·검증 도구로 확장한다. 현재 설정값으로 실제 손 조작의 체감 품질을 승인받았다는 의미는 아니다.



SP 회복 누락 수정 완료: [회복 규칙과 검증 결과](2026-10-04-combat-stamina-recovery.md). 공격 종료 후 1초 대기, 초당 20 회복. 자동 테스트 19개 및 실제 게임 공격 재개 검증 통과.

후속 구현: [피격 중단과 경직](2026-10-04-combat-hit-reaction.md). 애니메이션 제작은 [별도 AI 전달 목록](2026-10-04-combat-animation-backlog.md)을 따른다.
