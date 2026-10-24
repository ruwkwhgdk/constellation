a=next(a for a in A.get_all_level_actors() if a.get_name()=='StaticMeshActor_789');assert a.get_actor_label()=='classroom_start_floor_20'
c=a.static_mesh_component;mat=u.load_asset('/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/M_S0_UpperWood_V15');assert mat
old=c.get_material(0)
(O/'changes.json').write_text(json.dumps([dict(name=a.get_name(),label=a.get_actor_label(),slot=0,old=old.get_path_name(),new=mat.get_path_name())],indent=2))
c.set_material(0,mat)
tag='art1';shots=[('upper',(1450,1500,1500),(-30,105)),('concept',(2900,900,700),(-20,-138)),('join-close',(1400,2250,1170),(-20,20))];S.update(i=0,sent=False,t=time.monotonic())
