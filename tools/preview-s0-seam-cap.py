a=next(a for a in A.get_all_level_actors() if a.get_name()=='StaticMeshActor_797');c=a.static_mesh_component
mat=u.load_asset('/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/M_S0_ShallowRock_V18');assert mat
old=c.get_material(1)
(O/'changes.json').write_text(json.dumps([dict(name=a.get_name(),label=a.get_actor_label(),slot=1,old=old.get_path_name(),new=mat.get_path_name())],indent=2))
c.set_material(1,mat)
tag='art1';shots=[('junction',(2600,900,700),(0,110)),('concept',(2900,900,700),(-20,-138))];S.update(i=0,sent=False,t=time.monotonic())
