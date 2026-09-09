# 한국 구도심 상가 B — 상세 재질·소품 검토본

승인된 v02 블록아웃을 기반으로 제작한 상세 아트 단계입니다. Unreal 최종 임포트 이전에 Blender 미리보기로 검토하는 산출물입니다.

## 구성
- `OldKoreanBuildingB_Detail.blend`: 재질과 소품을 포함한 조립본.
- `OldKoreanBuildingB_Detail_Assembly.fbx`: 전체 조립 FBX.
- `Modules/`: 구조·간판·소품 개별 FBX.
- `Textures/`: 벽돌·콘크리트·실내벽·바닥·계단의 BaseColor / Roughness / Normal, 총 15개 1024px PNG.
- `Previews/`: 외관, 정면·우측, 상점 근접 렌더.
- `assembly.json`: 모듈 배치, 미터 좌표, 회전, 스케일.
- `collision_policy.json`: 모듈별 사용자 충돌 개수. 충돌이 0개인 장식에는 자동 충돌을 만들지 않습니다.
- `material_manifest.json`: 텍스처 연결과 노멀맵 규칙.
- `verification.json`: 독립 FBX 재가져오기 검사.

## 추가한 디테일
붉은 벽돌과 줄눈, 미세한 표면 변화가 있는 콘크리트·실내 마감, 먼지가 낀 불투명 창유리, 한글 상호·안내 글씨, 녹색·주황색 줄무늬 차양, 세로 간판, 실외기와 팬 그릴·브래킷, 노출 배관·빗물 배수관, 빨간 의자 4개, 외벽 배전함, 실내 걸레받이·천장등 외형을 추가했습니다.

간판 글씨는 메시로 변환되어 있으며 Blender에서 폰트가 없어도 볼 수 있습니다. 재생성에는 Windows 맑은 고딕 Bold가 필요합니다. 사진에서 읽기 어려운 간판 문구와 세부 형상은 참고 이미지에 기반해 재구성했습니다.

## Unreal로 가져올 때
Blender 소스는 미터, FBX에는 센티미터 변환이 적용됩니다. 기존 블록아웃과 동일한 X / -Y / Z 매핑을 사용합니다. 일부 칸막이의 길이 방향 스케일을 포함한 `assembly.json`을 사용해야 합니다.

PBR 재질의 BaseColor는 sRGB, Roughness와 Normal은 비색상 데이터입니다. 노멀맵은 OpenGL +Y이며 Unreal에서는 Green Channel 반전이 필요합니다. FBX가 Blender 노드 연결을 모두 재현한다고 가정하지 말고 `material_manifest.json`에 따라 연결합니다. 사용하지 않는 자동 충돌은 제거하고 사용자 UCX를 유지합니다.

유리는 이번 아트 검토본에서 불투명한 먼지 낀 유리 표현입니다. 투명 유리, 실내 조명 배우, 문 상호작용, LOD 및 최종 엔진 성능 검증은 별도입니다. 이 파일은 구조 검증과 아트 검토용이며 Unreal 최종 임포트 완료를 뜻하지 않습니다.

## 재생성
Blender에서 `generate_detail.py`를 백그라운드 Python 스크립트로 실행합니다. 함께 제공한 `blockout_v02_source.py`에서 승인된 구조를 만들고 상세 재질·소품을 적용합니다. 재생성은 이 폴더의 출력 파일을 덮어쓰므로 수동 수정본은 별도로 저장합니다.
