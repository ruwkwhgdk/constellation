# Fab 애셋 조사 — 폐교(일본풍) + 동굴 그래픽 콘셉트

**목적**: AbandonedSchool 레벨(동굴에 잠식된 일본 폐교) 그래픽 개선을 위해 Fab 마켓플레이스에서 참고/도입 가능한 애셋 조사.
**조사 방식**: WebSearch/WebFetch로 Fab 리스팅 페이지를 원격 조회 (실제 다운로드/가격 확인은 하지 않음).
**⚠️ 가격 관련 제약**: Fab 가격은 페이지에서 JS로 동적 렌더링되어 원격 조회로는 정확한 금액을 가져오지 못했습니다. 아래 표의 "가격"란은 대부분 "확인 필요"입니다 — 실제 다운로드 전에 Fab 플러그인/웹에서 직접 확인 필요합니다. 무료 애셋만 자동 다운로드하고 유료는 검토 후 진행하는 기존 원칙을 유지해 주세요.

---

## 1. 폐교 / 일본 학교 건물 & 소품

| 애셋 | 내용 | 엔진 | 비고 |
|---|---|---|---|
| [HQ Abandoned School (Modular)](https://www.fab.com/listings/c14f03c3-ddf4-4919-84ad-435b39456077) | 교실 2, 화장실 2, 도서관, 체육관, 사물함 공간, 복도 — 7개 모듈러 실내 공간. 외부/내부 모두 접근 가능 | UE + Unity | 평점 4.9/5 (30개) — **이미 "폐허" 콘셉트라 별도 손상 작업이 적게 필요함. 기본 골격으로 가장 적합한 후보** |
| [Japanese School Collection - 5 Asset Packs, 234 assets](https://www.fab.com/listings/af6a2e21-41f7-49a0-9cde-8b9b0b1ce091) | 교실/교사라운지/체육관/카페테리아/학교 등 5개 팩, 234개 애셋, LOD 4단계, PBR | UE5+ (일부 UE4.20-4.27) | 소품 다양성 확보용 |
| [Japanese School - Mega Pack, 12 asset packs](https://www.fab.com/listings/93bd3af2-1edd-4a99-a4a7-dc4b7bda3c87) | 교실/교무실/체육관/카페테리아/컴퓨터실/과학실/음악실/보건실/화장실/도서관 등 12개 팩 통합 | UE + Unity | 가장 방대한 구성. 성능 위해 일부 룸 섀도우 캐스팅 기본 OFF |
| [Old Japanese School](https://www.fab.com/listings/ae507a8b-70f0-4b34-a8f3-e4f49e5ecad4) | 일본 초등학교풍 모듈러 벽/코너 다수 | UE | PBR, 오래된 느낌의 외관 전용 |
| [Japanese School Building - Modular Environment](https://www.fab.com/listings/78d5da22-c0bf-4518-8116-24de0dfb9f37) | 건물 외관/부지만: 복도·교실용 모듈러 벽, 바닥/지붕, 수목류. **교실 소품은 미포함** | UE | 평점 4.3/5(4). Realistic/Anime/Manga 태그 — 외관 전용으로 소품 팩과 조합 필요 |
| [Modular Japanese Classroom](https://www.fab.com/ja/listings/280beafb-304c-4a36-86ef-2a59573bb618) | 일본식 교실 모듈러 | UE | 상세 미확인 |
| [Japanese Classroom - Realistic Environment](https://www.fab.com/ja/listings/0899a9a3-e060-4c2e-b6c2-e8d6cd8e78e8) | 사실적 스타일 일본 교실 | UE | 상세 미확인 |
| [Japanese School Science Classroom](https://www.fab.com/listings/81d8b24b-3a26-4da2-b777-375b9e504c7b) / [Computer Classroom](https://www.fab.com/listings/61885aec-a419-4890-82d1-97271106989b) | 과학실/컴퓨터실 특화 소품 | UE | 특정 룸 디테일 보강용 |
| [Japanese School Interior Props - Asset Pack](https://www.fab.com/listings/528f18f0-592b-4cda-a09a-849b81b4026d) | 교실 표지판 152종, 신발장 9종(3스타일×5색), 좌석 7종, 배수판 5종, 쓰레기통(8텍스처), 선반 6종, 화이트보드 3종, 테이블 3종, AED함/배너 등 | UE | **일본 학교 특유의 디테일(신발장=げた箱 등) 보강에 매우 유용** |
| [Abandoned school](https://www.fab.com/listings/aed2a439-1c05-4359-ab17-c07486516ec0) | 2층 학교 건물 + 책상/의자/캐비닛/지구본/지도/도구/스토브/책 등 | UE5+ (Nanite/Lumen) | 소비에트풍 폐허 — 일본풍은 아니지만 "황폐함" 디테일 참고용 |
| [Forgotten Classroom Interior (900K Tris)](https://www.fab.com/listings/d1cadfb1-234c-4893-9922-b1a0c5e18b80) | 단일 폐교실 인테리어, 약 90만 트라이앵글 | UE5(Nanite 권장)/Unity(HDRP)/Blender | 단일 룸 고퀄 디테일용, Nanite 권장 |
| [School Hallway / 27 Assets](https://www.fab.com/listings/40455d32-b511-493b-a15a-e7d3d6a29356) | 복도 전용 27개 애셋 | UE | 복도 디테일 보강 |
| [School Desk and Chair](https://www.fab.com/listings/e79975dc-0623-4fed-b152-f90d8410e16b) | 책상+의자 단품 | UE | 단품 채우기용 |

**추천 조합**: `HQ Abandoned School (Modular)`을 기본 골격(이미 폐허 상태)으로 쓰고, `Japanese School Interior Props`로 일본 학교 특유 소품(신발장, 표지판)을 얹고, 부족한 룸은 `Japanese School Collection` 또는 `Mega Pack`에서 발췌하는 방식을 추천합니다. 다만 HQ Abandoned School은 일본풍이 아닐 수 있으니, 외관/실루엣은 `Japanese School Building - Modular Environment`(일본식 지붕/외관)를 참고해 텍스처/모듈만 차용하는 방법도 가능합니다.

---

## 2. 동굴(Cave) 환경

| 애셋 | 내용 | 엔진 | 비고 |
|---|---|---|---|
| [Luos's Modular Rocks & Caves](https://www.fab.com/listings/d3de37d9-a260-44ad-9e0f-b0693fe03ad4) | 모듈러 동굴 조각 79개 + 바위/소품 437개 = **총 516개 메시**, 4K Albedo/Roughness/Normal | UE | 평점 4.8/5(47) — **커뮤니티에서 가장 널리 쓰이는 동굴/바위 모듈러 키트 중 하나. 최우선 후보** |
| [Cave Environment Modular](https://www.fab.com/listings/b330fcca-671c-4ba6-b26c-38bab5e8a596) | 완전 모듈식 바위(이동/스케일/회전으로 동굴 조립) | UE | 평점 5.0/5(3, 표본 적음) |
| [Cave Stalactites & Wall Kit – Nanite-Ready](https://www.fab.com/listings/6d72a075-8a87-4add-b1df-a6e5664bd4c8) | 종유석/석순 + 모듈러 동굴 벽 23종, **Nanite+Lumen 지원(UE5.0+)** | UE5.0+ | 기존 프로젝트가 UE5.8 + Nanite 사용 중이므로 호환성 우수 |
| [Stalactites Cave Kit](https://www.fab.com/listings/23f40d93-769d-415e-b460-9f14e438e462) | 종유석 전용 키트 | UE | 상세 미확인 |
| [Cave Stalactite and Stalagmite Rock Pack](https://www.fab.com/listings/850f5254-b830-4a90-93fb-b8c3f439452b) | 종유석+석순 바위팩 | UE | 상세 미확인 |
| [Ruins / Cave Assets](https://www.fab.com/listings/b01a481c-acea-4357-987a-10bfb2b7e6db) | 폐허+동굴 혼합 애셋 | UE | 폐교→동굴 전환부에 적합할 수 있음 |
| [Ancient Modular Fantasy Cave](https://www.fab.com/listings/f114797f-1265-47e1-9c5d-45ae182ad49b) | 판타지풍 모듈러 동굴 | UE | 스타일이 사실적 폐교와 맞을지 확인 필요 |
| [Fantasy Cave Environment Set](https://www.fab.com/listings/73e0b9c2-e15e-409f-952e-59b038a57ad9) | 동굴 환경 세트 | UE | 상세 미확인 |
| [Procedural Cave Generator](https://www.fab.com/listings/0ffafd7c-bbc1-4c23-9ef7-97036be8a867) | 시드 기반 절차적 동굴 네트워크 생성 (블루프린트+C++ 클래스 포함) | UE | 클릭 몇 번으로 동굴 네트워크 생성 — **큰 동굴 구조를 빠르게 블록아웃할 때 유용** |
| [Destructible Cave Generator Lite](https://www.fab.com/listings/7c8ec064-1270-4edd-844e-082f5ba9201d) | 파괴 가능한 동굴 생성기 (라이트 버전) | UE | 무료/라이트 버전일 가능성 있음 — 확인 필요 |

**참고**: 이미 프로젝트에 자체 제작한 Cliff Rock 애셋(사암 절벽, Tier A/B 6종, `claude/cliff-rock-batch-generation-log.md` 참고)이 있으므로, Fab 동굴 키트는 이를 **보완**하는 용도(동굴 내부의 종유석/석순, 좁은 통로 모듈)로 쓰고 절벽 외관은 기존 자체 제작 에셋을 우선 활용하는 것을 추천합니다.

---

## 3. 분위기 / 디테일 (공통)

| 애셋 | 내용 | 엔진 | 비고 |
|---|---|---|---|
| [Vertex Paint Materials Vol.1](https://www.fab.com/listings/d83d9a6e-8eb0-46c7-b881-16b224a51d7d) | 버텍스 페인트로 Basic/**Moss**/Snow/Water 블렌딩 | UE | 기존 벽/바닥 머티리얼 위에 이끼를 손으로 칠하듯 입힐 때 유용 |
| [Moss Textures Pack 1](https://www.fab.com/listings/37396a8a-ae0c-4d4d-994b-c4456e0ba203) / [Realistic Materials - Moss 1](https://www.fab.com/listings/f3595c88-d049-4852-85cb-6454bb26a9dd) / [Moss Substance PBR](https://www.fab.com/listings/5cd5a8a2-89ce-4964-92d2-b372897e83be) | 이끼 텍스처/머티리얼 단품 | UE | 폐교 벽에 침식된 이끼 표현용 |
| [Procedural Moss & Snow](https://www.fab.com/listings/7f6707ca-fe3d-43c3-9809-f8a76f13bfa0) | 절차적 이끼/눈 생성 | UE | 대량 표면에 자동 적용 시 유용 |
| [Easy Atmos](https://www.fab.com/listings/a7333445-ba38-4a78-9eab-f51c14c9161a) | 낙엽/**먼지 모트**/벌레떼/스파크/연기/로컬 볼류메트릭 안개 — 블루프린트 하나로 제어 | UE | Mesh Distance Fields 필요. **폐교 실내 빛줄기 속 먼지 표현에 적합** |
| [Dust Box](https://www.fab.com/listings/eea0aa29-bbf9-4f26-9188-92b615bea487) | 먼지 구름/모트 + 표면 먼지 쌓임, 11개 프리셋 | UE | Easy Atmos와 유사 목적, 프리셋 비교 후 택1 |
| [Smoke & Fog VFX](https://www.fab.com/listings/bc9691f9-1ed3-49ff-babe-f241262d9072) / [Fog and Smoke Volume - Niagara Fluids](https://www.fab.com/listings/6df0fdd6-2800-447a-9b1d-e59f7c04faca) | 안개/연기 Niagara VFX | UE | 동굴 습한 안개 표현용 |
| [Realistic modular Ivy](https://www.fab.com/listings/c72d9760-52ce-4d5d-9046-d85a31e76c8f) / [Ivy and Vines Pack 1](https://www.fab.com/listings/3c39a2b4-90ef-496e-bc7f-eed6a7017456) | 담쟁이덩굴 모듈 | UE | ※레벨에 이미 `Vine_Gate_00~08` 담쟁이 액터가 배치돼 있어 **추가 필요성은 낮음**. 다양성 보강용 참고만 |
| [Crazy Ivy - Realistic Ivy Generator Plugin](https://www.fab.com/listings/5cd4aa95-53ac-47fb-87f9-ffd4719c1156) | 에디터에서 절차적으로 담쟁이를 "자라게" 하는 플러그인 | UE | 기존 수동 배치 덩굴 외에 유기적으로 확산되는 느낌을 원하면 고려 |
| [Master Puddle Decal Pack](https://www.fab.com/listings/c80ee4ea-766b-4edf-9894-ab281532c63f) / [10 Water Puddle Ground Decal (UE5)](https://www.fab.com/listings/21444ef3-5a44-4c9e-ba6c-1256f09b2c4e) | 물웅덩이 데칼 | UE5 | 동굴수/빗물 유입 표현 |
| [120 Grunge, Damage, Leak Decal Pack](https://www.fab.com/listings/177de298-a6eb-45ba-a067-9c3d9ba65082) | 얼룩/손상/누수 데칼 120종 | UE | 벽/천장 물자국·낙서 흔적 |
| [60 Seamless Cracked Glass Textures](https://www.fab.com/listings/340805bc-b7e9-4f02-897d-fc9fb8b574a6) / [Broken Glass Material](https://www.fab.com/listings/4f594ccb-d223-4725-b6c7-6afa70cfe07c) | 깨진 유리 텍스처/머티리얼 | UE | 파손된 창문 표현 |
| [Old Vintage CRT TV Low-poly PBR](https://www.fab.com/listings/610632c0-9111-4ac2-9cf8-f33cc6501839) / [Retro CRT Television](https://www.fab.com/listings/00196519-6e95-40b1-bd20-5a71127134da) / [90s CRT TV 21/29 Inch](https://www.fab.com/listings/7283b159-a83c-46ba-b13f-1b18826f307c) | 구형 CRT TV 단품 | UE | 시청각실/교무실 소품, 콘셉트에 언급된 CRT 소품 후보 |

---

## 4. 종합 우선순위 추천

1. **바로 검토할 것 (핵심 3종)**
   - `Luos's Modular Rocks & Caves` — 동굴 골격 (평점/물량 검증됨)
   - `HQ Abandoned School (Modular)` 또는 `Japanese School Interior Props` — 학교 골격/디테일
   - `Cave Stalactites & Wall Kit (Nanite-Ready)` — UE5.8 Nanite 파이프라인과 궁합 좋음

2. **분위기 완성용**
   - `Vertex Paint Materials Vol.1` (이끼 블렌딩) + `Easy Atmos` 또는 `Dust Box` (먼지/안개)

3. **디테일 마감용**
   - `Master Puddle Decal Pack`, `120 Grunge/Damage/Leak Decal Pack`, 깨진 유리 텍스처, CRT TV 단품

4. **덩굴은 이미 확보됨** — 추가 다운로드는 선택 사항

---

## 5. 다음 단계 제안

- 위 목록 중 **무료 애셋**은 Claude Code(언리얼 MCP 연결)가 Fab 플러그인을 통해 바로 다운로드/임포트하도록 넘기고, **유료 애셋**은 사용자 검토 후 진행하는 기존 원칙을 유지합니다.
- Fab에서 받은 `MaterialInstanceConstant`의 parent가 `None`으로 깨지는 기존 버그(AdvancedCopyPackages 실패)가 재발할 수 있으니, Claude Code 쪽에서 임포트 후 항상 parent 링크를 검증하는 절차를 포함하는 것을 권장합니다.
- 정확한 가격은 이 조사에서 확인하지 못했으므로, 다운로드 전 Fab에서 직접 확인이 필요합니다.
