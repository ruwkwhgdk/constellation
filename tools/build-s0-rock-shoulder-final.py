"""One-shot decorative shoulder on maintained cap; no gameplay geometry changes."""
import unreal as u, json, math
from collections import Counter
E=u.EditorAssetLibrary;Q=u.GeometryScript_MeshQueries;AS=u.GeometryScript_AssetUtils
a=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='S0_Art_RearCrown_ledgeA')
assert not a.get_actor_enable_collision()
c=a.static_mesh_component;source=c.static_mesh;original_materials=list(c.get_materials())
assert source.get_name()=='SM_S0_FittedTransition_V28_0'
dest='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/SM_S0_RockShoulder_V31'
assert not E.does_asset_exist(dest)
transform=c.get_world_transform()
# Irregular narrow flank, embedded behind the existing front surface at both ends.
# Each row: height, outer X, inner X, front Y. Z>=280 is entirely rear-wall decoration.
rows=[(280,810,920,2010),(400,774,1010,1986),(535,750,1015,1978),(650,782,990,1988),(775,755,1010,1980),(885,780,980,1988),(975,793,940,1990),(1040,805,890,2010)]
world=[];faces=[]
for z,left,right,front in rows:
    ring=[(left+12,2082),(left,2020),(left+18,front+12),((left+right)*.5,front),(right-35,2012),(right,2035),(right-10,2082)]
    world.extend([(x,y,z) for x,y in ring])
n=7
for i in range(len(rows)-1):
    for j in range(n):
        aa=i*n+j;bb=i*n+(j+1)%n;cc=(i+1)*n+(j+1)%n;dd=(i+1)*n+j
        faces.extend([(aa,bb,cc),(aa,cc,dd)])
for j in range(1,n-1):faces.append((0,j+1,j))
base=(len(rows)-1)*n
for j in range(1,n-1):faces.append((base,base+j,base+j+1))
def volume():
    total=0
    for ia,ib,ic in faces:
        p,q,r=world[ia],world[ib],world[ic]
        total+=p[0]*(q[1]*r[2]-q[2]*r[1])+p[1]*(q[2]*r[0]-q[0]*r[2])+p[2]*(q[0]*r[1]-q[1]*r[0])
    return total/6
if volume()>0:faces=[(i,k,j) for i,j,k in faces] # Unreal-facing winding verified on V28.
edges=Counter(tuple(sorted(e)) for f in faces for e in [(f[0],f[1]),(f[1],f[2]),(f[2],f[0])])
assert all(count==2 for count in edges.values()) and abs(volume())>1
assert min(p[1] for p in world)>1900
buffers=u.GeometryScriptSimpleMeshBuffers()
buffers.vertices=[u.MathLibrary.inverse_transform_location(transform,u.Vector(*p)) for p in world]
buffers.triangles=[u.IntVector(*f) for f in faces]
buffers.uv0=[u.Vector2D(p[0]/250,p[2]/250) for p in world]
d=u.DynamicMesh();result=AS.copy_mesh_from_static_mesh(source,d,u.GeometryScriptCopyMeshFromAssetOptions(),u.GeometryScriptMeshReadLOD());assert 'SUCCESS' in str(result[-1])
assert Q.get_is_closed_mesh(d)
u.GeometryScript_MeshEdits.append_buffers_to_mesh(d,buffers)
assert Q.get_is_closed_mesh(d)
opts=u.GeometryScriptSplitNormalsOptions();opts.opening_angle_deg=55;opts.split_by_opening_angle=True
u.GeometryScript_Normals.compute_split_normals(d,opts,u.GeometryScriptCalculateNormalsOptions())
mesh=E.duplicate_asset(source.get_path_name(),dest);assert mesh
copy=u.GeometryScriptCopyMeshToAssetOptions();copy.enable_recompute_normals=False
result=AS.copy_mesh_to_static_mesh(d,mesh,copy,u.GeometryScriptMeshWriteLOD());assert 'SUCCESS' in str(result[-1])
assert E.save_loaded_asset(mesh,False)
material=original_materials[0]
assert all(m==material for m in original_materials)
targets=[(a,source,mesh,original_materials)]
(O/'mesh-audit.json').write_text(json.dumps({'actor':a.get_name(),'source':source.get_path_name(),'candidate':mesh.get_path_name(),'added_world_vertices':world,'added_triangles':faces,'added_triangles_count':len(faces),'closed':True,'collision_enabled':False,'note':'Two intersecting closed shells; decorative only. Existing cap retained.'},indent=2))

