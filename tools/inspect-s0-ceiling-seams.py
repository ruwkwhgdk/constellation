"""Read-only mesh intersection audit; no collision-HitResult reflection dependency."""
import unreal as u,math,json,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/CeilingSeamAudit_20261023';O.mkdir(parents=True,exist_ok=True)
def vec(p):return (p.x,p.y,p.z)
def sub(a,b):return tuple(a[i]-b[i] for i in range(3))
def dot(a,b):return sum(a[i]*b[i] for i in range(3))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def intersect(origin,direction,p,q,r):
 e1=sub(q,p);e2=sub(r,p);h=cross(direction,e2);det=dot(e1,h)
 if abs(det)<1e-8:return None
 s=sub(origin,p);t0=dot(s,h)/det
 if t0<0 or t0>1:return None
 k=cross(s,e1);t1=dot(direction,k)/det
 if t1<0 or t0+t1>1:return None
 distance=dot(e2,k)/det
 return distance if 0<distance<4000 else None
try:
 assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 A=u.get_editor_subsystem(u.EditorActorSubsystem);Q=u.GeometryScript_MeshQueries
 pitch=math.radians(57);yaw=math.radians(-120)
 forward=(math.cos(pitch)*math.cos(yaw),math.cos(pitch)*math.sin(yaw),math.sin(pitch));right=(-math.sin(yaw),math.cos(yaw),0);up=(-math.sin(pitch)*math.cos(yaw),-math.sin(pitch)*math.sin(yaw),math.cos(pitch))
 rays=[]
 for x,y in [(800,140),(800,160),(800,185),(700,240),(700,265),(700,290),(650,340),(650,390),(650,450)]:
  h=(x/800-1)*math.tan(math.radians(41.5));v=(1-y/450)*math.tan(math.radians(41.5))*900/1600
  rays.append({'pixel':[x,y],'direction':tuple(forward[i]+right[i]*h+up[i]*v for i in range(3)),'hits':[]})
 candidates=[];cache={}
 for actor in A.get_all_level_actors():
  center,extent=actor.get_actor_bounds(False)
  if center.x+extent.x<-1000 or center.x-extent.x>4000 or center.y+extent.y<-4000 or center.y-extent.y>3500 or center.z+extent.z<2200 or center.z-extent.z>3800:continue
  for c in actor.get_components_by_class(u.StaticMeshComponent):
   mesh=c.static_mesh
   if not mesh:continue
   path=mesh.get_path_name()
   if path not in cache:
    d=u.DynamicMesh();result=u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(mesh,d,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD())
    if 'SUCCESS' not in str(result[-1]):continue
    _,positions,gaps=Q.get_all_vertex_positions(d,False);_,triangles,tgaps=Q.get_all_triangle_indices(d,False)
    cache[path]=(positions.convert_vector_list_to_array(),triangles.convert_triangle_list_to_array())
   pp,tt=cache[path]
   if len(tt)>200000:continue
   transform=c.get_world_transform();world=[vec(u.MathLibrary.transform_location(transform,p)) for p in pp]
   candidates.append({'name':actor.get_name(),'label':actor.get_actor_label(),'bounds':str((center,extent)),'mesh':path,'materials':[str(m) for m in c.get_materials()]})
   for index,tri in enumerate(tt):
    if min(tri.x,tri.y,tri.z)<0:continue
    p,q,r=[world[i] for i in (tri.x,tri.y,tri.z)]
    for ray in rays:
     distance=intersect((1800,700,1100),ray['direction'],p,q,r)
     if distance is not None:
      point=[(1800,700,1100)[i]+ray['direction'][i]*distance for i in range(3)]
      ray['hits'].append({'actor':actor.get_name(),'label':actor.get_actor_label(),'component':c.get_name(),'distance':distance,'point':point,'triangle':index,'mesh':path})
 for ray in rays:ray['hits']=sorted(ray['hits'],key=lambda h:h['distance'])[:8]
 (O/'geometry.json').write_text(json.dumps({'rays':rays,'candidates':candidates},indent=2))
except Exception:(O/'error.txt').write_text(traceback.format_exc())
u.SystemLibrary.quit_editor()
