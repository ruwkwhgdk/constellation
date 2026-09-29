from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,zipfile,hashlib
R=Path(__file__).resolve().parent;O=R/'ContourRepair';D=O/'Delivery'
report=json.loads((D/'validation.json').read_text());assert report['data_checks_pass']
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',30)
canvas=Image.new('RGB',(1800,960),(235,235,235));draw=ImageDraw.Draw(canvas)
for i,(path,label) in enumerate([(R/'BoundaryLocal/renders/eye.png','이전 — BoundaryLocal'),(D/'renders/eye.png','수정 — ContourRepair')]):
 im=Image.open(path).convert('RGB').resize((900,900),Image.Resampling.LANCZOS);canvas.paste(im,(i*900,60));draw.text((i*900+24,12),label,font=font,fill=(25,25,25))
canvas.save(D/'renders/comparison.png')
readme=f'''# Heroine — 표시 부위 국소 보정

검토 파일: Heroine_ContourRepair.blend
교환 파일: Heroine_ContourRepair.fbx
비교 이미지: renders/comparison.png (좌: 이전, 우: 수정)

## 변경 내용
- 원래 눈썹의 색과 농담을 표면에서 재투영해 보존하고, 눈썹 아래 접힌 피부 면을 국소적으로 다시 연결했습니다.
- 눈 안쪽에 겹친 피부 면 78개를 제거했습니다. 뒤에 피부 표면이 있는 면을 대상으로 했습니다.
- 속눈썹 끝과 볼 옆 머리카락의 국소 형태를 다듬었습니다.
- 표시된 머리카락의 밝은 색 번짐 및 볼 위의 검은 색 번짐을 해당 UV 영역에서 보정했습니다.
- 아래 눈꺼풀 피부 띠의 안쪽 끝이 피부를 뚫고 나오지 않도록 깊이를 조정했습니다.

## 검증
- 홍채, 흰자, 아래 눈꺼풀 선 등 보호 대상 별도 메시의 정점/면/UV 일치 확인.
- 정면 확대, 얼굴 전체, 양쪽 사선 렌더 포함.
- FBX 재입력: {report['fbx_triangles']:,} triangles, 누락 이미지 없음.
- validation.json의 data_checks_pass는 데이터 검사 결과이며 미술적 완성도를 의미하지 않습니다.

기존 원본 및 Unreal 캐릭터 리소스는 교체하지 않았습니다. 이번 파일은 경계 국소 보정본입니다.
'''
(D/'README_KO.md').write_text(readme,encoding='utf-8')
files=[p for p in D.rglob('*') if p.is_file() and p.suffix not in ['.blend1']]
manifest={str(p.relative_to(D)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(D/'sha256.json').write_text(json.dumps(manifest,indent=2))
archive=R/'Heroine_ContourRepair_Package.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in D.rglob('*'):
  if p.is_file() and p.suffix!='.blend1':z.write(p,p.relative_to(D))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'package':str(archive),'bytes':archive.stat().st_size,'triangles':report['fbx_triangles'],'checks_pass':report['data_checks_pass']},ensure_ascii=False))
