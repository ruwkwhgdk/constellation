"""Offline classification from an Unreal read-only registry snapshot."""
import collections, csv, html, json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT/'registry.json').read_text(encoding='utf-8'))
G = DATA['packages']
errors = []
files = []
for base, dirs, names in os.walk(ROOT, onerror=lambda e: errors.append(str(e))):
    dirs[:] = [x for x in dirs if x != '.git' and not Path(base, x).is_symlink()]
    for name in names:
        f = Path(base, name)
        if OUT == f.parent or OUT in f.parents:
            continue
        try:
            st = f.stat()
            files.append({'path': f.relative_to(ROOT).as_posix(), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns})
        except OSError as e:
            errors.append(str(e))
disk = {'/Game/'+str(Path(f['path']).relative_to('Content').with_suffix('')).replace('\\','/'): f for f in files if f['path'].startswith('Content/') and Path(f['path']).suffix.lower() in ('.uasset','.umap')}
assert set(disk) == set(G), (set(disk)-set(G), set(G)-set(disk))
deps = {p: set(v['dependencies']) & set(G) for p,v in G.items()}
# Union the two registry query directions, conservatively retaining all edges.
for p,v in G.items():
    for ref in v['referencers']:
        if ref in deps:
            deps[ref].add(p)
refs = {p:set() for p in G}
for p,ds in deps.items():
    for d in ds:
        if d != p:
            refs[d].add(p)

def closure(roots):
    seen=set(); pending=list(roots)
    while pending:
        p=pending.pop()
        if p in seen or p not in G: continue
        seen.add(p); pending.extend(deps[p]-seen)
    return seen

evidence=collections.defaultdict(list)
runtime=set(); tooling=set(); script_mentions=set()
text_suffixes={'.py','.ps1','.cpp','.h','.ini','.json','.md','.txt','.csv','.uplugin','.uproject','.collection'}
path_pattern=re.compile(r'/Game/[A-Za-z0-9_\-/]+')
scan_roots={'Source','Config','tools','ArtSource','dev','docs','Tests','Build'}
for f in files:
    path=f['path']; pp=Path(path)
    if pp.suffix.lower() not in text_suffixes or f['bytes']>8*1024*1024: continue
    if path.split('/')[0] not in scan_roots and not path.startswith(('Content/Python/','Content/Collections/','Content/Developers/')): continue
    try: text=(ROOT/path).read_text(encoding='utf-8-sig',errors='replace')
    except OSError as e: errors.append(str(e)); continue
    for token in set(path_pattern.findall(text)):
        matches=[token] if token in G else [p for p in G if p.startswith(token.rstrip('/')+'/')]
        for p in matches:
            evidence[p].append(path)
            (runtime if path.startswith(('Source/','Config/')) else tooling).add(p)
            if pp.suffix.lower() in {'.py','.ps1'}: script_mentions.add(p)

maps={p for p in G if disk[p]['path'].endswith('.umap')}
external={p for p in G if p.startswith(('/Game/__ExternalActors__/','/Game/__ExternalObjects__/'))}
owner={p:'/Game/'+'/'.join(p.split('/')[3:-3]) for p in external}
orphan_external={p for p in external if owner[p] not in maps}
for p in external-orphan_external:
    deps[owner[p]].add(p)
    refs[p].add(owner[p])
# Source/reusable assets explicitly preserved by the project's maintained workflows.
protected_prefixes=['/Game/Environment/', '/Game/Resources/Characters/PC/player_heroine_new/', '/Game/Resources/Characters/CommonAnimation/', '/Game/Resources/Characters/PC/Player_Heroine/']
protected={p for p in G if any(p.startswith(x) for x in protected_prefixes)}
unknown={p for p in G if not G[p]['indexed_asset']}
cross_mount={p for p,v in G.items() if any(not x.startswith('/Game/') for x in v['referencers'])}
primary={p for p,v in G.items() if set(v['classes']) & {'PrimaryAssetLabel','PrimaryDataAsset','GameFeatureData'}}
runtime_closure=closure(runtime)
map_closure=closure(maps | runtime | (external-orphan_external))
protected_closure=closure(protected | unknown | cross_mount | primary)
keep=map_closure | protected_closure
candidates=set(G)-keep-external
# Remaining clusters include mutually referencing packages, not just zero-inbound leaves.
components=[]; remaining=set(candidates)
while remaining:
    todo=[min(remaining)]; group=set()
    while todo:
        p=todo.pop()
        if p in group or p not in candidates: continue
        group.add(p); todo.extend((deps[p]|refs[p]) & candidates-group)
    remaining-=group; components.append(group)
components.sort(key=lambda s: -sum(disk[p]['bytes'] for p in s))
group_id={p:f'C{i+1:04d}' for i,s in enumerate(components) for p in s}
labels={
 'runtime':'설정·코드 엔트리에서 참조',
 'map_only':'기타 맵·데모·검토맵에서 참조',
 'protected':'제작 소스·재사용·동적 로딩 보호',
 'orphan_external':'부모 맵 없는 외부 액터·객체',
 'unindexed':'Registry 미등재: 수동 확인',
 'unused_tooling':'맵 미사용·제작 스크립트 언급: 검토',
 'unused_leaf':'미사용 후보: 외부 참조 0',
 'unused_group':'미사용 후보: 후보끼리만 참조',
}
rows=[]
for p,v in G.items():
    if p in unknown: status='unindexed'
    elif p in orphan_external and p not in keep: status='orphan_external'
    elif p in runtime_closure: status='runtime'
    elif p in map_closure: status='map_only'
    elif p in protected_closure: status='protected'
    elif p in candidates: status='unused_tooling' if p in script_mentions else ('unused_leaf' if not refs[p] else 'unused_group')
    else: status='protected'
    rows.append({'status':status,'classification':labels[status],'package':p,'classes':';'.join(v['classes']), 'bytes':disk[p]['bytes'],'MiB':round(disk[p]['bytes']/1024**2,3),'path':disk[p]['path'],'group':group_id.get(p,''),'referencer_count':len(refs[p]),'referencers':';'.join(sorted(refs[p])),'dependencies':';'.join(sorted(deps[p])),'text_evidence':';'.join(sorted(set(evidence[p]))),'external_owner':owner.get(p,''),'indexed_asset':v['indexed_asset']})
rows.sort(key=lambda x:(x['status'],-x['bytes']))
def csv_write(name, items, fields=None):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(items[0])); w.writeheader(); w.writerows(items)
csv_write('all_assets.csv',rows)
csv_write('unused_candidates.csv',[x for x in rows if x['status'].startswith('unused_')],list(rows[0]))
csv_write('orphan_external_packages.csv',[x for x in rows if x['package'] in orphan_external],list(rows[0]))
csv_write('all_project_files.csv',files)
map_rows=[{'package':p,'runtime_reachable':p in runtime_closure,'production_or_tooling_protected':p in protected_closure,'bytes':disk[p]['bytes'],'dependencies_reachable':len(closure([p])),'text_evidence':';'.join(sorted(set(evidence[p])))} for p in sorted(maps)]
csv_write('maps.csv',map_rows)
group_rows=[{'group':f'C{i+1:04d}','packages':len(s),'bytes':sum(disk[p]['bytes'] for p in s),'sample':max(s,key=lambda p:disk[p]['bytes']),'members':';'.join(sorted(s))} for i,s in enumerate(components)]
csv_write('candidate_groups.csv',group_rows,['group','packages','bytes','sample','members'])
# Import source evidence is kept separately; no source art is declared unused.
imports=[]
for p,v in G.items():
    if v['tags']: imports.append({'package':p,'import_metadata':json.dumps(v['tags'],ensure_ascii=False)})
csv_write('import_sources.csv',imports,['package','import_metadata'])
totals=collections.defaultdict(lambda:{'count':0,'bytes':0})
folders=collections.defaultdict(lambda:{'count':0,'bytes':0})
candidate_folders=collections.defaultdict(lambda:{'count':0,'bytes':0})
for x in rows:
    t=totals[x['status']]; t['count']+=1;t['bytes']+=x['bytes']
    if x['status'].startswith('unused_'):
        key='/'.join(x['package'].split('/')[:4]); t=candidate_folders[key];t['count']+=1;t['bytes']+=x['bytes']
for x in files:
    key=x['path'].split('/')[0];t=folders[key];t['count']+=1;t['bytes']+=x['bytes']
cache_roots=('DerivedDataCache/','Intermediate/','.vs/')
cache=[x for x in files if x['path'].startswith(cache_roots)]
csv_write('rebuildable_cache_files.csv',cache,['path','bytes','mtime_ns'])
summary={'generated_utc':DATA['generated_utc'],'file_count':len(files),'file_bytes':sum(x['bytes'] for x in files),'asset_count':len(G),'asset_bytes':sum(x['bytes'] for x in rows),'maps':len(maps),'totals':dict(totals),'candidate_folders':dict(candidate_folders),'folders':dict(folders),'candidate_groups':len(components),'orphan_owner_maps':sorted({owner[p] for p in orphan_external}),'unindexed_packages':sorted(unknown),'read_errors':errors,'protected_prefixes':protected_prefixes,'runtime_root_count':len(runtime),'tooling_mention_count':len(tooling),'rebuildable_cache_bytes':sum(x['bytes'] for x in cache)}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
# Integrity gates: no candidate can be reached from any retained package.
assert not candidates & keep
assert not any(refs[p]-candidates-orphan_external for p in candidates)
assert sum(t['count'] for t in totals.values()) == len(disk)
assert len({r['package'] for r in rows}) == len(disk)

def size(n): return f'{n/1024**3:.2f} GiB' if n>=1024**3 else f'{n/1024**2:.1f} MiB'
def table(headers, records):
    return '<table><thead><tr>'+''.join('<th>'+html.escape(str(h))+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(c))+'</td>' for c in row)+'</tr>' for row in records)+'</tbody></table>'
parts=['<!doctype html><html lang="ko"><meta charset="utf-8"><title>Constellation 리소스 전역 검사</title><style>body{font:15px/1.65 system-ui,sans-serif;max-width:1300px;margin:40px auto;padding:0 24px;color:#17243b;background:#f7f9fc}h1,h2{line-height:1.3}table{border-collapse:collapse;width:100%;background:white;margin:18px 0;table-layout:auto}th,td{text-align:left;border-bottom:1px solid #ddd;padding:9px;overflow-wrap:anywhere}th{background:#e7eef9}a{color:#1655aa}small{color:#566}input,select{padding:9px;margin-right:12px}code{background:#e8edf3}</style><h1>Constellation 리소스 전역 검사</h1>',f'<p>{html.escape(DATA["generated_utc"])} · 디스크 저장본 기준 · 에셋 삭제/저장 없음</p>',f'<p>프로젝트 파일 {len(files):,}개 ({size(summary["file_bytes"])})를 목록화하고, Content 패키지 {len(G):,}개 ({size(summary["asset_bytes"])})와 맵 {len(maps)}개를 대조했습니다. .git 내부와 이번 보고서 폴더는 제외했습니다.</p>','<h2>판정 요약</h2>',table(['분류','패키지','디스크 크기'],[(labels[k],v['count'],size(v['bytes'])) for k,v in totals.items()]),'<p><b>미사용 후보는 삭제 승인 목록이 아닙니다.</b> 저장된 Registry 하드·소프트·관리·검색 참조, 모든 현존 맵, 설정/C++ 경로, 명시된 보존 규칙에서 도달하지 못한 패키지입니다. 제작 스크립트에서 언급되는 항목은 검토 분류로 분리했습니다. 과거 감사 JSON·백업 보고서에 이름이 있다는 사실은 사용 근거로 간주하지 않았습니다. 이름 조합 로딩, Blueprint 문자열, 외부 세이브/모드, 미저장 편집은 별도 확인해야 합니다.</p>','<h2>미사용 후보가 많은 폴더</h2>',table(['폴더','패키지','크기'],[(k,v['count'],size(v['bytes'])) for k,v in sorted(candidate_folders.items(),key=lambda kv:-kv[1]['bytes'])]),'<p>후보 중 ObjectRedirector는 이동 전 경로를 유지하는 연결 파일입니다. 일반 메시 삭제와 구분해 Unreal Redirector Fix Up 대상으로 검토하십시오. 원본 게임 캐릭터·애니메이션도 별도 보호했습니다.</p>','<h2>부모 맵이 없는 외부 패키지</h2>',f'<p>{len(orphan_external)}개. 부모 경로: {html.escape(", ".join(summary["orphan_owner_maps"]))}. World Partition/외부 액터 특성상 개별 참조 0만으로 판단하지 않았습니다. 부모 맵이 다른 브랜치/백업에서 복원될 계획인지 확인 후 묶음으로 검토하십시오. Registry 미등재 항목은 별도로 보류했습니다.</p>','<h2>전체 폴더 사용량</h2>',table(['폴더','파일','크기'],[(k,v['count'],size(v['bytes'])) for k,v in sorted(folders.items(),key=lambda kv:-kv[1]['bytes'])]),f'<p>DerivedDataCache, Intermediate, .vs의 재생성 가능한 캐시/빌드 중간 산출물: {size(summary["rebuildable_cache_bytes"])}. 에셋 미사용 용량과 별도입니다. Saved는 복구 백업·자동 저장을 포함하므로 통째로 정리 대상으로 분류하지 않았습니다. ArtSource/dev 및 FBX·Blend·원화·재반입 원본은 런타임 참조가 없다는 이유로 미사용 판정을 내리지 않았습니다.</p>','<h2>검사 범위와 보존 기준</h2>','<ul><li>Asset Registry 동기 검색과 /Game 강제 재검색. 직접 의존성과 역참조를 합친 뒤 전이 폐쇄를 계산했습니다. 파일 크기는 .uasset/.umap의 실제 크기이며 조리/패키징 크기나 GPU 메모리가 아닙니다.</li><li>기본 맵, 패키징 맵, C++ 경로, AlwaysCook 디렉터리는 실행 엔트리로 포함했습니다. 기타 27개 중 나머지 맵과 연결 리소스도 보존했습니다. 실행 엔트리 집합은 실제 플레이 계측이 아니며 주석/설정 리터럴을 보수적으로 포함합니다.</li><li>Environment 전체, 주인공 신규 캐릭터와 공용 애니메이션은 CURRENT/Workflow의 재사용·재생성 원칙으로 보호했습니다. 그 밖의 제작 스크립트의 리터럴 경로·폴더 언급은 별도 검토 표시로 남겼습니다. 과거 검사 보고서 언급만으로 사용 중 판정을 내리지 않았습니다.</li><li>프로젝트 Plugins 폴더는 없으며 엔진 설치 리소스는 삭제 조사 대상에서 제외했습니다. /Game 에셋을 참조하는 다른 마운트의 역참조는 보호 대상으로 반영했습니다.</li><li>원본 제작 파일은 전체 목록과 Import 메타데이터를 제공하지만 Blend 내부 링크 등 제작 도구 내부 의존성까지 전부 검증한 것은 아닙니다. 신규 원본 미사용 판정은 보류합니다.</li></ul>',f'<p>파일 읽기 오류: {len(errors)}개. Registry 미등재 패키지: {len(unknown)}개. '+html.escape('; '.join(sorted(unknown)))+'</p>','<h2>목록 다운로드</h2><ul>']
for f in ['unused_candidates.csv','all_assets.csv','candidate_groups.csv','orphan_external_packages.csv','maps.csv','all_project_files.csv','rebuildable_cache_files.csv','import_sources.csv','summary.json','registry.json']:
    parts.append(f'<li><a href="{f}">{f}</a></li>')
parts+=['</ul><h2>미사용 후보 검색</h2><input id="q" placeholder="이름 또는 경로 검색" style="width:60%"><p id="count"></p><div id="results"></div><script>const rows=',json.dumps([{k:x[k] for k in ['package','classification','MiB','group','classes']} for x in rows if x['status'].startswith('unused_')],ensure_ascii=False).replace('</',r'<\/'),';const q=document.getElementById("q"),box=document.getElementById("results");function render(){const r=rows.filter(x=>JSON.stringify(x).toLowerCase().includes(q.value.toLowerCase()));document.getElementById("count").textContent=r.length+"개 · 크기 내림차순";const t=document.createElement("table");for(const x of [{package:"패키지",classification:"판정",MiB:"MiB",group:"묶음",classes:"유형"},...r.sort((a,b)=>b.MiB-a.MiB)]){const tr=t.insertRow();for(const v of Object.values(x)){tr.insertCell().textContent=v}}box.replaceChildren(t)}q.addEventListener("input",render);render();</script></html>']
(OUT/'report.html').write_text(''.join(parts),encoding='utf-8')
print(json.dumps({'asset_count':len(G),'totals':dict(totals),'candidate_folders':dict(candidate_folders),'orphan_owner_maps':summary['orphan_owner_maps'],'read_errors':errors,'cache_bytes':summary['rebuildable_cache_bytes'],'checks':'coverage, classification partition, no retained inbound references: PASS'},ensure_ascii=False,indent=2))
