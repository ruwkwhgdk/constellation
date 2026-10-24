import unreal as u,json
from pathlib import Path
P=Path(__file__).resolve().parent
exec(compile((P/'verify_assets.py').read_text(),str(P/'verify_assets.py'),'exec'),{'__file__':str(P/'verify_assets.py'),'__name__':'__main__'})
mesh=u.load_asset('/Game/Constellation/Characters/Enemies/Slime_Liquid/SKM_Slime_Liquid')
maps=json.loads((P/'replacement-report.json').read_text())['maps']+['/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool']
report={'maps':{},'success':False}
for path in maps:
 world=u.load_asset(path);assert world,path
 rows=[]
 for c in u.ObjectIterator(u.SkeletalMeshComponent):
  if not c.get_path_name().startswith(path+'.'):continue
  sk=c.get_editor_property('skeletal_mesh_asset')
  if sk and 'Slime' in sk.get_name():
   assert sk==mesh,(path,c.get_path_name(),str(sk))
   rows.append(c.get_path_name())
 report['maps'][path]=rows
assert sum(len(v) for v in report['maps'].values())>=10
assert u.load_asset('/Game/Constellation/Characters/Enemies/Slime_Liquid/AM_Slime_Liquid_Idle').get_play_length()==4
report['success']=True
(P/'saved-verification.json').write_text(json.dumps(report,indent=2))
exec(compile((P/'reference_audit.py').read_text(),str(P/'reference_audit.py'),'exec'),{'__file__':str(P/'reference_audit.py'),'__name__':'__main__'})
