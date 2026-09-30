"""Import the separated stairwell door pair and create a dedicated verification map."""
import unreal as u
import json
from pathlib import Path
SRC=Path(u.Paths.project_dir())/'ArtSource/Stairwell_Modular/Export/DoorPair'
DEST='/Game/Constellation/Environments/Stairwell'
AT=u.AssetToolsHelpers.get_asset_tools(); E=u.EditorAssetLibrary; M=u.MaterialEditingLibrary
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
def imported(filename,dest,options=None):
    t=u.AssetImportTask(); t.filename=str(SRC/filename); t.destination_path=dest
    t.automated=True; t.replace_existing=True; t.save=True
    if options:
        t.options=options; t.factory=u.FbxFactory(); t.replace_existing_settings=True
    AT.import_asset_tasks([t])
    assert t.imported_object_paths,filename
    return E.load_asset(t.imported_object_paths[0])
tex=imported('T_Stairwell_Door14_BaseColor.png',DEST+'/Textures')
def material(name,texture=None):
    path=DEST+'/Materials/'+name
    mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(name,DEST+'/Materials',u.Material,u.MaterialFactoryNew())
    M.delete_all_material_expressions(mat)
    if texture:
        n=M.create_material_expression(mat,u.MaterialExpressionTextureSample); n.texture=texture
        M.connect_material_property(n,'RGB',u.MaterialProperty.MP_BASE_COLOR)
    else:
        n=M.create_material_expression(mat,u.MaterialExpressionConstant3Vector); n.constant=u.LinearColor(.24,.25,.26,1)
        M.connect_material_property(n,'',u.MaterialProperty.MP_BASE_COLOR)
    for prop,value in [(u.MaterialProperty.MP_ROUGHNESS,.72),(u.MaterialProperty.MP_METALLIC,.05)]:
        n=M.create_material_expression(mat,u.MaterialExpressionConstant); n.r=value; M.connect_material_property(n,'',prop)
    M.recompile_material(mat); E.save_loaded_asset(mat); return mat
mats=[material('M_Stairwell_DoorPaint',tex),material('M_Stairwell_FramePaint')]
opts=u.FbxImportUI(); opts.import_mesh=True; opts.import_materials=False; opts.import_textures=False
opts.import_as_skeletal=False; opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
d=opts.static_mesh_import_data; d.combine_meshes=True; d.auto_generate_collision=False
d.one_convex_hull_per_ucx=True; d.generate_lightmap_u_vs=True; d.transform_vertex_to_absolute=False
d.convert_scene_unit=True
meshes=[]
for name,mat in zip(['SM_Stairwell_DoorLeaf14','SM_Stairwell_DoorFrame13'],mats):
    mesh=imported(name+'.fbx',DEST+'/Meshes',opts); mesh.set_material(0,mat); E.save_loaded_asset(mesh); meshes.append(mesh)
bp_path=DEST+'/Blueprints/BP_Stairwell_DoorAssembly'
if E.does_asset_exist(bp_path):
    bp=E.load_asset(bp_path)
else:
    factory=u.BlueprintFactory(); factory.set_editor_property('parent_class',u.Actor)
    bp=AT.create_asset('BP_Stairwell_DoorAssembly',DEST+'/Blueprints',u.Blueprint,factory)
    sub=u.get_engine_subsystem(u.SubobjectDataSubsystem); lib=u.SubobjectDataBlueprintFunctionLibrary
    handles=sub.k2_gather_subobject_data_for_blueprint(bp)
    root=handles[0]
    for name,mesh in [('DoorFrame',meshes[1]),('DoorLeaf',meshes[0])]:
        h,reason=sub.add_new_subobject(u.AddNewSubobjectParams(parent_handle=root,new_class=u.StaticMeshComponent,blueprint_context=bp))
        assert not str(reason),str(reason)
        sub.rename_subobject(h,name)
        comp=lib.get_object_for_blueprint(lib.get_data(h),bp)
        comp.set_static_mesh(mesh); comp.set_mobility(u.ComponentMobility.MOVABLE)
        comp.set_collision_profile_name('BlockAllDynamic')
    u.BlueprintEditorLibrary.compile_blueprint(bp)
    E.save_loaded_asset(bp)
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
map_path=DEST+'/Maps/L_Stairwell_DoorVerification'
assert (level.load_level(map_path) if E.does_asset_exist(map_path) else level.new_level(map_path))
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
cls=E.load_blueprint_class(bp_path)
report={'assets':[],'blueprint':bp_path,'map':map_path,'runtime_interaction_implemented':False,'states':[]}
for name,pos,angle in [('Closed',0,0),('Open90',250,90)]:
    a=actors.spawn_actor_from_class(cls,u.Vector(pos,0,0)); a.set_actor_label('Door_'+name)
    comps=a.get_components_by_class(u.StaticMeshComponent)
    leaf=next(c for c in comps if c.static_mesh==meshes[0]); frame=next(c for c in comps if c.static_mesh==meshes[1])
    original=frame.get_world_transform()
    leaf.set_relative_rotation(u.Rotator(pitch=0,yaw=angle,roll=0),False,False)
    assert frame.get_world_transform()==original
    assert abs(leaf.get_editor_property('relative_rotation').yaw-angle)<.01
    report['states'].append({'name':name,'leaf_yaw':leaf.get_editor_property('relative_rotation').yaw,'frame_unchanged':True})
floor=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(75,0,-5)); floor.set_actor_label('VerificationFloor')
floor.static_mesh_component.set_static_mesh(E.load_asset('/Engine/BasicShapes/Cube'))
floor.set_actor_scale3d(u.Vector(6,5,.1))
light=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,400),u.Rotator(pitch=-45,yaw=-30,roll=0))
actors.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,300))
actors.spawn_actor_from_class(u.PlayerStart,u.Vector(-50,-250,100),u.Rotator(pitch=0,yaw=90,roll=0))
sms=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
for mesh in meshes:
    bounds=mesh.get_bounding_box(); size=bounds.max-bounds.min
    geom=mesh.get_editor_property('body_setup').get_editor_property('agg_geom')
    collisions=sum(len(geom.get_editor_property(p)) for p in ['convex_elems','box_elems','sphere_elems','sphyl_elems'])
    report['assets'].append({'path':mesh.get_path_name(),'dimensions_cm':[size.x,size.y,size.z],'collision_hulls':collisions})
assert report['assets'][0]['collision_hulls']==1,report
assert report['assets'][1]['collision_hulls']==3,report
assert 205<report['assets'][0]['dimensions_cm'][2]<215,report
level.save_current_level(); E.save_directory(DEST,only_if_is_dirty=True,recursive=True)
(SRC/'unreal_import_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
u.log('STAIRWELL_DOOR_IMPORT_VERIFIED '+json.dumps(report))
