import unreal as u,json
from pathlib import Path
p=Path(u.Paths.project_dir())/'Saved/S0WetFloor/RockCut_20261022';p.mkdir(parents=True,exist_ok=True)
try:
 result={}
 for name in ['GeometryScript_MeshModeling','GeometryScript_MeshRepair','GeometryScript_MeshQueries']:
  c=getattr(u,name);result[name]={k:str(getattr(c,k).__doc__) for k in dir(c) if any(s in k.lower() for s in ['plane_cut','fill_hole','boundary','triangle_count'])}
 for name in ['GeometryScriptMeshPlaneCutOptions','GeometryScriptFillHolesOptions']:
  c=getattr(u,name,None);result[name]=str(c.__doc__) if c else 'missing'
 for n in [11,12]:
  m=u.load_asset('/Game/LuosCaves/Meshes/Props_Mesas/SM_LCave_P_Mesa_%02d'%n);result[str(n)]=str(m.get_bounding_box())
 (p/'api.json').write_text(json.dumps(result,indent=2))
finally:u.SystemLibrary.quit_editor()
