from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,shutil,zipfile
R=Path(__file__).resolve().parent;O=R/'DetailFinish';D=O/'Delivery'
validation=json.loads((D/'validation.json').read_text());assert validation['pass'],validation
for n in ['collar','skirt','shoes']:
 shutil.copy2(O/'renders'/f'{n}.png',D/'renders'/f'{n}.png')
for n in ['stage1.json','texture_changes.json','boundary_changes.json','fit_changes.json','microshape_changes.json']:
 shutil.copy2(O/n,D/n)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',23)
pairs=[('Eye',R/'NeutralInspection/renders/eye.png',D/'renders/eye.png'),('Bracelet',R/'NeutralInspection/renders/hand_top.png',D/'renders/hand_top.png'),('Ankle material',R/'NeutralInspection/renders/shoes.png',D/'renders/shoes.png'),('Skirt hem',R/'NeutralInspection/renders/skirt.png',D/'renders/skirt.png')]
sheet=Image.new('RGB',(1600,1750),(25,27,32));draw=ImageDraw.Draw(sheet)
for i,(label,a,b) in enumerate(pairs):
 ox=(i%2)*800;oy=(i//2)*875
 draw.text((ox+15,oy+10),label,fill='white',font=font)
 for j,p in enumerate([a,b]):
  im=Image.open(p).convert('RGB');im.thumbnail((790,390));sheet.paste(im,(ox+(800-im.width)//2,oy+55+j*405));draw.text((ox+15,oy+60+j*405),'BEFORE' if j==0 else 'AFTER',fill='white',font=font)
sheet.save(D/'comparison.png')
eye=Image.new('RGB',(2000,1040),(25,27,32));ed=ImageDraw.Draw(eye)
for j,p in enumerate([R/'NeutralInspection/renders/eye.png',D/'renders/eye.png']):
 eye.paste(Image.open(p).convert('RGB').resize((1000,1000)),(1000*j,40));ed.text((1000*j+20,8),'BEFORE' if j==0 else 'AFTER',font=font,fill='white')
eye.save(D/'eye_comparison.png')
report='''# Heroine 국소 디테일 보정 결과

이 파일은 NeutralExpression을 보존한 별도 보정본입니다. 원본 눈·눈썹 디자인과 무표정을 유지하는 범위에서 작업했습니다. Unreal 프로젝트의 플레이어 에셋은 교체하지 않았습니다.

## 이번에 적용한 보정

- 눈 위 피부 능선과 속눈썹 상단의 국소 면을 완화하고, 아래 눈꺼풀 피부 띠의 하단 깊이를 볼에 맞췄습니다. 홍채·흰자·아래 아이라인 메시를 그대로 유지했습니다.
- 입 양 끝 주변의 작은 각짐을 국소 완화했습니다. 입의 좌우 폭과 가장 바깥 입꼬리 위치를 유지했습니다.
- 칼라의 제한된 베이지색 번짐, 리본·치마 밑단의 일부 밝은 색 오염, 반대쪽 앞머리의 살색 흔적을 국소 보정했습니다. 기존 줄무늬·체크 무늬와 눈썹 텍스처는 유지했습니다.
- 팔찌 구슬을 실제 손목 단면에 맞춰 이동하고 크기를 조절해 손에 묻히던 현상을 줄였습니다. 구슬 표면의 각짐은 세분화로 완화했습니다.
- 발목 스타킹에 잘못 배정된 신발 재질을 재분류했습니다. 정면에서 보이던 밝은 사각형 반사는 사라졌습니다.
- 신발 반사를 소폭 완화하고, 손끝의 국소 각짐을 부드럽게 정리했습니다.

## 아직 남아 있는 부분

확대 화면의 눈꺼풀 접합선, 은색 머리핀 테두리, 리본의 일부 깨진 경계, 치마 밑단의 불균일한 두께는 완전히 해결된 상태가 아닙니다. 포켓 끝의 틈, 어깨의 직선적인 질감 전환, 뒷머리 홈과 복잡한 메시 연결도 추가적인 위치별 처리가 필요합니다. 이번 보정본을 모든 결함이 제거된 최종 상용 모델로 판단하지 않았습니다.

손톱·관절 재조형, 눈 디자인 교체, 의상 전체 재제작은 수행하지 않았습니다. 기존 인상을 크게 바꾸는 작업은 변경 범위를 먼저 설명할 대상입니다.

## 검증

- 원본 Blend 파일 SHA-256 유지.
- 본체 면 구성 및 UV 유지.
- 홍채·흰자·아래 아이라인 등 보호한 눈 메시 유지.
- 입 가장 바깥 양 끝 위치 유지.
- FBX 재가져오기 후 삼각형 수 일치 및 이미지 누락 0개. 정확한 수치는 validation.json에 기록했습니다.
- 정면·사선·전신 앞뒤·손등/손바닥 렌더 확인. 아직 리깅과 애니메이션 변형 검증은 하지 않았습니다.

`validation.json`은 데이터 보존 및 내보내기 검증입니다. 시각적 결함이 전부 없어졌다는 판정은 아닙니다.

## 파일

- Heroine_DetailFinish.blend: 작업용 원본, 텍스처 포함.
- Heroine_DetailFinish.fbx: 정적 모델 내보내기.
- textures/: 연결된 텍스처.
- renders/: 검토용 렌더.
- comparison.png: 동일 시점 보정 전후 비교.
'''
report+=f"\n최종 삼각형 수: **{validation['triangles']:,}개**.\n"
(D/'Changes_KO.md').write_text(report,encoding='utf-8')
with zipfile.ZipFile(R/'Heroine_DetailFinish_Package.zip','w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for p in D.rglob('*'):
  if p.is_file():z.write(p,'Heroine_DetailFinish/'+str(p.relative_to(D)))
print('PACKAGE_READY',validation)
