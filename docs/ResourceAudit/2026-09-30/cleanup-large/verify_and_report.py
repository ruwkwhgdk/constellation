import collections,csv,datetime,html,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
result=json.loads((OUT/'deletion.json').read_text(encoding='utf-8'))
before=json.loads((OUT/'registry.json').read_text(encoding='utf-8'))['packages']
after=json.loads((OUT/'registry_after.json').read_text(encoding='utf-8'))['packages']
chosen={r['package'] for r in plan['entries']};paths={r['path'] for r in plan['entries']}
assert result['cleanup_success'] and set(result['deleted'])==chosen and not result['remaining']
assert not chosen & set(after)
assert set(before)-set(after)==chosen,sorted((set(before)-set(after))-chosen)
outside_refs={p:sorted(set(v['dependencies'])&chosen) for p,v in after.items() if set(v['dependencies'])&chosen}
assert not outside_refs,outside_refs
changed=[];missing=[]
for path,baseline in plan['asset_baseline'].items():
    f=ROOT/path
    if path in paths:
        assert not f.exists(),path
    elif not f.exists():missing.append(path)
    else:
        st=f.stat()
        if st.st_size!=baseline['bytes'] or st.st_mtime_ns!=baseline['mtime_ns']:changed.append(path)
assert not missing,missing
assert all(p in {'Content/Levels/L_StartIsland.umap','Content/Environment/StairwellModular/Scene/Maps/L_Stairwell_PlayScale2.umap','Content/Environment/SubwayEntrance/Materials/M_SE_TunnelGuide.uasset','Content/Environment/SubwayEntrance/Materials/M_SE_TunnelGuide_Exterior.uasset','Content/Environment/SubwayEntrance/Meshes/SM_SE_ExteriorDarkTunnel.uasset','Content/Environment/SubwayEntrance/Meshes/SM_SE_InteriorDarkTunnel.uasset'} for p in changed),changed
maps=[p for p,v in before.items() if 'World' in v['classes']]
assert all(p in after for p in maps)
by=collections.defaultdict(lambda:{'count':0,'bytes':0})
for r in plan['entries']:
    key=r['package'].rsplit('/',1)[0];by[key]['count']+=1;by[key]['bytes']+=r['bytes']
report={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'deleted_packages':len(chosen),'deleted_bytes':result['deleted_bytes'],'before_packages':len(before),'after_packages':len(after),'outside_references_to_deleted':outside_refs,'unexpected_missing_files':missing,'concurrent_subway_asset_changes_observed':changed,'unchanged_retained_files':len(plan['asset_baseline'])-len(paths)-len(changed),'filesystem_fallback_count':len(result['filesystem_fallback']),'preserved_maps':len(maps),'new_packages_during_operation':sorted(set(after)-set(before)),'local_lfs_recovery_verified':True,'recovery_head':plan['head'],'groups':dict(by),'limitations':['Saved packages and registry were validated; no full cook or in-game playtest.','Freed Content bytes exclude DDC/cache growth and preserved Git LFS history.','Existing interactive editor was left running; unsaved in-memory edits were not inspected.']}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
dest=ROOT/'docs/ResourceAudit/2026-09-30/cleanup-large';dest.mkdir(parents=True,exist_ok=True)
for name in ['plan.json','delete_manifest.csv','deletion.json','verification.json','prepare.py','delete_unreal.py','verify_and_report.py','retry_remaining.py','filesystem_fallback.json','deletion_attempt1.json']:
    shutil.copy2(OUT/name,dest/name)
old=ROOT/'docs/ResourceAudit/2026-09-30'
old_rows=list(csv.DictReader((old/'unused_candidates.csv').open(encoding='utf-8-sig')))
remaining=[r for r in old_rows if r['package'] not in chosen]
with (dest/'remaining_candidates.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(old_rows[0]));w.writeheader();w.writerows(remaining)
parts=['<!doctype html><html lang="ko"><meta charset="utf-8"><title>대용량 미사용 에셋 정리 결과</title><style>body{font:16px/1.7 system-ui;max-width:1100px;margin:40px auto;padding:0 24px;color:#17243b}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:9px;text-align:left;overflow-wrap:anywhere}a{color:#1655aa}</style><h1>대용량 미사용 에셋 정리 결과</h1>',f'<p>{report["verified_utc"]}</p><p><b>{len(chosen)}개 패키지 삭제 · Content {result["deleted_bytes"]/1024**2:.2f} MiB 감소</b></p><p>Unreal Asset Registry를 새로 검사한 뒤 정확한 목록만 Unreal EditorAssetLibrary API로 삭제했습니다. 230개는 API로 파일까지 삭제됐고, 사운드/텍스처 2개는 API 재시도 성공 후에도 파일이 남아 참조 0·원본 해시·Git LFS 복구본을 확인하고 정확한 두 파일만 삭제했습니다. 첫 사운드 실패는 같은 삭제 묶음의 SoundCue가 메모리에서 참조하던 문제였습니다. 후보 폴더 전체를 삭제하지 않았으며 사용 중인 Bicycle 메시 등은 유지했습니다.</p><h2>삭제 목록 요약</h2><table><tr><th>폴더</th><th>패키지</th><th>MiB</th></tr>']
for p,v in sorted(by.items(),key=lambda kv:-kv[1]['bytes']):parts.append(f'<tr><td>{html.escape(p)}</td><td>{v["count"]}</td><td>{v["bytes"]/1024**2:.2f}</td></tr>')
parts+=['</table><h2>검증</h2>',f'<ul><li>최신 삭제 전 패키지 {len(before)}개 → 삭제 후 {len(after)}개.</li><li>별도 Unreal 프로세스의 전체 참조 재검색: 삭제 항목을 참조하는 잔존 패키지 0개.</li><li>기존 맵 {len(maps)}개 유지. 나머지 에셋 파일 누락 0개. 별도 지하철 작업으로 보이는 6개 에셋의 크기·수정시간 변경이 관측됐으며 해당 변경을 되돌리지 않았습니다. 그 외 보존 파일의 크기·수정시간은 동일합니다.</li><li>Environment 채택 키트·캐릭터 원본·원본 제작 파일은 이번 삭제 대상에서 제외했습니다. 동시 지하철 수정의 현재 저장본을 기준으로 삭제 대상 참조가 없는지 재검증했습니다.</li><li>전체 패키징/실제 플레이 검증은 수행하지 않았습니다. 열려 있던 에디터와 미저장 작업에는 접근하지 않았습니다.</li></ul><h2>복구와 잔여 후보</h2>',f'<p>삭제 전 232개 모두 Git HEAD <code>{plan["head"]}</code>의 LFS 원본과 SHA-256이 일치하고 로컬 LFS 오브젝트가 정상임을 확인했습니다. Git 이력과 LFS 원본은 유지했으며 새 대용량 백업을 만들지 않았습니다. Content 감소량과 디스크 전체의 순감소량은 다릅니다. 검사 과정에서 생성된 DDC/Registry 캐시는 포함하지 않은 수치입니다.</p>',f'<p>기존 미사용 후보 중 {len(remaining)}개, {sum(int(r["bytes"]) for r in remaining)/1024**2:.2f} MiB가 남았습니다. 부모 없는 외부 액터 47개는 이번 범위에서 제외했습니다. 캐시·원본 제작 파일도 제거하지 않았습니다.</p>','<p><a href="delete_manifest.csv">정확한 삭제 목록·해시</a> · <a href="verification.json">검증 결과</a> · <a href="remaining_candidates.csv">남은 후보</a> · <a href="plan.json">복구 기준·삭제 전 상태</a></p></html>']
(dest/'report.html').write_text(''.join(parts),encoding='utf-8')
# Keep the historical audit intact and point readers to the completed cleanup.
old_report=old/'report.html';text=old_report.read_text(encoding='utf-8')
banner='<p style="padding:16px;background:#e6f5ed"><b>후속 정리 완료:</b> 이 페이지는 삭제 전 감사 기록입니다. <a href="cleanup-large/report.html">232개·514.44 MiB 삭제 결과 및 잔여 후보 보기</a></p>'
if 'cleanup-large/report.html' not in text:text=text.replace('<h1>Constellation 리소스 전역 검사</h1>','<h1>Constellation 리소스 전역 검사</h1>'+banner)
old_report.write_text(text,encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='groups'},ensure_ascii=False,indent=2))
print('Remaining candidates:',len(remaining),sum(int(r['bytes']) for r in remaining)/1024**2,'MiB')
