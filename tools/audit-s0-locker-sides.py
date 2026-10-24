import unreal as u,json
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/S0LockerSides';O.mkdir(exist_ok=True)
P=lambda o,k:o.get_editor_property(k)
w=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
rows=[]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 for c in a.get_components_by_class(u.StaticMeshComponent):
  m=c.static_mesh
  if m and 'SM_Locker' in m.get_path_name() and a.get_actor_location().distance(u.Vector(3203,0,214.6))<450:
   rows.append(dict(actor=a.get_actor_label(),component=c.get_name(),mesh=m.get_path_name(),transform=str(c.get_world_transform()),bounds=str(m.get_bounding_box()),materials=[str(c.get_material(i)) for i in range(c.get_num_materials())]))
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening')
(O/'audit.json').write_text(json.dumps(dict(actors=rows,cameras=[str(x) for x in P(a,'cameras')],steps=[dict(i=i,data=s.export_text()) for i,s in enumerate(P(a,'steps')) if P(s,'type')==u.DirectorNodeType.CAMERA_MOVE]),ensure_ascii=False,indent=2),encoding='utf8')
u.SystemLibrary.quit_editor()
