# 최종 플레이 레벨 인계

플레이 맵: `/Game/Environment/StairwellModular/Scene/Maps/L_Stairwell_PlayScale2`.

사용자가 공간 크기 해결을 확인한 2배 확장본이다. 문·난간·형광등의 크기는 유지했다. 문에 맞춘 추가 벽은 제거했다.

- 유지 소스·재생성 순서·검증 한계: [CURRENT.md](../../Workflow/CURRENT.md)
- 다음 제작에 적용할 절차: [SKILL.md](../../Workflow/SKILL.md)
- 정리 후 저장 맵 검사: [current_verification.json](current_verification.json)
- 검토 화면: [review.html](review.html) — 기존 캡처이며 이번 정리 후 렌더 갱신은 수행되지 않았다.

`tools/play-stairwell.ps1`은 이 레벨을 실행한다. 카메라 완충 설정은 저장 검증까지 완료했고 실제 플레이 체감 확인은 남아 있다. 문 런타임 상호작용과 전체 이동·성능 검증은 별도 작업이다.
