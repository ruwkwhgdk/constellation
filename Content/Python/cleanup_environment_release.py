"""Retire obsolete hall prototype packages, preserving final and external references."""
import unreal as u,json,runpy
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'ArtSource/OvergrownHall/Workflow'
runpy.run_path(str(root/'Content/Python/audit_environment_release.py'))
d=json.loads((out/'registry_audit.json').read_text());assets=d['assets'];closure=set(d['final_map_closure']);prefix='/Game/Environment/OvergrownHall/'
legacy=['Blockout/','Production/','Scene/','Bird/Clips/','Bird/Meshes/','TripoReplacement/Maps/','TripoReplacement/Sequences/']
candidates={p for p in assets if p.startswith(prefix) and p not in closure and (any(p.startswith(prefix+x) for x in legacy) or '/Bird/Tripo/Meshes/' in p)}
deletable=set(candidates)
while True:
    blocked={p for p in deletable if any(r!=p and r not in deletable for r in assets[p]['referencers'])}
    if not blocked:break
    deletable-=blocked
report=dict(candidates=sorted(candidates),protected=sorted(candidates-deletable),references={p:assets[p]['referencers'] for p in candidates},deleted=[],failed=[],retained_source_policy='TripoFull and TripoReplacement base kit/material inputs are retained for maintained derivation recipes; final closure and all external referencers protect assets.')
(out/'asset_cleanup.json').write_text(json.dumps(report,indent=2))
E=u.EditorAssetLibrary
for p in sorted(deletable,key=lambda p:(0 if '/Maps/' in p else 1,p)):
    assert p.startswith(prefix) and p not in closure
    ok=E.delete_asset(p)
    remains=any((root/'Content'/(p[6:]+ext)).exists() for ext in ['.uasset','.umap'])
    (report['deleted'] if ok and not remains else report['failed']).append(p)
    (out/'asset_cleanup.json').write_text(json.dumps(report,indent=2))
for p in closure:
    if p.startswith(prefix):assert E.does_asset_exist(p),p
for p in report['deleted']:assert not E.does_asset_exist(p),p
(out/'asset_cleanup.json').write_text(json.dumps(report,indent=2))
assert not report['failed'],report['failed']
u.log('ENVIRONMENT_CLEANUP_OK '+str(len(report['deleted'])))
