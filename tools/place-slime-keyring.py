import unreal as u,json,shutil,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/SlimeKeyring';A=u.get_editor_subsystem(u.EditorActorSubsystem)
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
before=hashlib.sha256(mapfile.read_bytes()).hexdigest()
backup=O/'AbandonedSchool-before-slime.umap'
assert not backup.exists(),'Already applied; inspect existing result before rerunning.'
shutil.copy2(mapfile,backup)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
aa=A.get_all_level_actors();by={a.get_actor_label():a for a in aa};old=[a for a in aa if a.get_actor_label().startswith('S0_Charm_')];assert len(old)==5
mesh=u.load_asset('/Game/Constellation/Environments/School/Props/slime_keyring/SM_slime_keyring');assert mesh
a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(3161,-49,184),u.Rotator(yaw=-90));a.set_actor_label('slime_keyring');a.set_folder_path('S0 Opening/Props')
c=a.static_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_static_mesh(mesh);a.set_actor_scale3d(u.Vector(.2,.2,.2));a.set_actor_enable_collision(False)
a.attach_to_actor(by['S0_LockerDoor'],'',u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
for actor in old:assert A.destroy_actor(actor)
assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==before,'Map changed in another process; do not overwrite'
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(O/'placed.json').write_text(json.dumps(dict(label=a.get_actor_label(),mesh=mesh.get_path_name(),parent=a.get_attach_parent_actor().get_actor_label(),transform=str(a.get_actor_transform()),replaced=5),indent=2))
u.log('SLIME_PLACED')
