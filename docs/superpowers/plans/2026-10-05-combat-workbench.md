# Combat Workbench Implementation Plan
Goal: 승인된 인게임 조정 패널, 자원 상한, 프리셋 및 게임 재시작 흐름 구현.
Spec: ../specs/2026-10-05-combat-workbench-design.md
Architecture: GameInstance subsystem에 세션 설정/초안 검증/JSON을 두고, 캐릭터 초기화 전에 액터별 자산을 복제한다. Slate UI는 초안만 편집하고 적용 시 월드를 재시작한다.
Tech: UE5.8 C++, Slate, GAS, JSON.

## Constraints
1600×900 기본, 본문18, 작은 창 스크롤. 원본 자산/기존 카메라 및 이동값 보존.
현재 공유 체크아웃의 진행 중 변경을 보존한다. 별도 브랜치/커밋/프로세스 종료 없음.
User explicitly requested execution; proceed inline with resource-maxima subtask delegated per subagent-driven-development.

## Tasks
- [x] ResourceLimits: CombatAttributes/CombatAbilitySystem maxima 초기화·클램프·회복 수정. 250HP/60SP 및 invalid fallback 자동 검사.
- [x] Workbench model: PrepareActor 복제 및 설정필드 구축; ValidateValues 전체검증; ApplyValues 다음 실행 설정; Save/LoadPreset 엄격JSON.
- [x] Slate HUD: 상태카드, F1 pause, 탭/스크롤, 숫자·체크박스, 대상선택, 원복·적용·취소·저장·불러오기.
- [x] Integration: BeginPlay에서 복제→설정→ASC/AI초기화. 입력과 EndPlay cleanup 연결.
- [x] Verify: 전체Editor빌드 및 combat 회귀. UI 렌더 스크린샷 기본/패널 확인. 실제 플레이 smoke.

## Review focus
- 참조 공유/순환 Action 복제로 원본 격리.
- 잘못된 수치/관계/JSON에서 부분 적용 금지.
- 사망 상태 및 일시정지에서도 패널 조작/재시작.
- 작은 창에서도 고정 버튼 접근, 긴 진단 줄바꿈.
- 월드 재시작/대상 변경/게임 종료시 UObject·Slate 수명 정리.

## Test procedure
Run tools/test-combat.ps1 after full build; require every named test.
Add Workbench model regression for isolated action graph and rejected invalid values.
Run game with workbench screenshot flag; inspect captured PNG before final claim.

## Verification results
Final Editor build succeeded; all 34 CombatCore tests passed including malformed preset rejection. Actual game restart retained player HP175/SP80 and slime HP200. Render captures inspected at 1280x720, 1600x900 and 1920x1080. Final 1600x900 capture includes selected-tab status and separated HUD/footer.
