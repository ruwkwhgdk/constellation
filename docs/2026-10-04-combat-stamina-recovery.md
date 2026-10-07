# SP 고갈 후 공격 불가 수정

## 원인과 정책
선입력 예약 교착이 아니라 스태미나 회복 누락이다. 공격 비용은 차감했지만 SP를 돌려주는 경로가 없었다. 사용자가 SP=0을 확인했다.

전투 컴포넌트에 다음 시험용 기본 규칙을 적용한다.
- 공격 중에는 회복하지 않는다.
- 공격 종료 또는 취소 후 1초 대기한 다음 초당 20 회복한다.
- 새 공격을 시작하면 회복 대기를 다시 시작한다. 자원 부족으로 거절된 입력은 회복 대기를 연장하지 않는다.
- 상한은 기존 스태미나 속성의 100이다. 사망 후에는 회복하지 않는다.
- Combat 컴포넌트의 Stamina Recovery Per Second / Stamina Recovery Delay로 조정한다. 회복량 0은 회복 비활성이다.
- 이동·카메라 설정에는 변경이 없다.

## 검증
SP 고갈 → 예약된 후속 공격 거절 → 대기 → 회복 → 공격 재개 경로를 자동화하고, 공격 중·취소 후·사망 후 및 상한을 검사한다. 실제 게임에서는 LMB 입력과 기본 컴포넌트 틱으로 같은 경로를 확인한다.

검증 완료:
- 전체 Development Editor 빌드 성공. 에디터 종료 후 DLL 잠금 해소.
- tools/test-combat.ps1: 전투 자동 테스트 19/19 성공.
- 실제 게임 -CombatStaminaReview: passed=true, observed_exhaustion=true, executions=2, stamina=20.05. 첫 공격으로 SP 0에 도달하고 후속 공격이 거절된 뒤, 자연 회복으로 두 번째 공격이 실행됨을 확인했다.
- 읽기 전용 코드 검토에서 발견한 테스트 초기 SP 설정 시점 문제를 수정했다.

증거: Saved/Logs/Combat-build.log, Saved/Logs/Combat-tests.log, Saved/Logs/Combat-stamina-play.log, Saved/CombatAudit/20261004/stamina-review.json.

에디터를 다시 열어 기존 L_CombatCore 시험장에서 테스트하면 된다. 회복 설정은 기본 컴포넌트 값으로 적용되므로 시험장 재생성은 필요 없다.
