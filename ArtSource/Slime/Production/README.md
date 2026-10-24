# Slime Liquid — Revision 10

유지 원본: `Slime_Liquid.blend`.
원화: `../Concepts/2026-10-13/slime-form-refinement-02.png`.

## 젤 재질

- 불투명 표면의 색 그라데이션을 실제 Transmission 0.94 / IOR 1.22 재질로 교체했다.
- 외피는 Roughness 0.16, Coat 0.16이며, 보라색 Volume Absorption 밀도 0.8–3을 사용한다.
- `Slime_InnerGel`은 몸체와 꼭지 내부의 별도 스킨 볼륨이다. 밀도 8–32의 불규칙한
  보라색 흡수층이며, 경계의 농도가 0으로 풀려 단단한 내부 구체로 보이지 않게 한다.
- 얇은 외곽·바닥 점액에는 빛이 통과하고, 두꺼운 중앙에는 짙은 보라색이 겹친다.
- 물방울의 표면은 외부에서 보이지만 같은 젤 내부로 잠긴 후에는 불필요한
  중첩 굴절면이 생기지 않도록 Transmission Ray에 투명 처리한다.
- 미리보기는 Cycles GPU / AgX Medium High Contrast 기준이다.

## Idle

Revision 10: 물방울의 이전 기울기와 휘어진 꼬리를 제거했다.
자유 낙하 구간에서만 물방울의 세로축을 월드 Z축에 맞춘다.
몸체를 타는 동안에는 긴 축을 표면 접선에, 납작한 면을 몸체 표면에 정렬한다.
접촉 직후와 분리 직전에는 quaternion 보간으로 자세를 부드럽게 연결한다.
몸체의 z=0.16m 경계에서 놓인 뒤에는 월드 X/Y를 고정하고,
z = release_z − 0.5 × 9.81 × t²로 가속 낙하한다.
바닥 점액의 움직이는 끝점을 계속 따라가던 수평 흔들림을 제거했다.

- 4초/24fps. 몸과 바닥 점액의 꿀렁임을 유지한다.
- 물방울은 처음에 X/Y를 고정한 채 가속하며 수직으로 내려온다.
- 실제 몸체와 접촉하는 높이를 계산한 뒤, 몸의 곡면을 따라 아래로 흐른다.
- 마지막에는 수직 자세로 돌아와 크기를 유지하며 웅덩이 아래로 하강한다.
- Scale은 전 프레임 `(0.62, 1, 0.24)`로 일정하다. 숨길 때도 축소하지 않는다.
- 수면 아래에서만 내부 복귀하며, 끝과 시작 포즈가 일치한다.

## 전달 파일

- `Slime_Liquid.blend`: 모델, 젤 재질, 14본 리그, 4초 Idle, 검토 조명.
- `SK_Slime_Liquid_Idle.fbx`: 내부 젤을 포함한 5개 스킨 메시와 리그/Idle.
- `Preview/Idle_Liquid_v10.mp4`, `Preview/Idle_Liquid_v10.gif`: 현재 미리보기.
- `Preview/model-sheet-v10.jpg`, `Preview/idle-contact-sheet-v10.jpg`: 검토 시트.
- `revision-10.json`, `build-report.json`: 경로·규격 기록.
- `verification-source.json`, `verification-fbx.json`: 최신 검증.
- `History/`: 이전 수정본 보존 ZIP. v01–v09은 현재 전달본이 아니다.

26,700 triangles / 13,516 vertices. 5개 메시, 14본.
단위 m, 정면 -Y, Z-up, 바닥 피벗. source frames 1–97, 미리보기 1–96.
FBX 재임포트 프레임은 2–98이며 4초 길이는 같다.

## 검증과 Unreal 전달 범위

전체 프레임에서 물방울의 실제 메시의 기준 정점 간 거리·구간별 자세, 초기 수직 낙하,
하단 수평 이동 0·중력 가속도 9.81m/s², 자유 낙하의 수직 정렬과 몸체 구간의 표면 접선 정렬, 본체 접지, 루프 일치를 검사한다.
FBX는 빈 Blender 장면에서 재임포트해 5개 메시, 14개 본, 움직임과 치수를 확인한다.

2026-10-14 Unreal 리소스 교체를 완료했다. 게임용 호환 FBX, 엔진 전용 외피/내부 밀도/
물방울 재질, 기존 전투 동작 보정 및 검증 기록은 `../Integration/README.md`를 따른다.
이 폴더의 원본은 보존하며, Unreal 재임포트에는 Integration의 cm 단위 호환 FBX를 사용한다.
Cycles 볼륨·투과 셰이더는 FBX로 전달되지 않으므로 Unreal 재질은 별도로 구현한 근사 표현이다.

## 유지 작업

`gel_flow_v08.py`: 현재 젤·내부 메시·물방울 경로·저장/출력의 유지 진입점.
`puddle_idle.py`: 바닥 점액 가중치와 애니메이션.
`review_gel_v08.py`: 현재 투과 젤 원본 검사 및 Cycles 전체 렌더.
`verify_fbx.py`: 현재 5메시 FBX 재임포트 검사.
`refine_slime.py`, `build_slime.py`, `review_slime.py`는 이전 수정의 기반/보조 스크립트다.
전체 재생성 시 build 이후 반드시 gel_flow_v08을 적용한다.

Blender는 `tools/run-blender.ps1` 보호 런처로 실행한다.
수작업 원본을 재생성하기 전 먼저 보존한다.
