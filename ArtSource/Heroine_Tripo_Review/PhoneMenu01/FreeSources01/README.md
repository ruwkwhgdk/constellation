# 무료 공식 원본 — 2026-10-21

사용자가 Adobe 로그인을 완료한 뒤 Mixamo 공식 UI에서 직접 다운로드했다. 유료 구매, 재배포 사이트, 생성 모션을 사용하지 않았다.

- 검색: https://www.mixamo.com/#/?page=1&query=phone
- 이용 안내: https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html
- 설정: X Bot, FBX Binary, With Skin, 30fps, Keyframe Reduction none, Arm-Space 50, Overdrive 50, Mirror off, Trim 0–100.
- `Texting_While_Standing.fbx`: SHA256 `CD6168F426C425DE9FF0A6508FDED753BD1AA37A8382B9F6AD5FE9A3289A3FDE`, 708프레임. 양손·가로 그립으로 최신 사용자 조건에 맞지 않아 제외.
- `Texting.fbx`: SHA256 `347CF0B184CDFC323A68271A69392331818905AF0C4EFB2A72B6E73904792148`, 557프레임. 오른손 한손 사용 비교 후보. 손을 올리는 동작이어서 실제 주머니 꺼내기 연출 적합성은 별도 확인 대상.
- `Talking_On_A_Cell_Phone.fbx`: SHA256 `D60D409492AFA1250CA76B6A9D69EC00482F5C3938A250DB72AFECD6BCDAC4ED`, 1118프레임. 오른손을 허리 뒤로 가져가는 꺼내기/수납 구간. 원본 1–72 및 1040–1118을 편집 후보에 사용. 통화 중 귀에 대는 구간은 제외.
- `Talking_On_Phone.fbx`: SHA256 `F4C35B4CB342FDA6657F7EE62CD50236AFC094639E910331B39BB2386AFB2B80`, 1166프레임. 비교 조사본, 현재 미채택.
- `Talking.fbx`: SHA256 `D29E91212954F8E56417C23770ACF0E5BAC0E7B313D6E700437F251A6E734762`, 145프레임. 비교 조사본, 현재 미채택.

`../OneHandSourceEdit01/source_frames.json`에 편집본 285프레임의 원본 대응을 기록했다. 원본 구간 사이 12프레임 크로스페이드 두 곳을 제외하고 본의 로컬 자세를 그대로 사용한다. 새 꺼내기·넣기 자세를 작성하거나 역재생하지 않았다. 이 편집본은 사용자 승인본이 아니다.

각 폴더의 `*_Raw.blend`는 다운로드한 모션을 그대로 가져온 보존본이다. `audit.json`은 실제 본 이름·프레임 범위·손/골반 위치를 기록한다. 소스 데이터를 타인에게 독립 재배포하는 공개 저장소에 올리지 않는다.

상용 게임에 사용할 수 있다는 공식 안내와 실제 동작/캐릭터 적합성은 별개다. 손가락 근접, 주머니 접촉, 클립 구분 및 리타기팅 검수 후 사용자 영상 승인 전에 엔진에 반영하지 않는다.
