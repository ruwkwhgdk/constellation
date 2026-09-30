"""Export the selected placeholder for orientation analysis, without saving the map."""
import unreal as u, json, hashlib
from pathlib import Path
root=Path(u.Paths.project_dir())
out=root/'ArtSource/SubwayEntrance/Design'
f=root/'Content/Levels/L_StartIsland.umap'
before=hashlib.sha256(f.read_bytes()).hexdigest()
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
a=[a for a in actors if a.get_actor_label()=='subway_station']
assert len(a)==1
a=a[0]; p=a.get_actor_location(); r=a.get_actor_rotation(); s=a.get_actor_scale3d()
assert (p-u.Vector(3900,-19500,10530)).length()<1
t=u.AssetExportTask(); t.object=a.static_mesh_component.static_mesh
t.filename=str(out/'existing_dummy.fbx');t.automated=True;t.prompt=False;t.replace_identical=True
t.exporter=u.StaticMeshExporterFBX();t.options=u.FbxExportOption()
assert u.Exporter.run_asset_export_task(t)
data=dict(label=a.get_actor_label(),location=[p.x,p.y,p.z],rotation_pitch_yaw_roll=[r.pitch,r.yaw,r.roll],scale=[s.x,s.y,s.z],mesh=a.static_mesh_component.static_mesh.get_path_name(),map_saved=False)
vertices=[]
for section in range(a.static_mesh_component.static_mesh.get_num_sections(0)):
    vertices.extend(u.ProceduralMeshLibrary.get_section_from_static_mesh(a.static_mesh_component.static_mesh,0,section)[0])
data['native_vertices_cm']=[[v.x,v.y,v.z] for v in vertices]
assert hashlib.sha256(f.read_bytes()).hexdigest()==before
(out/'placement_target.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
u.log('SUBWAY_DUMMY_EXPORT_OK')
