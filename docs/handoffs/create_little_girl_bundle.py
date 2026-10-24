from pathlib import Path
import json, hashlib, zipfile, re
root=Path('C:/Users/User/Documents/UnrealProjects/Constellation')
base=root/'Saved/LittleGirlEyeRig/Inspections'
latest=base/'20261019_ForeheadBoundary_01'
fallback=base/'20261019_SideScalp_01'
out=root/'Saved/Handoffs/LittleGirl_AI_Handoff_2026-10-19.zip'
out.parent.mkdir(parents=True,exist_ok=True)
assert not out.exists(), 'Refuse overwrite of existing handoff'
entries={}
def add(path,name):
    path=Path(path)
    assert path.is_file(),str(path)
    assert name not in entries,name
    entries[name]=path.read_bytes()
add(root/'docs/handoffs/LittleGirl_3D_Handoff_2026-10-19.md','HANDOFF.md')
add(latest/'LittleGirl_ForeheadBoundary_CANDIDATE.blend','Models/Latest/LittleGirl_ForeheadBoundary_CANDIDATE.blend')
add(fallback/'LittleGirl_SideScalp_CANDIDATE.blend','Models/Fallback/LittleGirl_SideScalp_CANDIDATE.blend')
add(base/'20261019_LocalSegmentation_01/Separated_Ring_CANDIDATE.glb','Models/Original/Separated_Ring_CANDIDATE.glb')
add('C:/Users/User/Desktop/Portfolio/Project Constellation/illust/little_girl.png','References/little_girl_original.png')
add('C:/Users/User/AppData/Local/Temp/codex-clipboard-7ec9b789-63c9-43f3-81e5-bda0f401035b.png','References/target_concept_face.png')
add('C:/Users/User/AppData/Local/Temp/codex-clipboard-7bb5c4e5-9b8b-41ea-a72b-fae8b3a7ad68.png','References/target_original_model_face.png')
for p in sorted(latest.iterdir()):
    if p.suffix.lower() in {'.png','.json','.txt'}:
        add(p,'Inspections/Latest/'+p.name)
review=(latest/'review.html').read_text(encoding='utf-8').replace('href="LittleGirl_ForeheadBoundary_CANDIDATE.blend"','href="../../Models/Latest/LittleGirl_ForeheadBoundary_CANDIDATE.blend"')
entries['Inspections/Latest/review.html']=review.encode('utf-8')
for name in ['STATUS.txt','final_validation.json']:
    p=fallback/name
    if p.exists():add(p,'Inspections/Fallback/'+name)
add(root/'docs/handoffs/bundle_dependencies.json','Textures/dependency_inventory.json')
entries['Textures/README.txt']=('두 .blend 파일에는 각각 177개의 텍스처 이미지가 내장되어 있습니다.\n외부 텍스처, 연결 라이브러리, 외부 파일 의존성은 Blender에서 검출되지 않았습니다.\n따라서 경로 재연결 없이 모델을 열 수 있으며, 별도 텍스처 복사본은 중복 용량을 피하기 위해 만들지 않았습니다.\n필요하면 Blender의 File > External Data에서 내장 데이터를 추출할 수 있습니다.\n최신 이마의 Forehead_SampledSkin_DRAFT는 이미지 텍스처가 아닌 임시 단색 재질입니다.\n').encode('utf-8')
entries['START_HERE.md']='''# 소녀 캐릭터 AI 작업 전달 패키지

먼저 ZIP 전체를 한 폴더에 압축 해제하세요. 모델은 Blender 5.2.1 LTS로 저장되었습니다.

1. `HANDOFF.md`를 읽으세요. 목표·금지 조건·실패 사례·다음 작업이 있습니다.
2. `References/`의 최초 전신 원화와 목표 얼굴 두 장을 확인하세요. 실패한 검사 이미지를 목표로 삼지 마세요.
3. `Models/Latest/LittleGirl_ForeheadBoundary_CANDIDATE.blend`에서 이어갑니다.
4. `Models/Fallback/LittleGirl_SideScalp_CANDIDATE.blend`는 직전 복귀 기준이며 보존합니다.
5. `Models/Original/Separated_Ring_CANDIDATE.glb`는 AI 보완 전 고리 머리카락 분할 기준입니다.
6. `Inspections/Latest/review.html`을 브라우저로 열면 실제 모델의 전후 이미지를 볼 수 있습니다. before는 복귀 기준본, after는 최신 후보입니다. isolated는 머리카락 등을 숨긴 연결 구조 검사입니다.

현재는 부분 완료본입니다. 넓은 이마 단차, 임시 단색 피부 재질, 눈 외관 개선과 리깅·Unreal 검증이 남아 있습니다. 원래 눈매·눈 크기·눈썹·앞머리를 유지하세요.

## 텍스처

두 Blender 파일 각각에 텍스처 177개가 내장되어 있습니다. 외부 연결 파일이 없어 별도 다운로드나 로컬 경로 재설정은 필요하지 않습니다. `Textures/`에서 검사 목록을 확인할 수 있습니다.

## 문서 경로 해석

HANDOFF.md의 C:/ 경로는 제작 PC의 이력입니다. 이 패키지에서는 위 상대 경로를 사용하세요. 문서가 언급한 모든 과거 실험·게임 프로젝트·스킬을 포함한 패키지는 아닙니다. 최신 모델과 복귀본, 직접 비교 가능한 분할 기준, 원화, 최신 검사 자료를 포함합니다. 다른 AI는 자신이 사용할 Blender 도구와 작업 환경을 설정해야 합니다.

검사 JSON은 원래 실행 기록을 그대로 보존했으므로 제작 PC 경로가 남아 있습니다. 구조 검사 통과는 외관이나 게임 적용 완료를 의미하지 않습니다. `rejected_bake_transfer.json`은 폐기 실험 기록입니다.

원본 모델 파일은 바이트 그대로 포함했습니다. `MANIFEST_SHA256.json`으로 압축 해제 후 파일 무결성을 확인할 수 있습니다. 이 패키지는 사용자가 다른 AI에 전달하기 위한 자료이며 자동 업로드는 하지 않았습니다.
'''.encode('utf-8')
manifest=[{'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in sorted(entries.items())]
entries['MANIFEST_SHA256.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,data in sorted(entries.items()):z.writestr(name,data)
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    for item in manifest:
        assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256'],item['path']
    for link in re.findall(r'(?:src|href)="([^"]+)"',review):
        import posixpath
        assert posixpath.normpath('Inspections/Latest/'+link) in z.namelist(),link
result={'zip':str(out),'bytes':out.stat().st_size,'files':len(entries),'crc_check':'passed','all_manifest_hashes':'passed','review_links':'passed','sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(out.parent/'LittleGirl_AI_Handoff_2026-10-19.validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
