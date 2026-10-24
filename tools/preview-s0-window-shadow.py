labels=['S0_Ref_WindowBlue_0','S0_Ref_WindowBlue_1','S0_Ref_WindowBlue_2','S0_Ref_CaveBlue']
changes=[]
for a in A.get_all_level_actors():
 if a.get_actor_label() in labels:
  c=a.get_component_by_class(u.LightComponent);assert c.get_editor_property('cast_shadows')
  changes.append(dict(name=a.get_name(),label=a.get_actor_label(),old=True,new=False));c.set_cast_shadows(False)
assert len(changes)==4
(O/'changes.json').write_text(json.dumps(changes,indent=2))
tag='art1';shots=[('floor',(2600,0,180),(-8,180)),('reverse',(3050,-2650,1650),(-25,130))];S.update(i=0,sent=False,t=time.monotonic())
