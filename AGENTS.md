# Blender automation

For command-line Blender work in this project, invoke `tools/run-blender.ps1`
with the original Blender arguments instead of launching `blender.exe` directly.
This checks Windows profile lookup before Blender can create thumbnail caches.

Blender 5.2.1's thumbnail code does not check failure of
`SHGetSpecialFolderPathW(CSIDL_PROFILE)`. The Codex sandbox account on this machine
fails that call and Blender can create random Unicode directories containing
`.thumbnails` in its working directory. Setting HOME, USERPROFILE or XDG_CACHE_HOME
does not repair this Windows code path.

If the launcher reports profile lookup failure, use the tool's normal approval
mechanism to request an appropriate normal-user execution context for that specific
Blender job. Do not bypass the guard, change sandbox account permissions, or disable
the sandbox globally. Do not stop an existing interactive Blender session.

Diagnostic details and a regression check: `docs/blender-thumbnail-folders.md`.

# Character animation workflow

## 3D 캐릭터 제작 환경 및 검사 원칙

Project Constellation의 3D 캐릭터 모델링 작업에서는 아래 지침을 항상 따른다.

### 프로젝트 용도
- 등신대 비율의 서브컬쳐 오픈월드 액션 RPG용 캐릭터를 제작한다.
- Blender에서 모델을 제작·수정하고 언리얼 엔진 5.8에서 사용한다.
- 캐릭터의 원화 특징, 얼굴 인상, 신체 비율과 실루엣을 유지한다.
- 변형 품질은 실제 사용하는 달리기·공격·회피·점프·착지 등의 동작으로 확인한다.

### 로컬 실행 환경
- Blender 실행 파일:
  `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- 확인된 버전: Blender 5.2.1 LTS.
- PATH 등록에 의존하지 않고 전체 실행 경로를 사용한다.
- 명령줄 실행은 위의 Blender automation 규칙에 따라 반드시 `tools/run-blender.ps1`을 통한다. 전체 실행 경로 사용 지침은 `blender.exe` 직접 실행이나 보호 런처 우회를 허용하지 않는다.
- 실행 파일이 없거나 버전이 달라졌으면 현재 환경을 다시 확인한다.

### 사용할 스킬
- 캐릭터 모델의 검사·수정에는 `lida-avatar-workflow` 스킬을 사용한다.
- 설치 위치:
  `C:\Users\User\.codex\skills\lida-avatar-workflow`
- 검사 스크립트:
  `C:\Users\User\.codex\skills\lida-avatar-workflow\scripts\lida_model_tools.py`
- 현재 작업에 필요한 참고 문서만 읽는다.
- 스킬의 예시 본 수·텍스처 크기·영향 본 수를 프로젝트 규격으로 자동 적용하지 않는다.

### 검사 및 수정 절차
1. 사용자가 지정한 저장된 .blend를 입력으로 사용한다. 파일을 임의로 선택하지 않는다.
2. 파일에서 메쉬·아마추어·관련 데이터를 확인하고 이름을 추측하지 않는다.
3. 검사는 별도 Blender 백그라운드 프로세스에서 수행하며,
   `--factory-startup --disable-autoexec` 옵션을 사용한다.
4. 수정 전 `audit`와 `snapshot`으로 현재 상태를 기록한다.
5. 변경할 부위, 유지할 데이터, 완료 조건을 명확히 한다.
6. 검사만 요청받았다면 모델을 수정하지 않는다.
7. 수정 요청 시 원본을 보존하고 별도 후보 .blend로 저장한다.
8. 수정 후와 저장·재열기 후에 검사하고, `compare`로 의도하지 않은 변경을 확인한다.
9. 결과와 비교 자료는 현재 프로젝트의 별도 검사 폴더에 실행별로 저장한다.
   기존 결과를 덮어쓰거나 과거 결과를 이번 실행 결과로 보고하지 않는다.

### 판단 기준
- 형태·토폴로지·뼈 위치·웨이트·법선·재질 문제를 구분하여 진단한다.
- 경계 에지, 0–1 범위 밖 UV, 변화가 없는 셰이프 키 등은
  의도된 구조일 수 있으므로 검사 수치만으로 자동 수정하지 않는다.
- `normalize-copy`는 웨이트 합계 수정이 필요한 경우에만 사용한다.
  자연스러운 변형이나 올바른 뼈 배정까지 보장한다고 판단하지 않는다.
- `compare`는 기록된 데이터의 완전 일치 여부를 확인하는 도구다.
  의도된 변경은 허용하고, 고정하기로 한 항목의 변경을 별도로 검토한다.
- UV·셰이프 키·재질 할당·스켈레톤 호환성을 보호한다.
  이를 변경해야 한다면 이유와 후속 영향을 설명한다.
- 폴리곤 수, LOD, 영향 본 수, 텍스처 및 재질 예산은
  목표 기기와 프로젝트 요구사항에 맞춰 결정한다.

### 검수 및 보고
- 수정 전후를 동일한 카메라·조명·자세로 비교한다.
- 기본 자세뿐 아니라 동작의 중간·최대 변형·복귀 상태를 확인한다.
- 검수 이미지는 실제 저장 모델에서 생성한다.
- 데이터 검사 통과를 외형·동작·게임 성능의 합격으로 간주하지 않는다.
- Blender 검사 완료, 외형·동작 확인 완료,
  언리얼 5.8 확인 완료, 미검증 항목을 구분하여 한국어로 보고한다.
- 언리얼 확인은 실제 가져온 에셋과 프로젝트에서 수행하며,
  실행하지 않은 검증은 완료했다고 보고하지 않는다.

## Heroine animation workflow

### 최우선 품질 게이트: 관절 꺾임과 손가락 자세

사용자 지시(2026-10-19): 모든 캐릭터 애니메이션 제작·리타기팅·보정·엔진 전달에서 손을 포함한 관절 꺾임과 어색한 손가락을 최우선 결함으로 취급한다. 발견된 큰 꺾임을 남긴 채 완료 또는 적용 가능으로 보고하지 않는다.
- 원본/리타기팅/보정/엔진 재생을 구분하여 원인을 확인한다. 손목만 독립 회전시키지 말고 어깨–팔꿈치–전완–손바닥 축과 엄지·각 손가락 마디를 함께 확인한다. 무릎·발목의 역꺾임도 같은 기준으로 검사한다.
- 승인된 자연스러운 원본 손 자세를 기준으로 엄지 벌어짐, 손가락 간격·과굴곡·역굴곡·교차, 손바닥 방향을 확인한다. 모든 손가락을 동일 각도로 펴거나 구부린 수치만으로 자연스럽다고 판정하지 않는다.
- 핵심 자세뿐 아니라 접근·최대 변형·유지·회수·클립 경계와 블렌드 중간을 정상 속도/저속 및 프레임 단위로 검사한다. 정면·측면·손 근접 구도를 사용하고 문제 프레임과 수정 전후를 기록한다.
- quaternion 연속성, 본 위치 오차, 데이터 일치, IK 도달 성공은 외형 합격 증거가 아니다. 실제 저장본의 메시 변형과 엔진 재로드 후 재생을 따로 확인한다. 엔진의 리타기팅·압축·IK·추가 레이어가 보정을 훼손하지 않는지 확인한다.
- 결함 발견 시 원본 자세, 본 축/매핑, 전완 비틀림, IK pole, 키 보간, 스킨 변형 중 원인을 구분하고 연결 관절까지 보정한다. 수정 후 전체 관련 클립과 경계를 재검사한다. 애매한 연출 변경은 이미지와 선택지를 먼저 제시한다.
- 검증 영상·검사 범위·미검증 항목을 저장한다. 사용자 검수 단계가 있는 작업은 승인 후 엔진에 반영하며, 승인된 관절·손가락 자세의 보존을 다시 검증한다.

Before heroine animation, rigging, retargeting, or animation polishing work, read
`ArtSource/Heroine_Tripo_Review/AnimationWorkflow/SKILL.md`. It records the current
deliverables, preserved character style, contact/tempo/garment checks, Unreal
handoff steps, and lessons from retired drafts. Start from the maintained source
listed there, not removed intermediate versions.

# Modular environment production

Before modular environment asset production, concept-to-Unreal scene reconstruction,
or stairwell scene revisions, read `ArtSource/Stairwell_Modular/Workflow/SKILL.md`
and its `CURRENT.md`. They record the maintained playable map, reusable sources,
human review stages, character-scale-first checks, and cleanup rules. Use the
maintained sources rather than retired backup maps or one-off revision scripts.

For Tripo environment reconstruction, vegetation/water, reference matching, or
environment cleanup, also read `ArtSource/OvergrownHall/Workflow/README.md` and
`ArtSource/OvergrownHall/CURRENT.md`. They record the user-approved scene,
reusable lessons, source dependencies, and separate visual/play/performance checks.


# Build working files — cleanup protection

User instruction (2026-10-14): do not delete or clean the project `Intermediate/` or any `Plugins/*/Intermediate/` directories. Other chats build in this shared checkout; generated compiler inputs can be in active use even when a momentary process check finds no build. Do not run Clean/Rebuild or remove build working files as disk cleanup. After the interrupted 2026-10-14 cleanup, allow the existing build to regenerate missing inputs; do not start a competing build.

# One-off Unreal validation cache policy

For every new one-off Unreal validation/review launch (including PIE probes,
headless checks, screenshots, and direct shell commands), include both
`-NoAssetRegistryCache -NoAssetRegistryCacheWrite` in the Unreal editor command.
This is especially important when using a new `-UserDir` per run: repeated
Asset Registry caches must not be generated in each validation folder.
Before launching, verify these flags are present in the actual command, even
when copying an older script. Use `tools/test-scene-game-pie.ps1` or the
`tools/run-s0-*.ps1` launchers as examples.

Keep normal interactive editor cache settings unchanged. Apply this policy to
future validation launches only; do not stop or restart ongoing jobs to add flags.
These flags control Asset Registry caches, not all Unreal or Git LFS caches.
They may increase validation startup scanning time. Keep validation logs,
reports, screenshots, source assets, autosaves, Packaged output, existing LFS
objects, and Git configuration/commit behavior intact. This policy does not
authorize deletion of Saved or Intermediate directories or automatic cleanup.
