"""Apply the authorized instance replacement and two-way subway travel volumes."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,shutil,datetime,hashlib,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'ArtSource/SubwayEntrance/Production/v001';D='/Game/Constellation/Environments/SubwayEntrance'
E=u.EditorAssetLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
EXT='/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland';INT='/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2'
Travel=u.load_class(None,'/Script/Constellation.SubwayTravelVolume');assert Travel
manifest=load_current_json((O/'manifest.json').read_text());assert (O/'unreal_import.json').exists()
backup=R/'Saved/SubwayEntranceRecovery'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S');backup.mkdir(parents=True,exist_ok=True)
for package in [EXT,INT]:
    file=R/'Content'/(package.removeprefix('/Game/')+'.umap');shutil.copy2(file,backup/file.name)
report=dict(backup=str(backup),maps=[],play_tested=False)
def snapshot():
    out={}
    for a in A.get_all_level_actors():
        p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d()
        row=dict(position=[p.x,p.y,p.z],rotation=[r.pitch,r.yaw,r.roll],scale=[s.x,s.y,s.z])
        if isinstance(a,u.StaticMeshActor):row['mesh']=a.static_mesh_component.static_mesh.get_path_name() if a.static_mesh_component.static_mesh else None
        out[a.get_actor_label()]=row
    return out
def spawn(cls,label,pos,rot=None):
    actor=A.spawn_actor_from_class(cls,u.Vector(*pos),rot or u.Rotator(pitch=0,yaw=0,roll=0));assert actor;actor.set_actor_label(label);actor.set_folder_path('SubwayEntrance');return actor
def volume(label,pos,extent,dest,arrival,yaw,max_foot):
    a=spawn(Travel,label,pos);a.set_editor_property('destination_map',E.load_asset(dest));a.set_editor_property('arrival_transform',u.Transform(location=u.Vector(*arrival),rotation=u.Rotator(pitch=0,yaw=yaw,roll=0),scale=u.Vector(1,1,1)))
    a.set_editor_property('maximum_foot_height',max_foot);a.get_editor_property('zone').set_box_extent(u.Vector(*extent),False);return a
current=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
if u.GameplayStatics.get_current_level_name(current,True)!='L_StartIsland':assert L.load_level(EXT)
before=snapshot();actors={a.get_actor_label():a for a in A.get_all_level_actors()}
assert not any(n.startswith('SE_') for n in actors),'Already applied: use a revision script instead.'
dummy=actors['subway_station'];island=actors['sky_island'];assert (dummy.get_actor_location()-u.Vector(3900,-19500,10530)).length()<1
assert before['sky_island']['mesh']=='/Game/Constellation/Environments/Shared/Architecture/Dummy/SM_Dummy_Cone_Large.SM_Dummy_Cone_Large'
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
# Confirm the actual surface, not just the actor's pivot/bounds.
u.log('ISLAND_COLLISION '+str(island.static_mesh_component.get_collision_enabled())+' simple='+str(u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_simple_collision_count(island.static_mesh_component.static_mesh)))
hit=u.SystemLibrary.line_trace_single(world,u.Vector(3900,-18800,11000),u.Vector(3900,-18800,9500),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[a for a in A.get_all_level_actors() if a!=island],u.DrawDebugTrace.NONE,True)
u.log('GROUND_TRACE '+str(hit))
def hit_z(h):
    if isinstance(h,tuple):h=next(x for x in h if isinstance(x,u.HitResult))
    if h is None:return None
    b=h.to_tuple()
    return b[4].z if b[0] else None
z=hit_z(hit);assert z is not None and abs(z-10000)<2,('Unexpected ground',z)
old_center,old_extent=island.get_actor_bounds(False)
surface_samples=[]
for ix in range(9):
    for iy in range(9):
        x=old_center.x+(ix-4)*900;y=old_center.y+(iy-4)*900
        if abs(x-3900)<214 and -19874<y<-19146:continue
        h=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,11000),u.Vector(x,y,6500),u.TraceTypeQuery.ECC_VISIBILITY,True,[a for a in A.get_all_level_actors() if a!=island],u.DrawDebugTrace.NONE,True)
        surface_samples.append((x,y,hit_z(h)))
root=spawn(u.TargetPoint,'SE_EntranceRoot',(3900,-19500,10530))
root.root_component.set_mobility(u.ComponentMobility.STATIC)
for row in manifest['assets']:
    a=spawn(u.StaticMeshActor,'SE_'+row['id'],(3900,-19500,10000));c=a.static_mesh_component;c.set_static_mesh(E.load_asset(D+'/Meshes/'+row['name']));c.set_mobility(u.ComponentMobility.STATIC)
    c.set_collision_profile_name('BlockAll' if row['collision_hulls'] else 'NoCollision')
    a.attach_to_actor(root,'',u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
    assert a.get_attach_parent_actor()==root
island_mat=island.static_mesh_component.get_material(0)
new_mesh=E.load_asset(D+'/Meshes/SM_SE_IslandWithStairwell');assert new_mesh
island.modify();island.static_mesh_component.set_static_mesh(new_mesh);island.static_mesh_component.set_material(0,island_mat)
island.set_actor_location(u.Vector(3900,-19500,10000),False,True);island.set_actor_rotation(u.Rotator(pitch=0,yaw=0,roll=0),True);island.set_actor_scale3d(u.Vector(1,1,1))
island.static_mesh_component.set_collision_profile_name('BlockAll')
assert A.destroy_actor(dummy)
volume('SE_TravelToInterior',(3900,-19760,9860),(198,48,115),INT,(-520,0,460),0,9800)
# Local lights only: no changes to the island's exposure, skylight or sun.
for i,y in enumerate([-19200,-19520,-19770]):
    a=spawn(u.RectLight,'SE_Light_%02d'%i,(3900,y,10280),u.Rotator(pitch=-90,yaw=0,roll=0))
    c=a.get_component_by_class(u.RectLightComponent);c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(220);c.set_editor_property('attenuation_radius',650);c.set_editor_property('source_width',160);c.set_editor_property('source_height',35)
after=snapshot()
for name,data in before.items():
    if name in ['subway_station','sky_island']:continue
    assert after.get(name)==data,('Unrelated actor changed',name)
assert 'subway_station2' in after and E.does_asset_exist('/Game/Constellation/Environments/StartIsland/Props/SubwayStation/subway_station')
# Physics creation/broadphase updates for newly spawned static actors complete on later editor ticks.
u.EditorPythonScripting.set_keep_python_script_alive(True);physics_started=time.time()
def finalize(dt):
    if time.time()-physics_started<5:return
    u.unregister_slate_post_tick_callback(final_handle)
    try:
        traces=[]
        for x,y,expected in [(3900,-19770,9760),(3900,-19520,9850.667),(4200,-19520,10000),(3900,-18800,10000)]:
            h=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,10070),u.Vector(x,y,9600),u.TraceTypeQuery.ECC_VISIBILITY,False,[],u.DrawDebugTrace.NONE,True)
            z=hit_z(h);assert z is not None and abs(z-expected)<5,(x,y,z,expected);traces.append(dict(x=x,y=y,z=z))
        center,extent=island.get_actor_bounds(False)
        assert (center-old_center).length()<1 and (extent-old_extent).length()<1,('Island outer bounds changed',center,extent)
        ignore=[a for a in A.get_all_level_actors() if a!=island]
        for x,y,expected in surface_samples:
            h=u.SystemLibrary.line_trace_single(world,u.Vector(x,y,11000),u.Vector(x,y,6500),u.TraceTypeQuery.ECC_VISIBILITY,False,ignore,u.DrawDebugTrace.NONE,True)
            z=hit_z(h);assert (z is None and expected is None) or (z is not None and expected is not None and abs(z-expected)<1),('Outer island surface changed',x,y,z,expected)
        assert L.save_current_level();report['maps'].append(dict(map=EXT,unrelated_actors_unchanged=True,ground_and_shaft_traces=traces,ground_z=10000,outer_bounds_unchanged=True,outer_surface_samples_passed=len(surface_samples)))
        assert L.load_level(INT);inner_before=snapshot();assert 'SE_TravelToExterior' not in inner_before
        volume('SE_TravelToExterior',(-668,0,460),(32,185,100),EXT,(3900,-18840,10100),90,390)
        inner_after=snapshot()
        for name,data in inner_before.items():assert inner_after.get(name)==data,('Interior actor changed',name)
        assert L.save_current_level();report['maps'].append(dict(map=INT,existing_actors_unchanged=True,arrival=[-520,0,460],return_trigger=[-668,0,460]))
        (O/'placement_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');u.log('SUBWAY_PLACEMENT_OK')
    except Exception:u.log_error(traceback.format_exc())
    finally:u.SystemLibrary.quit_editor()
final_handle=u.register_slate_post_tick_callback(finalize)
