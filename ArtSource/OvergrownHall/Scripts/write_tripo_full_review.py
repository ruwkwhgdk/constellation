from pathlib import Path
import json,html
p=Path(__file__).resolve().parents[1]/'TripoReplacement/v002'
rows=json.loads((p/'kit_manifest.json').read_text())
cards=''.join('<article><h3>'+r['id']+' '+html.escape(r['name'])+'</h3><img loading="lazy" src="'+r['id']+'_'+r['name']+'/prepared.png"><p>'+str(r['triangles'])+' triangles · '+str([round(d*100,1) for d in r['dimensions_m']])+' cm</p><a href="'+r['id']+'_'+r['name']+'/prepared.blend">Blender 보정본</a></article>' for r in rows)
body='''<!doctype html><meta charset="utf-8"><title>Overgrown Hall · 전체 Tripo 적용</title>
<style>body{font:17px/1.65 sans-serif;background:#172125;color:#eee;max-width:1400px;margin:40px auto;padding:0 24px}a{color:#9de3cf}img{width:100%;display:block}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}article{background:#243138;padding:16px;border-radius:12px}code{overflow-wrap:anywhere}small{color:#bcc}</style>
<h1>전체 환경 애셋 Tripo 교체</h1><p>새 19종을 보정·임포트하고 기존 Tripo 기둥·나무·비둘기와 조립했습니다. 물·광원·안개는 Unreal 효과로 유지합니다.</p>
<p>레벨: <code>/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull</code></p>
<h2>실제 Unreal 화면</h2><img src="unreal_full.png"><p>고정 카메라 렌더입니다. 캐릭터 플레이·성능 측정 결과와는 구분합니다.</p>
<div class="pair"><article><h2>교체 전</h2><img src="../v001/unreal_review.png"></article><article><h2>원화</h2><img src="../../References/source_scene.png"></article></div>
<h2>보정 내용</h2><p>측면 아치의 불필요한 문살 제거, 원형 창의 상부 반원 분리, 창살 장식 끝단 제거, 벤치 축 교정 및 180cm 폭 적용, 바닥의 별도 평탄 UCX 충돌, 지붕 패널 방향 보정을 적용했습니다. 표면 풍화 표현과 식생의 잎 두께는 Tripo 원본 특성이 남아 있습니다.</p>
<p>기존 시각용 메시의 잔존 여부·재질·치수·충돌·비둘기 시퀀스는 verification.json, 촬영 여부는 exposure_render_verification.json에서 확인할 수 있습니다. 미세 UV/탄젠트 경고, LOD·인스턴싱 최적화와 실제 플레이는 후속 검토 대상입니다.</p>
<h2>교체 모듈 19종</h2><div class="grid">'''+cards+'''</div><p><a href="verification.json">저장 레벨 검증</a> · <a href="kit_manifest.json">모듈 치수·폴리곤 보고서</a> · <a href="STATUS.md">제작 기록</a></p>'''
(p/'review.html').write_text(body,encoding='utf-8')
