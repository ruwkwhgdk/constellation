# 시퀀스에서 편집 가능한 연출 그래프로 전환

사용자가 승인한 목적: 원본 보존, 블렌딩과 이동 리스트 확장, 기획자 작업을 연출 툴로 점진 이전. 현재 작업 공간에서 직접 실행한다.

## 설계
- 기존 애니메이션 노드: 기존 시간 맞춤 기본값 유지. 수동 속도/오프셋/블렌드 인·아웃/가중치/역재생, 명시적 중첩 허용 추가.
- 기존 캐릭터·카메라 이동: 경유점 목록(초, 위치, Euler 회전, 스케일, 보간), 이동 중 애니메이션 별도 재생 옵션. 변환된 키의 축별 보간·탄젠트 보존.
- 에디터 변환 API 및 콘텐츠 브라우저에서 선택한 시퀀스를 새 이벤트로 가져오기. 원본 및 현재 이벤트는 덮어쓰지 않는다.
- 원본 Spawnable 템플릿, NPC·카메라 키, 이동/애니메이션/카메라 컷, 병렬/대기 구조 생성. 모든 지원 조건을 사전 검사하고 실패하면 결과를 게시하지 않는다.
- 현재 실행기의 30 fps 노드 경계 및 키 표현을 벗어나는 타이밍, Control Rig/Event/중첩/외부 Possessable 등은 이유를 반환한다. 근사 변환하지 않는다. 원본 재생 노드를 대안으로 유지한다.
- 변환 보고서 및 원본 참조 보존. 원본/생성 채널의 중간 시간 값과 애니메이션 매핑·블렌드, 원본 불변, 실패 원자성, 저장/재열기 검증.

## 작업
- [x] 경유점·블렌딩 데이터와 컴파일, 회귀 테스트.
- [x] 원본 분석 및 그래프 변환, 보존/거부 테스트.
- [x] 가져오기 UI와 예제, 사용 문서.
- [x] Editor/Shipping 빌드, 전체 자동 테스트, 실제 미리보기 검증.

## 검증 결과
- 전체 Editor 빌드 및 자동화 51개 성공: `Saved/Logs/SceneDirector-build.log`, `Saved/Logs/SceneDirector-tests.log`.
- Shipping 빌드: `Saved/Logs/SceneDirector-import-shipping.log`.
- 실제 원본/변환 겹침 애니메이션 포즈를 5개 시간에서 비교, 원본 불변·수정 독립성·저장/언로드/재열기 검증.
- 6000 Hz/nonzero start와 30fps 사이의 큐빅/자동/가중 탄젠트 중간값, 450도 회전, 키 범위 밖 상수 유지, 고정 속도 double 정밀도 검증.
- Keep State/가장 가까운 섹션 평가/미지원 트랙/표현 불가능한 키 시간은 명시적으로 거부.
- 편집기 실렌더링 및 원본 비교 시간 유지 확인: `Saved/Logs/SceneDirector-import-visual.log`, `Saved/SceneDirector-import-editor.png`.
- 예제 저장 성공: `Saved/Logs/SceneDirector-import-example.log`, `/Game/SceneDirector/Examples/L_ImportedPerformance`.
- 코드 검토 지적(탄젠트 재계산, 합성 종료 키, AnimBP 실행 모드, 루트 모션, 종료 상태, 정밀도)을 수정하고 회귀 검증 추가.
- 다른 작업의 전투 검증 프로세스 DLL 잠금 중 임시 빌드 시도가 있었으나, 종료 후 기본 DLL 이름으로 전체 빌드·검증 완료. 기본 UnrealEditor.modules 유지.
- Cook/Stage/패키지 실행은 별도 검증하지 않음.
