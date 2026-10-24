# Art source separation

게임 저장소는 실행에 필요한 Content, Source, Plugins, Config와 빌드·실행·코드 테스트 도구를 유지한다. 제작 원본은 형제 폴더 `../constellation-art-source`에 보존한다. Art 저장소는 `git@github.com:ruwkwhgdk/constellation-art-source.git`, 브랜치는 `develop`이다. 게임 실행과 쿠킹에 Art 체크아웃을 필수로 연결하지 않는다.

## 2026-10-24 로컬 분리

- 제작 원본: Art 저장소의 `ArtSource/`.
- 과거 작업 파일, 검수 자료, 에디터 제작 스크립트, 일회성 도구: Art 저장소의 `ProjectArchive/Constellation/<기존 상대 경로>`.
- 파일별 경로와 SHA-256, 관련 채팅 검토 근거: Art 저장소의 `Migration/2026-10-24/`.
- 정확한 보존 위치는 `copy-plan.json`, 복사 검증은 `copy-verification.jsonl`, 게임 쪽 사본 제거 기록은 `source-removal.jsonl`을 확인한다. 계획 목록만으로 제거 완료를 판단하지 않는다.
- 기존 Art 파일과 다른 게임 버전은 `Migration/2026-10-24/PreservedGameVersions/`에 별도 보존했다. SchoolLocker README, SchoolOpening README와 Photo_Memory_Draft.png가 해당한다. 기존 Art 파일을 자동으로 덮어쓰지 않았다.

Art 저장소의 제작 원본·재검증 자료·분리 기록은 `develop`의 `dc5743db83f648b1fd5f6b3fd64753c1fac47e0d`에 게시했다. 이 커밋은 정리 전 복원 기준이며, 현재 참조는 아래 후속 정리 커밋을 따른다. 기존 임포트 원본 42개의 해시는 유지한다. `Migration/2026-10-24/publication-manifest.json`은 게시 대상과 로컬에만 보존한 로그·생성 캐시를 구분한다. 게임 실행 자산의 재임포트는 수행하지 않았다.

## 2026-10-24 검토 프레임 정리

이 정리의 Art 게시 커밋은 `07786fc8b7e74a9cec2649ffe2904dff6c2f73a7`이며, 현재 참조는 아래 외부 작업공간 기록 보관 커밋을 따른다. 폰 모션 7,925개, 검 획득 1,502개, 보관된 게임 검토 프레임 12,377개의 추적 파일을 삭제했다. 편집 원본, 최종 영상, 보고서 연결 이미지와 대표 프레임은 유지한다.

`Migration/2026-10-24-DiskCleanup/plan.json`과 `deleted.jsonl`에 파일별 경로·해시·삭제 근거를 기록했다. `verification.json`은 정리 직후의 검사 기록이다. 과거 이관 manifest는 당시 보존 목록이므로 현재 체크아웃에 모든 프레임이 남아 있다는 뜻은 아니다. 삭제된 추적 프레임이 필요하면 정리 전 커밋 `dc5743db83f648b1fd5f6b3fd64753c1fac47e0d`에서 필요한 경로만 복원한다.

로컬 전용 셰이더 디버그 출력 정리까지 포함해 22,743개 파일, 12,550,543,101바이트를 제거했다. 게임의 추적 자산과 임포트 원본 해시는 변경하지 않았으며 재임포트도 수행하지 않았다. Git/LFS 이력은 유지한다.

## 외부 아트 작업공간 정리 기록 보관

이 기록의 Art 게시 커밋은 `200bee11eaa27c1918ff9c5494574b842a9e0da4`이며, 현재 잠금 정보는 아래 중복 정리 기록의 후속 커밋을 따른다. `Migration/2026-10-24-ExternalArtCleanup/`에 외부 `Constellation_ArtWorkspace/Cleanup_20261024`의 정리·재생성 비교 기록과 복원 도구를 보관했다. 파일별 원본/보관본 해시는 `publication-manifest.json`, 사용 방법은 `README.txt`를 따른다.

외부 작업공간에서 백업 9개·동일 사본 3개·재생성 중간본 36개를 제거한 기록이다. 편집 원본 모델 자체를 Art 저장소에 추가한 것은 아니며, 기록만으로 외부 원본 전체를 복원할 수는 없다. 복원 도구는 원래 외부 작업공간의 `Cleanup_20261024`에서 사용한다. 보관본에는 저장소에서 잘못 실행되는 것을 거부하는 위치 검사가 있다. 기존 폴더가 있으면 후속 기록을 덮어쓰지 않도록 먼저 비교한다.

게임 실행 자산과 기존 임포트 원본 42개의 해시는 유지했으며, 재임포트는 수행하지 않았다.

## 외부 아트 중복 사본 정리 기록 보관

현재 `art-source-lock.json`은 Art 저장소 `develop`의 `e396c6bc33d6e14d5d2792ea5027b86e3c90443a`를 참조한다. `Migration/2026-10-24-ExternalArtDuplicates/`에 중복 20쌍의 판단, 사본 6개 삭제 기록(250,969,813바이트), 보존 경로와 복원 방법을 보관했다. 재검증 기준·별도 제작 산출물인 14쌍은 보존했으며 보호 파일 54개와 남은 쌍의 해시를 확인했다.

`publication-manifest.json`은 외부 기록과 보관본의 해시를 연결한다. `snapshot/deleted.jsonl`의 보존본 SHA-256을 확인하고 누락된 원래 경로에 복사하는 절차는 `README.txt`를 따른다. 실제 보존본은 외부 `Constellation_ArtWorkspace`에 있으며 기록만으로 모델 전체를 복원할 수는 없다. `snapshot/cleanup.py.txt`는 실행하지 않는 과거 삭제 스크립트 사본이다. 이번 게시에서 게임 자산과 기존 임포트 목록·해시는 변경하지 않았다.

## 재임포트·재검증

필요한 원본만 Art 저장소의 실제 보존 경로에서 게임의 무시된 ArtSource 경로 또는 별도 검증 체크아웃으로 복원한다. 복원 시 manifest의 SHA-256을 확인한다. Unreal의 Reimport Source File은 선택한 파일 경로로 명시적으로 지정한다. 자동 재임포트나 폴더 감시는 켜지 않는다.

과거 보고서·스크립트에는 기존 절대 경로가 남아 있다. `Migration/2026-10-24/LOCATION-AND-RESTORE.md`를 읽고 해당 실행의 입력과 경로를 조정한다. 과거 스크립트를 일괄 실행하거나 예전 결과를 새 검증 결과로 사용하지 않는다. 임포트 변경 시 메시·재질·애니메이션을 검수한 뒤 Content 변경과 잠금 정보를 함께 커밋한다.

검증 프로젝트의 Content/Plugins/Source 연결은 Windows 정션일 수 있다. 이를 실제 복사본으로 계산하거나 내부 파일을 정리하지 않는다. Intermediate, Plugins의 Intermediate, 빌드 작업 파일, 자동 저장과 게임 저장 데이터는 그대로 보호한다. Git/LFS의 기존 이력도 삭제하지 않는다.
