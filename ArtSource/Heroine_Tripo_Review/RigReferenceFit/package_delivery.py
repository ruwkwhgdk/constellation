from pathlib import Path
import zipfile,json
P=Path(__file__).resolve().parent
assert json.loads((P/'revision_audit.json').read_text())['pass']
assert json.loads((P/'unreal_update.json').read_text())['pass']
report=json.loads((P/'preview_result.json').read_text())
assert 'z: 128.057' in report['upperarm_l']
assert '/RigReferenceFit/' in report['asset_source']
target=P.parent/'Heroine_ReferenceFit_Package.zip'
files=[p for p in (P/'Delivery').rglob('*') if p.is_file() and p.suffix!='.blend1']
files += [P/n for n in ['comparison_relaxed.png','comparison_relaxed_side.png','unreal_reference_fit.png','revision_audit.json','unreal_update.json','preview_result.json']]
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
    for p in files:z.write(p,p.relative_to(P))
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
print(target, target.stat().st_size, 'bytes;',len(files),'files; CRC verified')
