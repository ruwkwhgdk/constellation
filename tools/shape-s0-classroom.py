"""Inspect current rock geometry/collision before producing isolated visual variants."""
import unreal as u,json,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/ShapePass_20261017'
E=u.EditorAssetLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
review=(R/'tools/review-s0-shape.py').read_text()
exec(review[review.index('rows=[];lights=[]'):review.index('cmd=u.SystemLibrary')])
(O/'baseline-actors.json').write_text(json.dumps(rows,indent=2));(O/'baseline-lights.json').write_text(json.dumps(lights,indent=2))
info={}
for name in dir(u):
 if name.startswith('GeometryScript') and any(x in name for x in ['MeshQueries','MeshBasicEdit','VectorList','MeshDeformers']):
  cls=getattr(u,name);info[name]={'doc':cls.__doc__,'methods':{n:getattr(cls,n).__doc__ for n in dir(cls) if any(x in n for x in ['vertex','perlin','noise'])}}
for i in [7,9,14]:
 mesh=E.load_asset('/Game/LuosCaves/Meshes/Props_Mesas/SM_LCave_P_Mesa_%02d'%i);assert mesh
 vals={'bounds':str(mesh.get_bounding_box())}
 for p in ['body_setup','complex_collision_mesh']:
  try:vals[p]=str(mesh.get_editor_property(p))
  except Exception as ex:vals[p]=str(ex)
 body=mesh.get_editor_property('body_setup')
 vals['collision_trace_flag']=str(body.get_editor_property('collision_trace_flag'))
 vals['agg_geom']=str(body.get_editor_property('agg_geom'))
 info['Mesa'+str(i)]=vals
(O/'geometry-inspection.json').write_text(json.dumps(info,indent=2))
rows=[];lights=[]
exec(review[review.index('cmd=u.SystemLibrary'):])

# The first review establishes an unchanged baseline. Apply the variant recipe after captures.
