# Tripo 외형 교체 · 2026-09-25
사용자가 기존 Blender 절차적 나무·기둥 외형 품질을 부적합으로 판단. Tripo 생성 → Blender 보정 → Unreal 적용 경로로 변경.
기존 Production/Scene 모델은 배치·치수 비교용이며 새 외형 품질의 기준으로 쓰지 않는다.
1차 대상: 02 사각 폐허 기둥 구간, 19 활엽수. 이후 주두·기단, 관목·덩굴, 파손 구조를 같은 과정으로 교체한다.
기둥: 3m 길이, 65cm 사각 단면, 플랫 접합면. 생성 목표12000삼각형, H3.1 HD, 2K PBR/조명 제거. 목표치는 생성 실측값이 아님.
나무: 약6m 높이의 자연스러운 줄기·가지·수관, 원화와 맞는 부드러운 녹색 덩어리. 표면의 잎 표현, 열린 틈, 줄기 연결을 검수한다. 나무에서 AI 출력이 잎을 고형 덩어리로 합치면 그대로 최종 채택하지 않는다.
새 생성 결과는 외형 검토 전 최종 채택으로 표시하지 않는다. 원본GLB 보존 후 보정과 실제 Unreal 비교를 제공한다.

## 현재 생성 결과
- 기둥: https://studio.tripo3d.ai/ko/workspace/generate/9780e0b4-7bed-47ca-8177-a80cebe9f0ec
  Tripo 화면 표시11389삼각형/7053정점. 상부/하부 몰딩이 생성되어 몸통 분리·캡 분리 후 접합 검사 필요. 파일 실측 전.
- 나무: https://studio.tripo3d.ai/ko/workspace/generate/60596073-5df9-4e6b-affc-ca73e0a9abfd
  Tripo 화면 표시29879삼각형/35726정점. 줄기·가지·분리된 수관 형태 확인. 파일 실측 전.
- 총90크레딧, 잔액2465→2375. 추가 생성 없음.
- 내보내기 GLB 요청을 했지만 다운로드 이벤트가 발생하지 않고 Downloads/관련 임시경로에 파일 없음. 사용자가 수동 다운로드 후 경로를 알려주도록 요청한 상태.
- prepare_tripo_environment.py와 import_tripo_environment_review.py는 준비된 초안이며 아직 새 GLB에서 실행/검증되지 않았음. 기둥 원본을 먼저 열어 몰딩/몸통 구간 분할을 구현해야 함. 현재 스크립트의 전체모델 치수 정규화만으로 최종 기둥을 만들면 안 됨.
- prepare_tripo_context.py는 실행 완료: 기존02그룹 중 Shaft 제외한 상부·후면 피어를 보존하는 FBX 및30구간 배치 좌표 생성.
- 새 모델 Blender 보정/Unreal 적용은 아직 미완료. 기존 레벨 수정 없음.

## FBX 수령 및 적용 · 2026-09-25
- 사용자 제공 Downloads의 ruined+concrete+pillar+3d+model.zip / tree+3d+model.zip을 각 Original/에 풀어 보존. GLB 대신 텍스처 포함 FBX로 진행.
- Blender 보정 완료: 기둥 원본11389→몸통4255삼각형,65×65×300cm. 중앙18–80% 구간을 분리·캡 처리. 전체 생성본은 Original에 보존.
- 나무29879삼각형,521×457×600cm. 줄기 피벗과 균일 스케일 정리. 잎은 두꺼운 입체 덩어리/뾰족한 형태로 남아 근접 최종 품질 승인 대기.
- 2K BaseColor/Normal/RM를 추출해 Unreal에 연결. UCX는 기둥/줄기에 단순 박스.
- 실제 검토맵: /Game/Environment/OvergrownHall/TripoReplacement/Maps/L_OvergrownHall_TripoReview
- 기둥30구간,외부나무19그루 교체. 기존 상부·후면 피어와 기타 모듈 유지. 비둘기12마리 전용 시퀀스 재바인딩.
- 새 프로세스에서 크기/개수/재질 연결/비둘기 이동 검사 통과(verification.json). 실제 플레이·성능 측정 미실시.
- Tripo 잎/남은 구조의 미세 탄젠트 경고가 있어 최종 품질 보정 대상. 외형 승인 대기이며 기존 Layout맵은 유지.
- 실제 SM6 Unreal 캡처 완료: unreal_review.png, exposure_render_verification.json screenshot=true. 화면에서 기둥 표면 변화/외부 수목 교체 확인. 기존 매끈한 기단·보와 새 풍화 기둥의 이질감, 뾰족한 나뭇잎, 배경 수관 높이/밀도 부족, 기존 관목 반복은 후속 개선 항목.
