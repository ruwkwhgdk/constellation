import collections, csv, hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
OLD=ROOT/'docs/ResourceAudit/2026-09-30'
git=['git','-c','safe.directory='+ROOT.as_posix()]
def run(*args):return subprocess.check_output(git+list(args),cwd=ROOT)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
old={r['package']:r for r in csv.DictReader((OLD/'all_assets.csv').open(encoding='utf-8-sig'))}
current=json.loads((OUT/'registry.json').read_text(encoding='utf-8'))['packages']
folders=collections.Counter()
for r in old.values():
    if r['status'].startswith('unused_'):folders[r['package'].rsplit('/',1)[0]]+=int(r['bytes'])
big={p for p,b in folders.items() if b>=10*1024**2}
groups=[g for g in csv.DictReader((OLD/'candidate_groups.csv').open(encoding='utf-8-sig')) if any(p.rsplit('/',1)[0] in big for p in g['members'].split(';'))]
selected={p for g in groups for p in g['members'].split(';')}
assert len(selected)==232
assert all(old[p]['status'].startswith('unused_') for p in selected)
assert not any(p.startswith(('/Game/Environment/','/Game/__External','/Game/Resources/Characters/PC/')) for p in selected)
assert not any('World' in current.get(p,{}).get('classes',[]) for p in selected)
blocked={p:sorted(set(current.get(p,{}).get('referencers',[]))-selected-{p}) for p in selected}
blocked={p:v for p,v in blocked.items() if v or p not in current}
assert not blocked,blocked
# Each recovery record points at the existing HEAD and a verified local LFS object.
head=run('rev-parse','HEAD').decode().strip()
common=Path(run('rev-parse','--git-common-dir').decode().strip())
if not common.is_absolute():common=ROOT/common
media=common/'lfs/objects'
paths=[old[p]['path'] for p in sorted(selected)]
batch=subprocess.run(git+['cat-file','--batch'],input=''.join(head+':'+p+'\n' for p in paths).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT,check=True).stdout
cursor=0;entries=[]
for package,path in zip(sorted(selected),paths):
    end=batch.index(b'\n',cursor);header=batch[cursor:end].decode();cursor=end+1
    blob_oid,kind,length=header.split();assert kind=='blob',header
    blob=batch[cursor:cursor+int(length)];cursor+=int(length)+1
    f=ROOT/path;digest=sha(f)
    assert blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'),path
    pointer=dict(line.split(' ',1) for line in blob.decode().splitlines())
    oid=pointer['oid'].split(':')[1]
    assert digest==oid,(path,'differs from committed LFS object')
    obj=media/oid[:2]/oid[2:4]/oid
    assert obj.is_file() and obj.stat().st_size==f.stat().st_size and sha(obj)==oid,(path,'missing/corrupt local LFS recovery')
    assert f.stat().st_size==int(old[package]['bytes']),path
    entries.append({'package':package,'path':path,'bytes':f.stat().st_size,'sha256':digest,'lfs_oid':oid,'head_blob':blob_oid,'classes':current[package]['classes'],'previous_group':old[package]['group']})
baseline={}
for f in (ROOT/'Content').rglob('*'):
    if f.suffix.lower() in {'.uasset','.umap','.uexp','.ubulk'}:
        s=f.stat();baseline[f.relative_to(ROOT).as_posix()]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
plan={'head':head,'selection':'Whole unused connected components intersecting candidate folders >=10 MiB, from the prior audit; fresh full registry confirms zero outside referencers.', 'script_mentions_review':'tv_bp_probe.py only filters School_Blackboard_Arrow; finish_materials.py edits already placed LuosCaves static meshes, not Sounds; build_catalog.py reads historical inventory JSON. These broad prefix mentions are not dependencies on the selected candidates.', 'entries':entries,'asset_baseline':baseline,'before_registry':str(OUT/'registry.json'),'local_lfs_recovery_verified':True}
(OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'delete_manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(entries[0]));w.writeheader();w.writerows(entries)
print(json.dumps({'count':len(entries),'MiB':sum(x['bytes'] for x in entries)/1024**2,'current_packages':len(current),'outside_referencers':len(blocked),'all_files_match_HEAD_and_local_LFS':True,'head':head},indent=2))
