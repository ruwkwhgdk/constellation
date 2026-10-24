mat=u.EditorAssetLibrary.load_asset('/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/M_S0_UpperWindowBacking_V19');assert mat
changes=[]
for a in A.get_all_level_actors():
 if not a.get_actor_label().startswith('ClassroomStart_ExteriorWindowBlackout_') or a.get_actor_location().z>=1000:continue
 c=a.static_mesh_component;old=c.get_material(0)
 assert old.get_name()=='M_ClassroomStart_WindowBlackout'
 changes.append(dict(name=a.get_name(),label=a.get_actor_label(),old=old.get_path_name(),new=mat.get_path_name()))
 c.set_material(0,mat)
assert len(changes)==14,len(changes)
(O/'changes.json').write_text(json.dumps(changes,indent=2))
tag='art1';shots=[('lower-window',(2800,-1500,400),(0,-90)),('concept',(2900,900,700),(-20,-138))];S.update(i=0,sent=False,t=time.monotonic())
