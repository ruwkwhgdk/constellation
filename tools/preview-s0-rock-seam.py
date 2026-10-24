a=next(a for a in A.get_all_level_actors() if a.get_name()=='StaticMeshActor_797')
assert a.get_actor_label()=='classroom_start_floor_22'
c=a.static_mesh_component;old=c.get_material(0);assert old.get_name()=='M_S0_Plaster_V9'
mat=u.load_asset('/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/M_S0_ShallowRock_V18');assert mat
(O/'changes.json').write_text(json.dumps([dict(name=a.get_name(),label=a.get_actor_label(),old=old.get_path_name(),new=mat.get_path_name())],indent=2))
c.set_material(0,mat)
tag='art1';shots=[('backwall',(1700,400,300),(5,90)),('concept',(2900,900,700),(-20,-138))];S.update(i=0,sent=False,t=time.monotonic())
