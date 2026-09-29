# 원화 보정01 · 건축/창살/지붕
현재 레벨은 TripoFull/Maps/L_OvergrownHall_TripoFull을 유지한다.
- Blender: Scripts/refine_tripo_structure.py. Tripo06 원본 외곽을 보존하고 같은 모델의 직선 부재로 성긴 내부 격자(세로3/가로3)를 구성. Tripo04 상부 장식 돌출 제한 및 Smooth4회.
- Unreal: Content/Python/refine_tripo_hall_structure.py. 전용 메시2개 반입,창8/측면아치8교체,주두규격축소,Tripo지붕조각14개 추가. 재실행시 기존 OH_STRUCTURE_Roof 액터를 대체하여 중복 배치를 방지한다.
- 기존 v002 전체 반입을 재실행하면 이 보정은 되돌아가므로 그 뒤 이 보정 스크립트를 실행한다.
- 현재 조명/카메라/벤치/식생/수면/비행배치는 유지했다. 실제 플레이 및 최종아트 승인 아님.
- 비교: review.html. 수정 전 v002/unreal_full.png 보존,수정 후 unreal_structure.png는 실제 Unreal 캡처.
최종 실제 렌더 갱신:2026-09-25 18:58:59. 창살 굵기5cm 및 프레임 안쪽으로 겹치도록 길이를 보완했다. 저장 레벨 검사 재통과. 원화와 완전 일치하는 최종 상태는 아니며, 세부 접합과 조명/식생/수면 후속 검토가 남는다.
