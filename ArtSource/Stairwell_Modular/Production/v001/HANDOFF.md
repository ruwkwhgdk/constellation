# 계단실 모듈러 v001 검토 인계

22개 채택 번호를 길이·방향 파생형 포함 31개 메시로 제작했다. Blender 기하 검사와 Unreal 임포트·조립 수치 검사를 통과했다. 2026-09-24 사용자가 전체 외형을 채택했다. 텍스처/재질 보완과 원화 장면 재현을 이어간다. 외형 채택이 PIE 검증 완료를 의미하지는 않는다.

- 검토 이미지: [review.html](review.html), 이미지 클릭 시 개별 원본 확대.
- Blender: [stairwell_kit_review_v001.blend](stairwell_kit_review_v001.blend), 모델을 번호별로 펼친 검토 장면.
- Unreal 검토 맵: `/Game/Environment/StairwellModular/ReviewKit/Maps/L_Stairwell_KitReview`.
- 기존 문 검토 맵: `/Game/Environment/StairwellModular/Maps/L_Stairwell_DoorVerification`.
- 기존 문틀·문짝은 재사용했으며 신규 29개 메시만 ReviewKit/Meshes에 반입했다.
- 기준 프로세스: [PRODUCTION_PROCESS.md](../../PRODUCTION_PROCESS.md).

## 확인된 사항

- 01–22 누락 없음, 메시별 삼각형 예산과 UV 확인.
- 바닥 타일 30cm 피치/3mm 줄눈, 140cm 폭의 양쪽 절단 타일 10cm.
- 벽 타일 10cm 피치, 안·밖 코너 타일 면 방향 수정 및 검사.
- 난간 12개 파생형의 4cm 관 단면·25cm 수직 간격·접합면 위치/접선 확인.
- Unreal에서 신규 29개 메시의 실제 치수·재질 슬롯·UCX 개수 확인.
- 저장된 Unreal 맵 재개방 후 계단–참 접합과 난간 유효 폭120cm·브래킷 바깥 방향 확인.
- 형광등 2,869삼각형, 상판 덮개와 발광 표면 추가, 별도 RectLight 배치.

## 외형 검토 시 확인할 사항

규격형 애셋은 기본 표면 재질 상태다. 원화처럼 강한 오염, 녹, 줄눈의 사용 흔적은 후속 외형 보완 대상이다. 형광등은 Tripo 원본을 보존한 보정본으로, 상판 덮개 비례와 하부 발광 위치를 확인해야 한다. 내부 원본 메시의 경계 엣지133개가 남아 있다.

전체 외형 채택은 reports/appearance_approval.json에 기록했다. 후속 수정은 번호와 파생형 이름으로 지정하고 같은 검사를 다시 실행한다.

## 아직 완료하지 않은 것

- 캐릭터 PIE 이동·카메라·전체 머리 위 공간 확인.
- 문 개폐 입력과 런타임 애니메이션.
- 원화 시점의 전체 공간 조립, 조명, 오염 표현.

현재 맵은 애셋 전시 및 계단/난간 접합 확인용이다. 원화 장면 재현 완료본으로 사용하지 않는다.
