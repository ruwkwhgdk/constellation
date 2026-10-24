import unreal as u,json,time,traceback,shutil
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();O=R/'Saved/SwordAcquisition/AnimationIntegration';O.mkdir(parents=True,exist_ok=True)
backup=O/('Backup-'+time.strftime('%Y%m%d-%H%M%S'))
def save_backup(p,ext='.uasset'):
 src=R/'Content'/(p.removeprefix('/Game/')+ext)
 if src.exists():
  dst=backup/src.relative_to(R/'Content');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
try:
 map_path='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool';save_backup(map_path,'.umap')
 world=u.EditorLoadingAndSavingUtils.load_map(map_path);actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors();stage=next(a for a in actors if isinstance(a,u.SwordAcquisitionStage));sword=stage.get_editor_property('sword')
 comp=next(c for c in sword.get_components_by_class(u.StaticMeshComponent) if c.static_mesh and c.static_mesh.get_name()=='SM_Weapon_Sword')
 task=u.AssetExportTask();task.set_editor_property('object',comp.static_mesh);task.set_editor_property('exporter',u.StaticMeshExporterOBJ());task.set_editor_property('filename',str(O/'SwordMesh.obj'));task.set_editor_property('automated',True);task.set_editor_property('prompt',False);task.set_editor_property('replace_identical',True)
 assert u.Exporter.run_asset_export_task(task)
 # OBJ exporter coordinates are inspected separately before final asset installation.
 data=json.loads((R/'ArtSource/SwordAcquisition/HeroineDelivery/sword_tracks.json').read_text())
 path='/Game/SceneDirector/School/DA_SwordAcquisitionAnimation';save_backup(path);asset=u.load_asset(path)
 if not asset:
  factory=u.DataAssetFactory();factory.set_editor_property('data_asset_class',u.SwordAcquisitionAnimationSet);asset=u.AssetToolsHelpers.get_asset_tools().create_asset(path.split('/')[-1],'/Game/SceneDirector/School',u.SwordAcquisitionAnimationSet,factory)
 clips={}
 for name,clip in data['clips'].items():
  c=u.SwordAcquisitionClip();c.set_editor_property('montage',u.load_asset('/Game/Constellation/Characters/Heroine/GamePilot/SwordAcquisition/AM_Sword_'+name));c.set_editor_property('loop',clip['loop'])
  samples=[]
  for row in clip['sword']:
   t=u.Transform(location=u.Vector(*row['t']),rotation=u.Quat(*row['q']).rotator(),scale=u.Vector(*row['s']));samples.append(t)
  c.set_editor_property('sword_samples',samples);clips[u.Name(name)]=c
 asset.set_editor_property('clips',clips);asset.set_editor_property('sample_rate',data['fps'])
 # Exported OBJ uses X,Z,Y; broadest crossguard vertices identify its centre.
 verts=[list(map(float,l.split()[1:4])) for l in (O/'SwordMesh.obj').read_text().splitlines() if l.startswith('v ')]
 bounds=comp.static_mesh.get_bounding_box();axis=max(range(3),key=lambda j:max(v[j] for v in verts)-min(v[j] for v in verts))
 lateral=0;wide=max(abs(v[lateral]) for v in verts);guard=[v[axis] for v in verts if abs(v[lateral])>wide*.92];guard_z=sum(guard)/len(guard)
 # The mesh's upright direction is positive Z; check exported sign against bounds.
 assert abs(max(v[axis] for v in verts)-bounds.max.z)<1,'OBJ up axis/sign mismatch'
 scale=30./(bounds.max.z-guard_z)
 # Preserve grip width; the slightly longer blade reaches into the platform.
 z_scale=max(scale,.55)
 mesh_to_guard=u.Transform(location=u.Vector(0,0,-guard_z*z_scale),scale=u.Vector(scale,scale,z_scale))
 asset.set_editor_property('mesh_to_guard',mesh_to_guard);assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
 stage.set_editor_property('animation_set',asset)
 first=data['clips']['Approach']['sword'][0];anchor=sword.get_actor_location();hero=u.Transform(location=u.Vector(anchor.x+first['t'][0],anchor.y+first['t'][1],890.2),rotation=u.Rotator(yaw=180));stage.set_editor_property('heroine_transform',hero)
 mesh_world=u.Transform(location=hero.translation+u.Vector(0,0,-90),rotation=u.Rotator(yaw=180))
 # Transform multiplication uses local * parent in Unreal.
 prop=u.Transform(location=u.Vector(*first['t']),rotation=u.Quat(*first['q']).rotator(),scale=u.Vector(*first['s']))
 comp.set_mobility(u.ComponentMobility.MOVABLE);comp.set_world_transform(u.MathLibrary.compose_transforms(u.MathLibrary.compose_transforms(mesh_to_guard,prop),mesh_world),False,True)
 graph_path='/Game/SceneDirector/School/DA_SwordAcquisition';save_backup(graph_path);graph=u.load_asset(graph_path);steps=list(graph.get_editor_property('steps'))
 cameras=list(graph.get_editor_property('cameras'))
 for camera in cameras:
  if str(camera.get_editor_property('key'))=='C':
   pos=u.Vector(-11303,-239,962.2);target=u.Vector(-10978,121,952.2)
   camera.set_editor_property('transform',u.Transform(location=pos,rotation=u.MathLibrary.find_look_at_rotation(pos,target)))
 graph.set_editor_property('cameras',cameras)
 # Stage owns exact clip durations; authored waits only leave a short visual beat.
 after=None
 for s in steps:
  if s.get_editor_property('type')==u.DirectorNodeType.GAME_ACTION:after=str(s.get_editor_property('action_parameters').get_editor_property('identifier'))
  elif s.get_editor_property('type')==u.DirectorNodeType.WAIT and after in ['Grip','Pull','RaiseHold','Lower']:
   s.set_editor_property('duration',.2 if after!='Grip' else .4);after=None
 graph.set_editor_property('steps',steps);u.SceneDirectorLibrary.compile_director(graph);assert not graph.get_editor_property('needs_compile');assert u.EditorAssetLibrary.save_loaded_asset(graph,False)
 assert u.EditorLoadingAndSavingUtils.save_map(world,map_path)
 (O/'installed.json').write_text(json.dumps(dict(clips=list(data['clips']),guard_mesh_z=guard_z,uniform_scale=scale,hero=str(hero),backup=str(backup)),indent=2))
except:(O/'install-error.txt').write_text(traceback.format_exc());u.log_error(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
