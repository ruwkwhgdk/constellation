# 폰 메뉴 — 2026-10-21 방향 수정

## 2026-10-21 정식 DLL 교체·재시작 검증 완료

사용자가 에디터 종료 후 정식 DLL 교체와 재시작 검증을 요청했고, PIE 테스트용 백틱(`) 키 추가도 요청했다. Esc 매핑은 유지하고 백틱을 같은 메뉴 토글/닫기에 추가했다. 콘솔 충돌을 피하기 위해 프로젝트 콘솔 키를 F10으로 옮겼다.

- 정식 증분 빌드 성공: `Saved/PhoneMenu/BaseDeployment01/build-console.log`. Clean/Rebuild 및 Intermediate 삭제 없음.
- 모듈 매니페스트와 재시작 프로세스의 실제 로드 목록 모두 `UnrealEditor-Constellation.dll` 확인. 임시 suffix DLL 사용 아님. `loaded-modules.json` 참조.
- 정식 DLL의 `Constellation.PhoneMenu.ApprovalAndCleanup` 자동 테스트 성공, 프로세스 종료 코드 0.
- 원본 프로젝트를 재시작한 에디터 PIE에서 Slate 백틱 key-down/up으로 10회 열기/닫기, 메뉴 Enter–Tab–Enter 선택, 일시정지/카메라/이동·시점 입력/커서 복귀 통과. `UnrealApply01/BaseRuntime_20261021_042205/result.json` 오류 없음.
- 검수 도구의 캐시된 Snapshot으로 발생한 초기 UI 검수 실패 2건은 별도 실패 기록에 보존했다. 현재 상태를 새로 읽는 Snapshot으로 변경 후 통과했다. 게임 UI 코드를 우회한 버튼 호출로 대체하지 않았다.
- 검수 맵을 저장하지 않고 기존 `/Game/Constellation/Review/LittleGirl_v03/L_LittleGirl_v03_Review`를 다시 열었다. 에디터 PID144036은 계속 실행한다.

이번 확인은 원본 프로젝트의 에디터 PIE이며 패키징 빌드/여러 화면비/벽 근접 검수는 포함하지 않는다. 승인된 손–폰 위치 오차는 유지한다. 아래 정식 DLL 보류 기록은 이 결과로 대체된다.

## 2026-10-21 영상 검수 후 엔진 진행 승인

사용자: “핸드폰 위치가 손과 조금 맞지 않는 오류가 있긴 한데, 일단 진행해 줘.”
`OneHandReview04/Heroine_Mixamo_OneHand_Cube08.blend`와 전달 영상 기준으로 언리얼에 연결했다. 손–폰 위치 오차는 사용자가 인지한 잔여 보정 항목이며 해결 완료로 보고하지 않는다. 아래 승인 대기 문구는 당시 기록이다.

`UnrealApply01`에서 승인 저장본의 본 변환과 폰 부착 285프레임을 추출했다. `/Game/Constellation/Characters/Heroine/GamePilot/Phone`의 Draw/Hold/Stow 시퀀스·몽타주를 저장했다. 새 프로세스 재로드 검사에서 26,978개 본 변환, 최대 위치 오차 0.000935cm/회전 오차 0.001054도. 원본 리그·메시 교체 없음.

현재 `BP_Player_Heroine`에 PhoneMenu 컴포넌트와 승인 게이트, 오른손 부착 트랙을 저장했다. 별도 프로세스에서 최초 저장은 열린 에디터의 파일 잠금(Error32)으로 실패했고, 새 DLL이 Hot Reload로 로드된 원본 에디터에서 해당 Blueprint만 저장했다. 미저장 NPC 작업은 저장/수정하지 않았다.

최종 코드 suffix2027 증분 빌드 성공. 별도 검수 에디터에서 실제 플레이어 Blueprint를 불러와 Enhanced Input의 Esc 액션으로 열기, Slate Esc로 닫기, 10회 반복, 일시정지/카메라/이동·시점 입력/커서 복귀와 Enter–Tab–Enter 메뉴 선택을 확인했다. 결과: `UnrealApply01/Runtime_20261021_020141/result.json`. 실제 키보드의 Esc key-down을 통한 열기는 액션 주입과 별도로 검증하지 않았다. 테스트는 격리 에디터 PIE이며 패키징 실행 검증이 아니다.

검수 카메라는 캐릭터 기준 위치 `(30,-25,35)cm`, 회전 `(Pitch=-52,Yaw=130,Roll=0)`, FOV 65로 저장했다. 폰 왼쪽/임시 메뉴 오른쪽 구도다. 메뉴 버튼은 6개이며 선택 상태만 표시한다. 닫을 때 수납 모션과 게임 화면 복귀를 수행한다.

최종 저장 후 새 격리 에디터에서 카메라 값을 덮어쓰지 않고 Blueprint를 다시 로드하여 1회 전체 흐름과 키보드 선택을 재검증했다. `UnrealApply01/Runtime_20261021_021255/result.json` 오류 없음. 검수 에디터는 종료했고 원본 에디터 PID63684는 유지했다. 원본 에디터를 닫아 달라는 요청은 반복하지 않는다.

외형: 근접 카메라에서 기존 폰–손 위치 오차가 크게 보인다. `UnrealApply01/source-camera80.png`는 승인 Blender 저장본을 엔진 검수와 대응하는 각도로 새로 렌더한 이미지다. 동일한 어긋남이 재현되어 임의로 손가락·그립을 재작성하지 않았다. 데이터 일치와 기능 통과를 최종 외형 합격으로 간주하지 않는다. 모든 관절의 엔진 프레임별 다각도 검사, 실제 맵 벽 근접·여러 화면비·중단 상황의 런타임 검수는 잔여 항목이다.

사용자가 현재 원본 에디터를 닫을 수 없다고 답했다. 원본 에디터를 유지하고 별도 검수 프로세스를 사용한다. 정식 base DLL 교체와 원본 프로젝트의 완전 재시작 검증은 보류 상태이며 재승인을 반복 요청하지 않는다.

**최신 선택:** 사용자는 양손·가로 그립 후보를 사용하지 않고 **한손·세로 그립을 유지해 무료 원본을 추가 탐색**하도록 답했다. Texting While Standing 및 Retarget01/02/Prop01/02는 채택하지 않는다. 원본 사용 승인으로 해석하지 않는다.

사용자 최신 지시: 꺼내기/넣기 동작을 직접 제작하지 않는다. 이전 Mixamo Reaching Out 작업처럼 **무료이며 상업 이용 가능한 기존 애니메이션 원본**을 검색·확보하고 리타기팅한다. 유료 팩은 제외한다.

- Candidate01–10은 중단된 직접 제작 실험이며 승인본/엔진 전달본이 아니다. 이 후보를 유지 시작점으로 삼거나 추가 보정하지 않는다.
- 캐릭터 입력은 사용자가 지정한 `C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/CarryPickupD01/Attempt06/Heroine_Pickup_Chair.blend`. 원본을 보존한다.
- 무료 원본의 꺼내기·유지·넣기 구간을 실제 확인한다. Texting 같은 유지 루프만으로 꺼내기/넣기가 있다고 판단하지 않는다.
- 원본 자세·손가락·타이밍 보존을 우선한다. 캐릭터 리그 차이에 따른 리타기팅과 폰 접촉 검증을 수행한다. 직접 작성한 꺼내기의 역재생으로 수납을 대체하지 않는다.
- 원본과 캐릭터 적용본의 정면·측면·손 근접 영상을 먼저 제공한다. 사용자 영상 승인 전 언리얼 임포트/활성화 금지.
- 기존 `AnimationWorkflow/ReachTouch.md`의 원본 확보·리타기팅·영상 비교 방식을 따른다.

## 메뉴 코드 상태

`Source/Constellation/PhoneMenu*`에 상태 전환, 임시 UI, 입력/카메라/일시정지 복구 코드를 구현했다. 기본 게이트는 false이며 설치된 플레이어 컴포넌트에서 승인/허용을 활성화한다.
독립 상태 테스트 통과. suffix2024에서 `Constellation.PhoneMenu.ApprovalAndCleanup` 및 부착 트랙 샘플링 테스트 성공 (`Saved/PhoneMenu/TestProject03/tests.log`). 이후 반복 열기, 진행 중 watchdog, Tab 탐색, 컨트롤러 재바인딩 수정을 포함한 suffix2027 빌드 및 위 런타임 검수 통과. 원본 프로젝트 base DLL 교체는 보류다.

## 무료 원본 조사

- Mixamo 공식: https://www.mixamo.com/
- Adobe 공식 FAQ: https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html — Adobe ID로 무료 사용, 상업 프로젝트 사용 가능 설명 확인.
- MoCap Online 무료 샘플: https://mocaponline.com/products/free-mocap-animation-pack — 무료 상업 사용 조건 및 포함 클립 확인 대상. Texting walk가 꺼내기·넣기를 포함한다고 간주하지 않는다.
- Fab의 Using Phone Animation Pack, Phone FPS Animation Pack, MetaHuman Cinema Pack 및 MoCap Central Core Motion 유료 후보는 사용자 무료 조건에 따라 제외. 구매하지 않았다.

사용자 로그인 완료 후 `FreeSources01`에 공식 Mixamo FBX 다섯 개를 확보했다. 다운로드 설정과 SHA256은 해당 폴더 README.md 참조. 양손 `Texting While Standing`은 제외했다.

현재 검수 후보는 `OneHandSourceEdit01/Mixamo_OneHand_SourceEdit01.blend`: `Talking On A Cell Phone`의 오른손 꺼내기·수납과 `Texting`의 한손 사용 구간을 편집했다. 285프레임/30fps, 두 곳에 12프레임 크로스페이드. 원본 프레임 대응은 `source_frames.json`. 주머니 동작은 허리 뒤쪽이며 현재 캐릭터의 옷과 맞는지 별도 확인해야 한다.

현재 영상 검수 후보는 `OneHandReview04/Heroine_Mixamo_OneHand_Cube08.blend`, 전달 페이지는 `OneHandReview04/Delivery/review.html`. 사용자 승인본/엔진 전달본이 아니다. 이전 OneHandRetarget01, OneHandProp02/03, OneHandReview01/02/03은 부착/여유 거리 비교본이며 최신 전달본으로 사용하지 않는다.

`OneHandRetarget02`에서 무료 원본의 손 위치를 캐릭터 비율에 맞춰 리타기팅했다. 옷과 폰 사이에 필요한 여유가 최대 5.06cm로 측정되어 유지 구간에서 팔 위치를 전방 5.5cm 보정했다. 어깨–팔꿈치를 함께 풀고 원본 손목 방향/손가락 로컬 자세를 유지한다. 꺼내기/넣기를 새로 작성하지 않았다. 큐브는 두 원본의 그립에 각각 맞춘 부착값을 같은 12프레임 구간에서 연결한다.

최신 후보의 `cube_contact.json`: 손 정점 998개, 31–245프레임, 0.5mm 초과 침범 검출 없음. `cube_body_contact.json`: 나머지 본체 정점, 73–206프레임, 같은 기준의 침범 검출 없음. 전체 삼각형 충돌·완전한 접촉·외형 합격을 보장하는 검사가 아니다. 소매 접촉 문제가 남았던 Cube07 대신 Cube08을 사용한다. 검수 렌더의 길게 늘어진 선은 Workbench 그림자 문제였으며 그림자를 끈 영상으로 전달한다.

주머니 동선은 허리 뒤쪽이고 현재 가디건 앞주머니와 일치하지 않는다. 원본에서 전환 중 반대손이 짧게 보조한다. 게임 카메라/임시 UI 연결, 유지 루프 경계, 실시간 블렌드, 실제 언리얼 애셋 검사는 사용자 영상 승인 이후 진행한다. 예전 직접 제작 Candidate01–10 또는 양손 Retarget01/02로 되돌아가지 않는다.

전달본 검증: `OneHandReview04/Validation/compare.json`은 `equal_captured_fields`이며 차이 없음. `key_continuity.json`은 1–285프레임 회전 키 부호 불연속 없음. MP4는 1920×640, 30fps, 285프레임/9.5초이며 FFmpeg 전체 디코드 확인 완료. 데이터 보존 검사와 외형 합격은 별개이며 사용자 영상 검수는 아직 대기 상태다. 언리얼 확인은 수행하지 않았다.
