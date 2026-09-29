# 형태·모서리 보정

사용자 요청: 부드러운 애니메이션 배경 느낌을 유지하되 건축 윤곽의 뭉개짐과 불규칙한 형태를 수정.

## 원인과 처리

Tripo 소스의 면·모서리 자체가 울퉁불퉁하고 휘어져 있었다. v004는 잔무늬를 완화했지만 이 기하 형상을 고치지는 않았다. 전체 smoothing으로 건축을 더 둥글게 만들지 않고 아래처럼 분리했다.

- 16종 건축·가구: 승인된 Tripo 치수와 주요 실루엣을 참조해 새 토폴로지를 구성. 벽·기둥 평면, 일정한 창살 단면, 연속 아치, 슬랫 벤치, 지붕 트러스를 정리. 단순 원본 메시 변형이 아니라 **원본 기준 리토폴로지/재구성**이다.
- 모서리는 작은 2단 베벨과 분리된 면 노멀로 유지. 옛 UV에 대응하는 Tripo 노멀맵을 새 토폴로지에 잘못 적용하지 않는다.
- 원본 Tripo BaseColor는 새 UV로 선택→활성 메시 재투영 베이크. 미투영 픽셀은 유효 표면의 중간색으로 메움. 색은 v004 팔레트로 완화하지만 재질의 추가 mip blur는 제거.
- 5종 돌무더기/식생: 원래 UV·토폴로지와 큰 실루엣 유지. 국소 변형을 1.8–3.5cm 수준으로 제한한 smoothing. 새 둥근 수관이나 새 식물 종을 제작한 것은 아님.
- 건축 16종 경계 엣지 0, 전 모델 설정 삼각형 예산 내. 원본과 보정본 Blender 형태 렌더 포함.

## 현재 적용 대상

- 맵: `/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull`
- 새 메시: 같은 TripoFull/Meshes의 `SM_OH_Clean_{ID}_{Name}`.
- 건축 재질: TripoFull/CleanMaterials, 새 색 텍스처: TripoFull/CleanTextures.
- 식생·돌무더기는 기존 PaintedMaterials 유지.
- 배치 532개를 해당 ID의 보정 메시로 교체. 치수/피벗/카메라/광원은 유지.
- 원본 메시·텍스처·이전 렌더는 보존.

## 재생성과 검증

1. `tools/run-blender.ps1 -b -P ArtSource/OvergrownHall/Scripts/clean_tripo_shapes.py`.
   - 기존 v002 prepared.blend 및 v001/Pillar·Tree 원본을 읽음.
   - 각 폴더 inspection.json이 있으면 재생성 생략. 수정 재생성은 해당 ID 산출물을 별도로 보관한 뒤 해당 검사 파일을 갱신하는 관리 절차 필요.
2. Unreal Editor에서 `Content/Python/apply_clean_hall_shapes.py` 실행.
3. `Content/Python/verify_clean_hall_shapes.py`: 저장 맵 재로드, 532개 메시·재질, 21종 치수, 바닥/나무 단순 충돌, 기존 배치/시퀀서 검사.
4. 실제 Unreal 렌더 `unreal_clean.png`, 전후 및 부품별 검토 `review.html`.
5. 새 프로세스에서 `Content/Python/capture_clean_hall.py` 실행하면 애셋을 재생성하지 않고 저장 상태와 SM6 렌더를 확인한다. 로그: `Saved/CleanHallFresh.log`.

전체 재생성 순서: v002 반입 → v003 건축 배치 보정 → v004 따뜻한 색/조명 설정 → v005 형태 보정. **v005 이후 v004의 style_tripo_hall.py만 단독 실행하면 새 UV에 옛 텍스처가 연결되므로 하지 않는다.** 현재 재질 수정은 CleanMaterials와 이 단계의 재투영 색을 사용한다.

직접 플레이와 성능 측정은 별도이며 미실시. 원화의 배경 숲·반사 수면·구도는 이 보정에 포함하지 않았다.
