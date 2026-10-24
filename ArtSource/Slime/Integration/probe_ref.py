import unreal as u,json
from pathlib import Path
P=Path(__file__).resolve().parent
sk=u.load_asset('/Game/Constellation/Characters/Enemies/Slime_Normal/SK_Slime_Normal')
rp=sk.get_reference_pose()
out={'bones':[str(x) for x in rp.get_bone_names()], 'doc':str(rp.get_ref_bone_pose.__doc__)}
out['poses']={str(b):str(rp.get_ref_bone_pose(b,u.AnimPoseSpaces.LOCAL)) for b in rp.get_bone_names()}
out['bounds']=str(u.load_asset('/Game/Constellation/Characters/Enemies/Slime_Normal/SKM_Slime_Normal').get_bounds())
out['transform_api']={n:str(getattr(u,n).__doc__) for n in ['MaterialExpressionTransformPosition','MaterialExpressionCustom','MaterialExpressionVertexColor']}
(P/'ref.json').write_text(json.dumps(out,indent=2))
