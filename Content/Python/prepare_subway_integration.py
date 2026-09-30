"""Read-only geometry and travel-site inventory. Never saves maps."""
import unreal as u,json,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'ArtSource/SubwayEntrance/Design'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
report={}
for map_name in ['/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland','/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2']:
    file=R/'Content'/ (map_name.removeprefix('/Game/')+'.umap');before=hashlib.sha256(file.read_bytes()).hexdigest()
    assert L.load_level(map_name);rows=[]
    for a in A.get_all_level_actors():
        p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d();c,e=a.get_actor_bounds(False)
        if map_name.endswith('L_StartIsland') and a.get_actor_label() not in ['sky_island','subway_station']:continue
        row=dict(label=a.get_actor_label(),class_name=a.get_class().get_name(),position=[p.x,p.y,p.z],rotation=[r.pitch,r.yaw,r.roll],scale=[s.x,s.y,s.z],center=[c.x,c.y,c.z],extent=[e.x,e.y,e.z])
        if isinstance(a,u.StaticMeshActor):
            mesh=a.static_mesh_component.static_mesh;row['mesh']=mesh.get_path_name() if mesh else None
            row['materials']=[a.static_mesh_component.get_material(i).get_path_name() if a.static_mesh_component.get_material(i) else None for i in range(a.static_mesh_component.get_num_materials())]
        if a.get_actor_label()=='sky_island':
            t=u.AssetExportTask();t.object=mesh;t.filename=str(O/'existing_island.fbx');t.automated=True;t.prompt=False;t.replace_identical=True;t.exporter=u.StaticMeshExporterFBX();t.options=u.FbxExportOption();assert u.Exporter.run_asset_export_task(t)
            verts=[];tris=[]
            for i in range(mesh.get_num_sections(0)):
                section=u.ProceduralMeshLibrary.get_section_from_static_mesh(mesh,0,i);offset=len(verts)
                for v in section[0]:
                    w=u.MathLibrary.transform_location(a.get_actor_transform(),v);verts.append([w.x,w.y,w.z])
                tris.extend(int(j)+offset for j in section[1])
            (O/'island_world_mesh.json').write_text(json.dumps(dict(vertices=verts,triangles=tris)),encoding='utf-8')
        rows.append(row)
    assert before==hashlib.sha256(file.read_bytes()).hexdigest()
    report[map_name]=dict(actors=rows,sha256=before,saved=False)
(O/'integration_survey.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
u.log('SUBWAY_INTEGRATION_SURVEY_OK')
