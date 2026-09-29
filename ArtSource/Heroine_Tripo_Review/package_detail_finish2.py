import json,zipfile,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
R=Path(__file__).resolve().parent;O=R/'DetailFinish2';D=O/'Delivery';v=json.loads((D/'validation.json').read_text());assert v['pass'],v
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',27)
for label,before,after in [('eye',R/'DetailFinish/Delivery/renders/eye.png',D/'renders/eye.png'),('collar',R/'DetailFinish/Delivery/renders/collar.png',D/'renders/collar.png'),('skirt',R/'DetailFinish/Delivery/renders/skirt.png',D/'renders/skirt.png'),('back',R/'NeutralInspection/renders/head_back.png',D/'renders/head_back.png')]:
 canvas=Image.new('RGB',(2000,1050),(26,28,34));draw=ImageDraw.Draw(canvas)
 for j,p in enumerate([before,after]):canvas.paste(Image.open(p).convert('RGB').resize((1000,1000)),(j*1000,50));draw.text((j*1000+20,10),'BEFORE' if j==0 else 'AFTER',font=font,fill='white')
 canvas.save(D/(label+'_comparison.png'))
protected={}
for name in ['T_Brow_SurfacePreserved','T_Ruby_Iris_Refined']:
 a=R/'DetailFinish/Delivery/textures'/(name+'.png');b=D/'textures'/(name+'.png')
 protected[name]=a.exists() and b.exists() and Image.open(a).convert('RGBA').tobytes()==Image.open(b).convert('RGBA').tobytes()
(D/'protected_texture_validation.json').write_text(json.dumps(protected,indent=2));assert all(protected.values()),protected
for name in ['texture_changes.json','pinhem_changes.json','geometry_changes.json','eyelid_patch_changes.json','collar_edge_changes.json']:
 shutil.copy2(O/name,D/name)
report=f'''# Heroine 추가 보정본

기준 파일: DetailFinish/Delivery/Heroine_DetailFinish.blend
최종 파일: Heroine_DetailFinish2.blend / Heroine_DetailFinish2.fbx
삼각형: {v['triangles']:,}개

## 적용한 수정

- 리본의 실제 분리 메시 조각을 기준으로 가장자리·끝·매듭 아래의 밝은 색 오염을 보정했습니다. 줄무늬와 기존 주름은 유지했습니다.
- 흰 칼라 바깥 끝에 남은 베이지색 번짐을 실제 앞면의 좁은 범위 안에서 추가 보정했습니다.
- 은색 머리핀 내부의 깨진 듯한 어두운 흔적을 인접한 은색으로 국소 복원했습니다. 보라색 핀 디자인을 교체하지 않았습니다.
- 위 눈꺼풀의 좁은 경계 구역에 기존 텍스처를 고해상도로 옮기고, 피부와 속눈썹의 연결선만 정리했습니다. 기존 두꺼운 속눈썹 농담을 유지했습니다. 이 구역에만 별도 재질과 UV를 사용합니다.
- 아래 눈꺼풀 연결 띠를 기존 눈 윤곽과 볼 표면에 맞추고, 피부와 닿는 끝의 색·음영 차이를 줄였습니다. 홍채·흰자·아이라인 메시와 무표정 입은 유지했습니다.
- 치마 밑단의 낮은 채도 얼룩을 보정하고 끝의 작은 요철을 완화했습니다. 체크 무늬와 주름 전체를 다시 만들지 않았습니다.
- 포켓 끝의 열린 작은 경계 두 곳에 면을 보충하고 주변 모서리를 다듬었습니다.
- 뒷머리의 가닥 시작점 접합, 짧은 검은 흔적과 작은 면의 꺾임을 국소 보정했습니다. 가닥 사이의 긴 틈은 보존했습니다.

## 보존 및 검증

- 이전 보정본의 파일 해시 유지.
- 홍채, 흰자, 아이라인, 반대쪽 아래 눈꺼풀 및 팔찌 메시 유지.
- 입 주변 정점 유지: 무표정과 입꼬리 위치를 바꾸지 않았습니다.
- 기존 본체 UV는 눈꺼풀의 명시된 패치 이외 영역에서 유지했습니다. 포켓에는 새 면 두 개를 추가했습니다.
- 원본 눈썹·홍채 텍스처의 픽셀 동일성 확인.
- FBX 재가져오기 후 삼각형 수 일치, 이미지 누락 0개.
- 정면·양쪽 사선·전신 앞뒤·눈/리본/치마/뒷머리 확대 렌더 검토.

## 작업 범위와 한계

아래 눈 주변의 기존 피부 면을 삭제하는 시험안은 빈틈을 만들어 폐기했습니다. 전달본에는 그 삭제를 적용하지 않았습니다. 연결 띠를 맞추는 보정안을 사용했습니다.

이 파일은 정적 외형 보정본입니다. 극단적인 근접 시점에서의 모든 미세 요철 제거, 얼굴 전체 리토폴로지, 어깨의 큰 접합 재구성, 손톱·관절 재조형, 전체 메시의 리깅용 정리는 완료됐다고 판단하지 않았습니다. 검사 통과는 파일 및 보호 영역 보존에 대한 검증이며 상용 품질 전체에 대한 보증은 아닙니다.

## 애니메이션 제작

리깅 후 대기·걷기·달리기·회피·공격 등의 키프레임 동작을 제작하거나, 기존 모션을 리타기팅하고 보정할 수 있습니다. 발 접지, 루프 연결, 루트 모션을 확인하고 Unreal용으로 내보낼 수 있습니다. 이 모델에는 먼저 뼈대·스킨 웨이트와 어깨·팔꿈치·무릎 등의 변형 검증이 필요합니다. 이번에는 애니메이션이나 리깅을 새로 만들지 않았습니다.
'''
(D/'Changes_KO.md').write_text(report,encoding='utf-8')
with zipfile.ZipFile(R/'Heroine_DetailFinish2_Package.zip','w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for p in D.rglob('*'):
  if p.is_file() and not any(part.endswith('.fbm') for part in p.relative_to(D).parts):z.write(p,'Heroine_DetailFinish2/'+str(p.relative_to(D)))
print('PACKAGE_COMPLETE',v,protected)
