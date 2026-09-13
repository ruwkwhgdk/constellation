# Resource Cleanup and Develop Publication Plan

**Goal:** 미사용 리소스를 참조 분석으로 정리하고 작업 목적별 커밋을 develop에 게시한다.
**Architecture:** 모든 맵과 기능성 애셋, 설정/코드에서 지정한 리소스를 보존 루트로 삼아 hard/soft/management 의존성을 추적한다. 참조가 없는 시각 리소스만 백업 후 제거하며, 동적 참조가 불명확한 항목은 보존한다.
**Tech Stack:** Unreal 5.8 Asset Registry, Python, Git LFS.
**Spec:** 사용자의 현재 정리 및 Git push 요청.

## Constraints
- develop만 사용. 추가 브랜치나 worktree를 만들지 않는다.
- 이전 리소스 카탈로그는 삭제 판정에 사용하지 않는다. 간접 참조와 다른 게임 맵을 포함한다.
- 삭제 직전 파일을 dev의 로컬 복구 ZIP으로 보관한다.
- 원격 이력 덮어쓰기나 force push를 하지 않는다.

## Tasks
- [ ] Git 변경 목록, 맵, 설정/코드의 동적 로드 경로와 Asset Registry 의존성 조사.
- [ ] 삭제 후보 및 보존 사유 목록을 생성하고, 외부 참조가 없는 후보만 백업 후 삭제.
- [ ] 삭제 이후 참조 무결성, 변경 Blueprint 로드 및 컴파일 상태, 맵 로드 검사.
- [ ] 아트/게임플레이/레벨 통합/리소스 정리/문서 목적별 변경 목록과 커밋 구성.
- [ ] Git LFS 및 diff 검사, develop 원격 상태 확인 후 순차 커밋과 push.
- [ ] 원격 develop SHA와 로컬 HEAD 일치 확인 및 결과 보고.
