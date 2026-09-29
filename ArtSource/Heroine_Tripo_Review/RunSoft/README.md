# 상하 움직임과 템포를 완화한 달리기

- 언리얼: `/Game/Resources/Characters/PC/player_heroine_new/Animations/AS_player_heroine_new_Run_Soft`
- 프리뷰 메시: `SK_player_heroine_new_RunPreview` (기존 치마 보정 유지)
- 편집 원본: `Heroine_Run_Soft.blend`
- 미리보기: `Run_Soft_Preview.gif`

현재 유지하는 달리기 편집 원본입니다. 이전 초안들은 사용자 요청에 따라 정리했습니다. 몸통 상하 이동 범위는 약 17.36cm에서 10.77cm로 38% 감소했습니다. 공중 구간의 지면 여유를 측정해 도약 높이를 낮췄으며, 접지 구간의 높이와 기존 관절 회전은 거의 그대로 유지했습니다. 전체 주기는 0.8초에서 1.0초로 늘렸습니다(동작 템포 20% 감소).

권장값은 이동 속도 168cm/s, 재생 배속 1.0입니다. 느린 조깅에 가까운 속도입니다. 이미 1초로 리타이밍된 클립이므로 추가로 배속을 0.8로 낮출 필요가 없습니다. 게임 이동 속도와 기존 Blend Space 연결은 변경하지 않았습니다.

120Hz 검사에서 접지 구간 수평 발 미끄러짐은 왼쪽 최대 1.30mm, 오른쪽 0.83mm였고, 최소 신발 높이는 지면 아래 0.24mm였습니다. 무릎 굽힘·루프 연결·기존 범위의 치마 외곽 간섭 검사가 통과했습니다. 전체 30프레임을 렌더하고 주요 자세를 시각적으로 확인했습니다. 언리얼에 임포트한 뒤 별도 프로세스에서 저장된 1초 클립, 스켈레톤, 재질, 동기화 마커를 다시 검증했습니다. 이번 수정본의 실제 게임 이동 및 전환 블렌딩 검증은 포함하지 않습니다.

상세 기록: `changes.json`, `validation.json`, `unreal_verification.json`.

다음 작업은 이 폴더의 최종 `.blend`에서 시작합니다. 과거 초안을 입력으로 삼는 `soften.py`, `prepare_tools.py`는 제거했습니다. `export.py` → `import_unreal.py` → `verify_unreal.py`는 현재 전달본 기준으로 독립 실행할 수 있습니다. 프리뷰는 `render.py -- all` 후 `finish.py`로 생성합니다. 필요한 게임 스켈레톤과 익스포터는 `../RigReferenceFit/Delivery`에 있습니다. 재사용 절차는 `../AnimationWorkflow/SKILL.md`를 참고합니다.
