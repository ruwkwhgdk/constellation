# Star Thread 튜토리얼 토스트

기존 WBP_Tutorial의 네 호출(이동 WASD / 점프 Space / 공격 좌클릭 / 변신 Z)을 유지하면서 네이티브 표시를 교체했다.

- 우측 중앙, 카드 640×192 Slate 단위, 간격 16. 여러 카드가 있으면 중앙 기준 세로 정렬.
- 입력 모드, 커서, 일시정지, 이동/시점 제한을 변경하지 않는다. 포커스와 마우스 히트 테스트를 받지 않는다.
- 기본 페이드 인 0.25초 → 표시 8초 → 페이드 아웃 0.35초. 실제 동작 완료가 먼저 감지되면 즉시 페이드 아웃.
- 이동: 입력과 실제 이동 동시 확인. 점프: 상승 중 실제 점프 상태 진입. 공격: 새 공격 몽타주와 공격 상태 또는 활성 네이티브 전투 실행. 변신: 변신 상태 전환과 실제 빙의 변경 확인.
- 기존 학교 오프닝 종료 후 지연 표시 유지.
- 종료 콜백의 강제 점프/공격/변신 호출 제거. 각 토스트가 스스로 제거되어 HUD의 최신 토스트 참조를 잘못 지우지 않는다.
- 레퍼런스의 Tab 조작 안내는 현재 대응 기능이 없어 표시하지 않는다. FooterText는 실제 기능 연결 시 설정 가능.

## 리소스
원본 투명 PNG: T_Tutorial_StarThreadAtlas.png (1536×1024).
상단 패널 UV: (88,112)–(1448,502). 하단 별 장식: (695,554)–(840,956).
엔진: /Game/Constellation/UI/Dialogue/T_Tutorial_StarThreadAtlas. UI / NoMipmaps / sRGB / NeverStream.
문구와 키캡은 이미지에 굽지 않고 Slate 텍스트로 표시한다.

이미지 제작: OpenAI ImageGen, 사용자 제공 Star Thread 시안 기반 새 UI 아틀라스. 요청 요지: 투명 배경, 글자 없는 어두운 남색 벽화 패널, 조용한 좌측 본문 공간, 오른쪽 청색 광물/성운 질감, 분리된 수직 금빛 세 별 장식. 기존 파일을 잘라 만든 이미지가 아닌 새 생성물.

## 재현
1. tools/import-tutorial-toast.py: 원본 텍스처 가져오기.
2. ConstellationEditor Development 빌드.
3. tools/apply-tutorial-toast.py: 감사된 4개 Blueprint의 종료 연결만 교체. 최초 수정 직전 백업은 Saved/TutorialToast.
4. Automation: Constellation.Audit.TutorialPrompt, Constellation.SchoolOpening.TutorialRetry.
5. tools/verify-tutorial-toast-pie.py: 별도 UserDir에서 Entry PIE로 실행. 저장 없이 4개 스택, 입력 상태 유지, 완료/시간 종료 검증.

Saved/TutorialToast의 build.log, tests.log, pie-result.json 및 스크린샷이 검증 기록이다. 전체 학교 진행을 처음부터 끝까지 플레이한 검증과는 구분한다.

## 검증 결과 (2026-10-12)
- ConstellationEditor Win64 Development 빌드 성공.
- NonblockingLifecycle, ActionObservation, SchoolOpening.TutorialRetry: 3/3 통과.
- 별도 Entry 맵 PIE: 4개 동시 표시, 커서/일시정지 상태 유지, 점프 완료 알림 시 해당 카드만 제거, 나머지 시간 만료 검증 통과.
- 실제 엔진 점프, 입력+이동량, 네이티브 전투 몽타주 실행의 완료 감지 자동화 통과. 변신과 레거시 공격은 기존 Blueprint 실행 순서 감사 및 코드 연결 확인; 전체 학교 플레이 경로의 직접 실행 검증은 미실시.
- 최종 화면: preview-pie.png. 테스트용 빈 Entry 맵 배경이다.
