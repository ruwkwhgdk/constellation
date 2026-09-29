"""Reference corrections: landing grid, wall-mounted lamps, rear architecture."""
import unreal as u, math
def apply_details():
    A=u.get_editor_subsystem(u.EditorActorSubsystem); E=u.EditorAssetLibrary; M=u.MaterialEditingLibrary
    actors={a.get_actor_label():a for a in A.get_all_level_actors()}
    for label,a in actors.items():
        if label.startswith('SWScene_Detail_'): A.destroy_actor(a)
    root='/Game/Environment/StairwellModular/Scene/Materials/Weathered/'
    def mat(name): return E.load_asset(root+name+'_Weathered')
    def cube(name,pos,size,material):
        a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),u.Rotator())
        a.set_actor_label('SWScene_Detail_'+name); a.static_mesh_component.set_static_mesh(E.load_asset('/Engine/BasicShapes/Cube'))
        a.set_actor_scale3d(u.Vector(*[v/100 for v in size])); a.static_mesh_component.set_material(0,material); return a
    def beam(name,start,end,radius=2):
        mid=[(a+b)/2 for a,b in zip(start,end)]; d=[b-a for a,b in zip(start,end)]; length=math.sqrt(sum(v*v for v in d))
        a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*mid),u.Rotator(pitch=math.degrees(math.atan2(d[2],math.hypot(d[0],d[1])))-90,yaw=math.degrees(math.atan2(d[1],d[0])),roll=0))
        a.set_actor_label('SWScene_Detail_'+name); a.static_mesh_component.set_static_mesh(E.load_asset('/Engine/BasicShapes/Cylinder')); a.set_actor_scale3d(u.Vector(radius/50,radius/50,length/100)); a.static_mesh_component.set_material(0,mat('M_Kit_RailSteel')); return a
    # Tile pattern turns 30 degrees; physical landing remains flush with both flights.
    path=root+'M_LandingTurn30'
    if not E.does_asset_exist(path): assert E.duplicate_asset(root+'M_Kit_FloorTile_Weathered',path)
    landing_mat=E.load_asset(path)
    # Create a dedicated grid material using supported node creation APIs.
    M.delete_all_material_expressions(landing_mat)
    custom=M.create_material_expression(landing_mat,u.MaterialExpressionCustom)
    custom.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
    inp=u.CustomInput(); inp.set_editor_property('input_name','P'); custom.set_editor_property('inputs',[inp])
    custom.set_editor_property('code','float2 p=P.xy-float2(180,-120); float2 q=float2(0.8660254*p.x+0.5*p.y,-0.5*p.x+0.8660254*p.y); float2 d=abs(frac(q/30.0+0.5)-0.5)*30.0; float2 aa=max(fwidth(q)*0.5,0.025); float2 v=smoothstep(0.18-aa,0.18+aa,d); float dirt=0.86+0.07*sin(P.x*0.071+sin(P.y*0.03))*sin(P.y*0.083); return lerp(float3(0.05,0.065,0.063),float3(0.28,0.34,0.35)*dirt,min(v.x,v.y));')
    p=M.create_material_expression(landing_mat,u.MaterialExpressionWorldPosition); M.connect_material_expressions(p,'',custom,'P'); M.connect_material_property(custom,'',u.MaterialProperty.MP_BASE_COLOR)
    rough=M.create_material_expression(landing_mat,u.MaterialExpressionConstant); rough.r=.63; M.connect_material_property(rough,'',u.MaterialProperty.MP_ROUGHNESS)
    M.recompile_material(landing_mat); E.save_loaded_asset(landing_mat)
    overlay=cube('LandingRotatedTiles',(270,180,-.42),(180,600,1),landing_mat)
    overlay.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    # Restore the right wall to the landing edge, backing the wall-mounted fixture.
    for z in [-30,210]:
        a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(90,127.5,z+120),u.Rotator())
        a.set_actor_label('SWScene_Detail_RightWall_'+str(z)); a.static_mesh_component.set_static_mesh(E.load_asset('/Engine/BasicShapes/Cube'))
        a.set_actor_scale3d(u.Vector(.6,.15,2.4))
        a.static_mesh_component.set_material(0,mat('M_Kit_WallTile'))
    for name in ['OpenEdgeRailPost60','OpenEdgeRailPost180']:
        if 'SWScene_'+name in actors: actors['SWScene_'+name].set_actor_hidden_in_game(True); actors['SWScene_'+name].set_is_temporarily_hidden_in_editor(True)
    # Narrow service panels and structural reveals beside the door and on the far side.
    paint=mat('M_Kit_MetalPaint'); dark=mat('M_Kit_DarkTrim'); concrete=mat('M_Kit_Concrete')
    cube('DoorSideServicePanel',(342,82,114),(4,61,222),paint)
    for y in [51,113]: cube('DoorSidePanelReveal'+str(y),(339,y,114),(5,3,224),dark)
    cube('DoorSidePier',(345,119,120),(24,10,240),concrete)
    # Panels follow the outside wall of the descending flight, leaving its path open.
    for x in [395,495,595]:
        cube('RearServicePanel'+str(x),(x,354,68),(94,4,220),paint)
        cube('RearPier'+str(x),(x-49,349,68),(7,14,230),concrete)
    for z in [65,90]:
        beam('RearTurnRail'+str(z),(350,55,z),(350,128,z))
        beam('RearJoinRail'+str(z),(350,128,z),(360,128,z))
    # Door hardware remains attached in world to the approved closed-door pose.
    door=actors['SWScene_DoorLeaf']
    for z in [70,95]:
        a=beam('DoorPushBar'+str(z),(346,-42,z),(346,31,z),1.4)
        a.attach_to_actor(door,'',u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
    # Ceiling bounce is directional upward; it does not wash out the foreground steps.
    light=A.spawn_actor_from_class(u.RectLight,u.Vector(65,15,292),u.Rotator(pitch=90))
    light.set_actor_label('SWScene_Detail_CeilingBounce'); c=light.get_component_by_class(u.RectLightComponent); c.set_mobility(u.ComponentMobility.MOVABLE); c.set_intensity(850); c.set_light_color(u.LinearColor(.65,.85,1)); c.set_editor_property('source_width',160); c.set_editor_property('source_height',120); c.set_editor_property('attenuation_radius',420)
    return dict(landing_pattern_yaw_deg=30,landing_footprint_unchanged=True,right_wall_end_cm=120,rear_panels=4,door_push_bars=2,reference_hidden_geometry='inferred')
