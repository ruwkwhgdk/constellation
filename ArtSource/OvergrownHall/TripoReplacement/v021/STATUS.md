# v021 · 폐허 실루엣과 비둘기

유지 맵의 측면 아치6개를 큰 비대칭 파손3변형으로 교체. 나머지2개는 유지하고8개 모두 차가운 슬레이트색 파생 재질 사용. 지붕 트러스3개는 하부 연결재의 일부가 끊긴 파생 메시로 교체. 닫힌 천장50개는 그대로이며 아래에 유지 Tripo 부러진 보를 재사용한 처진 부재6개 추가. 부재 바운드 최저 높이는700cm 초과, 충돌 없음.

비둘기28마리는 크기0.27–0.58로 변화를 확대하고 크림색의 밝은 실루엣 재질 적용. 실제 Sequencer 스케일 키를 수정했으며 위치 경로와 기존 Tripo 리깅·140개 애니메이션 섹션은 유지. 밝기에는 미술용 emissive750이 포함된다. 경로와 중심 간격은 v019와 동일하며 날개 충돌 검증은 아니다.

소스: `Scripts/build_hall_silhouette_finish.py` → 프로젝트 Blender 런처로 실행 → `Content/Python/finish_hall_silhouettes.py` → `capture_hall_silhouettes.py`.

모든 파생 메시 nonmanifold0. 아치484/668/1356삼각형, 트러스364삼각형. 처음 트러스 Boolean 실험의 바운드 이상은 수정했고 정상 외곽(12.67×0.22×2.00m)을 확인한 결과만 반입했다. `assets.json`, `baseline.json`, `applied.json`, `verification.json` 참고.

실제 렌더 `unreal_silhouettes.png`에서 정돈된 아치/삼각 트러스 반복이 줄어든 것을 확인. 아직 따뜻한 빛·식생 색면·수면의 밝은 연결이 부족해 이 단계에서는 시각적 성공으로 판정하지 않음. 플레이 미실행.
