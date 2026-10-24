"""Closed purpose-fit decorative wall cap, in Unreal centimetres. Original assets preserved."""
import unreal as u, math, json
from collections import Counter
E=u.EditorAssetLibrary
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
knots=[(790,1065),(980,1035),(1170,1090),(1370,1115),(1570,1060),(1760,1040),(2000,1080),(2210,1055),(2420,1025),(2630,1095),(2820,1105),(3010,1060),(3210,1035)]
def height(x):
 for (a,h),(b,k) in zip(knots,knots[1:]):
  if a<=x<=b:return h+(k-h)*(x-a)/(b-a)
 raise ValueError(x)
targets=[];audit=[]
for idx,(left,right,center,label) in enumerate([(790,2000,1400,'S0_Art_RearCrown_ledgeA'),(2000,3210,2600,'S0_Art_RearCrown_ledgeB')]):
 a=next(a for a in A.get_all_level_actors() if a.get_actor_label()==label)
 assert not a.get_actor_enable_collision()
 oldmesh=a.static_mesh_component.static_mesh;oldtransform=a.get_actor_transform()
 dest=D+'/SM_S0_FittedTransition_V26_'+str(idx)
 assert not E.does_asset_exist(dest),'One-shot candidate already exists'
 # Use all shared silhouette knots and intermediate samples. Both halves share an identical seam ring.
 xs=sorted(set([left,right]+[x for x,h in knots if left<x<right]+[left+(right-left)*i/24 for i in range(1,24)]))
 verts=[];faces=[]
 for x in xs:
  top=height(x);front=1982-7*math.sin(x*.013)-6*math.cos(x*.021)
  skirt=720+29*math.sin(x*.009)+18*math.cos(x*.017)
  ring=[(2085,skirt),(2020,skirt),(front+16,850+18*math.sin(x*.012)),(front,965),(front+8,top-23),(front+24,top),(2085,top-10)]
  verts.extend([(x-center,y-2000,z-900) for y,z in ring])
 n=7
 for i in range(len(xs)-1):
  for j in range(n):
   a0=i*n+j;b0=i*n+(j+1)%n;c0=(i+1)*n+(j+1)%n;d0=(i+1)*n+j
   faces.extend([(a0,b0,c0),(a0,c0,d0)])
 # Convex cross section caps, fan from its first vertex.
 for j in range(1,n-1):faces.append((0,j+1,j))
 base=(len(xs)-1)*n
 for j in range(1,n-1):faces.append((base,base+j,base+j+1))
 def signed_volume():
  total=0
  for ia,ib,ic in faces:
   p,q,r=verts[ia],verts[ib],verts[ic]
   total+=p[0]*(q[1]*r[2]-q[2]*r[1])+p[1]*(q[2]*r[0]-q[0]*r[2])+p[2]*(q[0]*r[1]-q[1]*r[0])
  return total/6
 if signed_volume()<0:faces=[(i,k,j) for i,j,k in faces]
 edges=Counter(tuple(sorted(e)) for f in faces for e in [(f[0],f[1]),(f[1],f[2]),(f[2],f[0])])
 assert all(count==2 for count in edges.values()) and signed_volume()>0
 assert all(math.isfinite(c) for p in verts for c in p)
 buffers=u.GeometryScriptSimpleMeshBuffers()
 buffers.vertices=[u.Vector(*p) for p in verts];buffers.triangles=[u.IntVector(*f) for f in faces]
 buffers.uv0=[u.Vector2D(p[0]/250,p[2]/250) for p in verts]
 d=u.DynamicMesh();u.GeometryScript_MeshEdits.append_buffers_to_mesh(d,buffers)
 assert u.GeometryScript_MeshQueries.get_is_closed_mesh(d)
 opts=u.GeometryScriptSplitNormalsOptions();opts.opening_angle_deg=55;opts.split_by_opening_angle=True
 u.GeometryScript_Normals.compute_split_normals(d,opts,u.GeometryScriptCalculateNormalsOptions())
 mesh=E.duplicate_asset(oldmesh.get_path_name(),dest);assert mesh
 copy=u.GeometryScriptCopyMeshToAssetOptions();copy.enable_recompute_normals=False
 result=u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(d,mesh,copy,u.GeometryScriptMeshWriteLOD());assert 'SUCCESS' in str(result[-1])
 mesh.set_editor_property('complex_collision_mesh',None)
 assert E.save_loaded_asset(mesh,False)
 transform=u.Transform(location=u.Vector(center,2000,900),rotation=u.Rotator(),scale=u.Vector(1,1,1))
 targets.append((a,oldmesh,mesh,oldtransform,transform))
 audit.append({'label':label,'source':oldmesh.get_path_name(),'candidate':mesh.get_path_name(),'vertices':verts,'triangles':faces,'closed':True,'volume_cm3':signed_volume(),'world_x_range':[left,right],'min_world_y':min(v[1]+2000 for v in verts),'top_range_cm':[min(height(x) for x in xs),max(height(x) for x in xs)],'collision':'actor remains disabled'})
(O/'mesh-audit.json').write_text(json.dumps(audit,indent=2))
