# Carry 애니메이션 기능 검토본

유지 원본 `../RunSoft/Heroine_Run_Soft.blend`의 모델과 Rigify 리그를 보존한 별도 Action이다. 모델·얼굴·체형·스킨 웨이트는 변경하지 않았다. 각 `Heroine_Carry_*.blend`가 편집 원본이며 `AS_Heroine_Carry_*.fbx`가 refined 스켈레톤 전달 파일이다.

| 클립 | FPS | 길이 | 접촉/분리 Notify |
|---|---:|---:|---:|
| Pickup | 30 | 1.4초 | 0.55초 |
| Place | 30 | 1.4초 | 0.85초 |
| Throw | 30 | 0.9초 | 0.38초 |
| Hold | 30 | 1.2초 반복 | 없음 |
| Aim | 30 | 1.2초 반복 | 없음 |

`build_carry.py`가 Action과 접지 FK 보정을 생성하고 `export_carry.py`가 유지 Delivery 게임 리그로 출력한다. `render_carry.py`와 `render_all_carry.py`는 검토 프레임을 만든다. CLI는 프로젝트 `tools/run-blender.ps1`로만 실행한다.

현재 플레이어는 기존 Mixamo 베이스 메시를 사용한다. Unreal의 `CarryRetarget.cpp`가 기준 본 좌표계와 신체 비율을 맞추고, 유지 Idle의 골반 높이에 첫 프레임을 맞춰 게임용 `AS_Carry_*_Game`을 생성한다. 원시 FBX 기준 포즈와 첫 프레임 사이의 높이 차이를 동작으로 취급하지 않는다. 게임용 몽타주는 `/Game/Constellation/Characters/Heroine/Base/Animation/Carry/AM_Carry_*`다.

운반·조준은 상체 슬롯과 양손 IK로 기존 보행에 합성한다. 전환 모션은 전신이며 물건의 접촉 시점을 Notify로 연결한다. 서로 다른 크기의 물건에 동일한 전환 모션을 적용하므로 물건별 Grip/CarryOffset과 접촉 자세를 확인해야 한다.

제작 소스의 발 위치 최대 편차는 집기·내려놓기·던지기에서 0.273cm였다. 이는 게임에 리타깃된 신발 표면의 미끄러짐이나 의상 간섭 전체를 보증하는 수치는 아니다. 본 리소스는 첫 기능 검토용이며 최종 연출/모션 품질의 사용자 시각 검토가 필요하다. 실제 플레이 검토 자료는 프로젝트 `Saved/CarryReview/`에 기록한다.

설정·입력·지원 물건 조건은 `docs/hold-and-throw.md`를 참조한다.
