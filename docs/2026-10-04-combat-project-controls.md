# 프로젝트 기본 조작값 동기화

2026-10-04. 사용자 요청에 따라 전투 시험장의 주인공 이동 속도와 카메라 회전·추적 설정을 원본 프로젝트 기준으로 맞췄다.

## 기준과 적용 결과

| 항목 | 원본 기준 / 적용값 |
|---|---|
| 실제 보행 최고 속도 | Ac_Stats의 Walk Speed: **500cm/s** |
| 가속·감속 | 각각 2048cm/s² |
| 캐릭터 방향 전환 | 이동 방향 회전, Yaw 360°/s |
| 카메라 거리·FOV | 450cm / 90° |
| 카메라 부착 위치 | Z 10cm, Target Offset 0 |
| 위치 추적 지연 | 활성화, 속도 **10**, 최대 거리 **60cm** |
| 회전 추적 지연 | 비활성화 |
| 마우스 회전 | 원본 IAC_Default의 IA_Look 매핑과 modifier 재사용 |
| 컨트롤러 배율 | Yaw 2.5 / Pitch -2.5 |
| 위아래 시점 범위 | 원본 CameraManager의 -89.9°~89.9° |

BP_Player_Heroine의 CharacterMovement 기본값은 600이지만, 실제 BP 입력/초기화 경로에서 Ac_Stats의 Walk Speed를 사용한다. 따라서 600이나 과거 자료의 800이 아닌 **현재 스탯의 500**을 기준으로 했다. 원본 그래프와 추출 값은 Saved/CombatAudit/20261004/heroine-control-graph.txt 및 project-control-defaults.json에 보관했다.

시험장에 별도로 넣었던 감도 0.15와 시점 제한을 제거했다. 원본 Look 매핑만 별도 임시 컨텍스트로 연결해 프로젝트의 키·modifier 처리를 재사용하고, BP와 같은 AddControllerYawInput/AddControllerPitchInput 경로로 처리한다. 빙의 해제·종료 시 이 시험장 컨텍스트만 제거한다.

기존 카메라 기준 WASD, Tab 잠금/해제, 공격 중 이동 차단은 유지한다. 자유 이동에서는 원본의 이동 방향 회전 속도를 따른다.

## 이동 모션

RunSoft의 제작 기준은 168cm/s이다. 게임 이동 속도를 여기에 맞춰 낮추지 않고, 요청한 500cm/s를 유지했다. 기존 배속 상한 1.5는 500cm/s에서 모션과 이동을 불일치시키므로 제거했다. 최고속에서는 약 2.98배로 재생된다.

이는 기존 클립의 배속 대응이며, 500cm/s에 맞춘 새 달리기 모션 제작·전환 블렌딩·체감 품질 검토가 끝났다는 의미는 아니다. 후속 모션 작업도 게임 속도 기준을 임의로 바꾸지 않고 진행한다.

## 검증

- 전체 Development Editor 빌드 성공.
- 전투 자동화 **15/15 성공**. ProjectControlDefaults 및 원본 컨트롤러 배율 비교 포함.
- 시험장 저장본을 다시 열고 원본 BP·스탯과 속도·카메라·Look 자산·회전 배율 직접 비교: matched=true.
- 실제 게임에 마우스 X/Y를 주입해 원본 Enhanced Input 매핑을 통한 양축 회전 성공.
- 실제 W 입력: 가속 구간을 포함한 약 1초 이동 440.28cm, 카메라 정면과 방향 일치도 1.0000.
- 달리던 중 공격의 일반 이동 0.00cm, 공격 종료 후 237.69cm 이동 및 달리기 모션 복귀.

증거:
- Saved/Logs/Combat-build.log
- Saved/Logs/Combat-tests.log
- Saved/Logs/Combat-project-controls-verify.log
- Saved/Logs/Combat-project-controls-final.log
- Saved/CombatAudit/20261004/lab-verification.json
- Saved/CombatAudit/20261004/movement-review.json

## 사용과 후속

시험장 경로와 조작키는 동일하다. 이전 실행을 종료하고 ./tools/play-combat-lab.ps1로 다시 실행한다.

tools/setup-combat-lab.py는 전투 데이터·몽타주를 재사용하면서, 이번 요청에 따라 플레이어 이동·카메라·Look 설정을 원본에서 다시 동기화한다. 따라서 시험장만의 해당 설정을 따로 바꾼 뒤 이 스크립트를 실행하면 프로젝트 값으로 돌아간다. 원본 캐릭터·스탯·입력 자산은 수정하지 않는다.

다음 구현 범위는 입력 예약·콤보·회피·피격이며, 여기서 확정한 프로젝트 조작값을 기반으로 확장한다.


후속 구현: [전투 입력 예약과 후속 공격 연결](2026-10-04-combat-input-buffer.md). 기존 조작값을 유지한 3단계 연결 검증을 추가했다.
