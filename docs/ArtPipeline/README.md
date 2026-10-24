# Art source separation

게임 저장소는 실행에 필요한 Content, Source, Plugins, Config와 빌드·실행·코드 테스트 도구를 유지한다. 제작 원본은 형제 폴더 `../constellation-art-source`에 보존한다. Art 저장소는 `git@github.com:ruwkwhgdk/constellation-art-source.git`, 브랜치는 `develop`이다. 게임 실행과 쿠킹에 Art 체크아웃을 필수로 연결하지 않는다.

## 2026-10-24 로컬 분리

- 제작 원본: Art 저장소의 `ArtSource/`.
- 과거 작업 파일, 검수 자료, 에디터 제작 스크립트, 일회성 도구: Art 저장소의 `ProjectArchive/Constellation/<기존 상대 경로>`.
- 파일별 경로와 SHA-256, 관련 채팅 검토 근거: Art 저장소의 `Migration/2026-10-24/`.
- 정확한 보존 위치는 `copy-plan.json`, 복사 검증은 `copy-verification.jsonl`, 게임 쪽 사본 제거 기록은 `source-removal.jsonl`을 확인한다. 계획 목록만으로 제거 완료를 판단하지 않는다.
- 기존 Art 파일과 다른 게임 버전은 `Migration/2026-10-24/PreservedGameVersions/`에 별도 보존했다. SchoolLocker README, SchoolOpening README와 Photo_Memory_Draft.png가 해당한다. 기존 Art 파일을 자동으로 덮어쓰지 않았다.

Art 저장소의 제작 원본·재검증 자료·분리 기록은 `develop`의 `dc5743db83f648b1fd5f6b3fd64753c1fac47e0d`에 게시했다. `art-source-lock.json`의 `art_commit`도 이 커밋을 가리키며 기존 임포트 원본 42개의 해시는 유지한다. `Migration/2026-10-24/publication-manifest.json`은 게시 대상과 로컬에만 보존한 로그·생성 캐시를 구분한다. 게임 실행 자산의 재임포트는 수행하지 않았다.

## 재임포트·재검증

필요한 원본만 Art 저장소의 실제 보존 경로에서 게임의 무시된 ArtSource 경로 또는 별도 검증 체크아웃으로 복원한다. 복원 시 manifest의 SHA-256을 확인한다. Unreal의 Reimport Source File은 선택한 파일 경로로 명시적으로 지정한다. 자동 재임포트나 폴더 감시는 켜지 않는다.

과거 보고서·스크립트에는 기존 절대 경로가 남아 있다. `Migration/2026-10-24/LOCATION-AND-RESTORE.md`를 읽고 해당 실행의 입력과 경로를 조정한다. 과거 스크립트를 일괄 실행하거나 예전 결과를 새 검증 결과로 사용하지 않는다. 임포트 변경 시 메시·재질·애니메이션을 검수한 뒤 Content 변경과 잠금 정보를 함께 커밋한다.

검증 프로젝트의 Content/Plugins/Source 연결은 Windows 정션일 수 있다. 이를 실제 복사본으로 계산하거나 내부 파일을 정리하지 않는다. Intermediate, Plugins의 Intermediate, 빌드 작업 파일, 자동 저장과 게임 저장 데이터는 그대로 보호한다. Git/LFS의 기존 이력도 삭제하지 않는다.
