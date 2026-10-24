records=[]
for a in A.get_all_level_actors():
 if a.get_name() not in ['StaticMeshActor_788','StaticMeshActor_789']:continue
 c=a.static_mesh_component;mesh=c.static_mesh;t=a.get_actor_transform();sections=[]
 for i in range(mesh.get_num_sections(0)):
  vertices,triangles,normals,uvs,tangents=u.ProceduralMeshLibrary.get_section_from_static_mesh(mesh,0,i)
  points=[u.MathLibrary.transform_location(t,v) for v in vertices]
  sections.append(dict(index=i,points=sorted(set((round(v.x,4),round(v.y,4),round(v.z,4)) for v in points)),triangles=len(triangles)//3))
 records.append(dict(name=a.get_name(),label=a.get_actor_label(),transform=str(t),materials=[m.get_path_name() if m else '' for m in c.get_materials()],sections=sections))
(O/'join-geometry.json').write_text(json.dumps(records,indent=2))
tag='baseline';shots=[('upper',(1450,1500,1500),(-30,105))];S.update(i=0,sent=False,t=time.monotonic())
