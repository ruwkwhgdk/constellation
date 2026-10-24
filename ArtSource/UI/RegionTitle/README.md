# 지역 진입 타이틀 — A안 v2 (2026-10-13)

기준: Concepts/2026-10-13/region-title-A-v2-spacing.png.

구현: Source/Constellation/RegionTitleWidget.h/.cpp. 기존 WBP_RegionTitle의 RegionTitleName/RegionTitleDesc FText를 읽으며 BP_RegionTrigger의 지역 조회/DoOnce/ShowDelay는 유지한다. 주제목과 부제는 이미지가 아닌 동적 텍스트다. 알려진 기존 RichText 래퍼만 제거하여 표시한다.

시각: 중앙보다 조금 위. 5개 금빛 별과 얇은 연결선, 명조 제목, 구분선/마름모, 여유 있는 부제. 별/선은 Slate 벡터이며 성운만 투명 PNG다. 전체 화면 패널/암전은 없다. TitleSubtitleGap, TitleFont, SubtitleFont, NebulaOpacity를 위젯 기본값에서 편집 가능하다. 긴 제목은 별도로 축소하여 맞춘다.

연출: 별 0~0.4초, 선/텍스트 0.4~0.9초, 3.2초까지 유지, 4초까지 페이드 후 자기 제거. 동일 플레이어에 새 타이틀이 오면 이전 것을 제거하고 재시작한다. 기존 트리거의 PlayAnimation 이후 제거 경로를 끊고 네이티브 수명주기로 통합한다. 학교 오프닝의 외부 4초 타이머는 비네이티브 위젯에만 유지한다. 입력 모드/커서/포커스/일시정지를 변경하지 않는다.

리소스:
- Resources/T_RegionNebula.png → /Game/Constellation/UI/RegionTitle/T_RegionNebula
- Fonts/NanumMyeongjo-Regular.ttf → FF_RegionMyeongjo, F_RegionMyeongjo
- 폰트 출처: https://github.com/google/fonts/tree/main/ofl/nanummyeongjo
- 재배포 라이선스: Fonts/OFL.txt. 폰트는 프로젝트에 포함되며 사용자 PC의 시스템 폰트에 의존하지 않는다.
- 성운은 ImageGen으로 신규 생성: 투명 캔버스, 국소적인 청색 수채/벽화 성운, 드문 금빛 먼지, 텍스트/배경 장면/패널/별자리 제외. 원본의 알파 그대로 사용한다.

적용:
1. tools/import-region-title.py로 PNG를 UI 텍스처로 가져온다.
2. ConstellationEditor 빌드 후 tools/create-region-title-font.py로 폰트 자산을 생성/저장한다. 최초 코드 로드 전에 폰트가 없다면 초기 생성 세션의 CDO 경고가 발생할 수 있다. 폰트 생성 후 새 프로세스에서 적용한다.
3. tools/apply-region-title.py를 에디터가 자산을 잠그지 않는 상태에서 실행한다. 첫 수정 전 백업: Saved/RegionTitle/*-before.uasset.
4. Constellation.RegionTitle.Lifecycle와 Constellation.SchoolOpening.TutorialRetry 자동화, tools/verify-region-title-pie.py 별도 UserDir 검증.

## 최종 적용 및 검증 (2026-10-13)

- ConstellationEditor Win64 Development 빌드 성공.
- WBP_RegionTitle, BP_RegionTrigger 최종 저장 완료. 새 프로세스에서 저장된 위젯의 네이티브 부모 확인.
- 자동화 Constellation.RegionTitle.Lifecycle 및 Constellation.SchoolOpening.TutorialRetry 2/2 통과. 부동소수점 오차 허용값을 명시하여 시간 경계 비교 검증.
- PIE: 일반/긴 제목/빈 부제, Toast 동시 표시, 커서·이동/시점 제한·일시정지 상태 유지, 4초 제거, 연속 호출 교체, 외부 제거 통과.
- 저장된 BP_RegionTrigger의 기존 Show Region Title 경로를 실행하여 DT_RegionStringData의 실제 '텅 빈 교실' 표시와 정상 제거 확인. 재부모화 등 임시 수정 없이 검증했다.
- 밝은 Template_Default와 어두운 Entry 배경에서 화면 확인. 배경은 QA용이며 게임 배경 리소스에 추가하지 않았다.
- 전체 학교 경로 플레이, 다른 화면비/DPI의 실기기 검증 및 연출 영상은 미실시. 화면 대응은 제한 영역 내 ScaleToFit 및 제목/부제 개별 축소로 구현했다.
- 캡처: Resources/preview-bright-pie.png, preview-dark-pie.png, preview-long-pie.png, preview-no-subtitle-pie.png.
- 로그/결과: Saved/RegionTitle/build.log, apply.log, tests.log, pie-final.log, pie-result.json.

전체 빌드를 막던 LittleGirlBasketActor.cpp의 SpawnActor 클래스 인수 누락과 TObjectPtr→auto* 변환도 최소 수정했다. 바구니 동작 변경은 없다.
