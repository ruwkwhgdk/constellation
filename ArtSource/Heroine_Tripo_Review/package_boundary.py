from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,zipfile
R=Path(__file__).resolve().parent;O=R/'BoundaryLocal'
v=json.loads((O/'validation.json').read_text());assert v['pass'],v
c=json.loads((O/'local_changes.json').read_text())
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',24)
sheet=Image.new('RGB',(1400,760),(30,30,33));d=ImageDraw.Draw(sheet)
for i,(p,label) in enumerate([(R/'DetailPreserved/renders/eye.png','수정 전 · 디테일 보존본'),(O/'renders/eye.png','표시 영역 국소 보정')]):
 sheet.paste(Image.open(p).convert('RGB').resize((700,700),Image.Resampling.LANCZOS),(i*700,60));d.text((i*700+20,16),label,font=font,fill='white')
sheet.save(O/'renders/comparison.png')
(O/'README.md').write_text(f'''# 붉게 표시된 얼굴 경계의 국소 보정

기준은 `DetailPreserved/Heroine_DetailPreserved.blend`입니다. 눈썹이나 눈꺼풀을 새로 디자인하지 않았습니다.

변경:
- 표시된 머리카락 영역의 밝고 따뜻한 색 번짐을 제한된 마스크로 줄였습니다.
- 앞머리 옆의 실제 피부 면에 잘못 그려진 어두운 색을 해당 좁은 영역 안에서 보정했습니다.
- 눈썹의 원래 색과 두께를 유지하며 표시한 범위에만 약한 텍스처 선명도 보정을 적용했습니다.
- 기존 눈 주변 면의 작은 요철을 깊이 방향으로 조정하고 아랫눈꺼풀 연결부 양 끝을 기존 볼 표면에 맞췄습니다.
- 안쪽 눈 구석의 분리된 작은 조각 {c['removed_corner_fragment_faces']}면을 제거했습니다. 중앙 속눈썹과 홍채는 교체하지 않았습니다.

본체의 정면 x/z 정점 좌표는 유지했습니다. 유지한 면들의 연결과 UV가 원본과 일치하는지 확인했습니다. 색 보정은 4096×4096 베이스 컬러에 베이크했고 FBX 재수입에서 {v['fbx_triangles']:,} 삼각형과 이미지 로딩을 확인했습니다.

BLEND/FBX에는 텍스처가 포함되어 있습니다. 별도 새 텍스처는 `textures/`에 있습니다. `renders/comparison.png`는 같은 구도·조명의 비교입니다.

확대 시 원래 생성 모델의 거친 선과 일부 경계는 남아 있습니다. 전체 재조형이나 원본 표현 교체를 하지 않은 국소 보정본입니다. 큰 재작업은 사용자에게 범위와 인상 변화를 설명하고 확인받은 뒤 진행합니다.
''',encoding='utf-8')
zpath=R/'Heroine_BoundaryLocal_Package.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
 for p in O.rglob('*'):
  if p.is_file() and p.suffix!='.blend1':z.write(p,p.relative_to(O))
with zipfile.ZipFile(zpath) as z:assert z.testzip() is None
print(zpath)
