import bpy,json,csv
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parents[1]/'TripoReplacement/v002'
rows=[]
for row in csv.DictReader((BASE/'jobs.csv').open()):
    out=BASE/(row['id']+'_'+row['name'])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(next((out/'Original').glob('*.fbx'))))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    ps=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    lo=Vector([min(p[i] for p in ps) for i in range(3)]); hi=Vector([max(p[i] for p in ps) for i in range(3)])
    row.update(bounds=list(hi-lo),triangles=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),objects=[o.name for o in meshes])
    rows.append(row)
    scene=bpy.context.scene; size=max(hi-lo); center=(lo+hi)/2
    scene.world=bpy.data.worlds.new('World'); scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
    for off,power in [((1,-2,3),500),((-2,1,2),350)]:
        p=center+Vector(off)*size; bpy.ops.object.light_add(type='AREA',location=p); o=bpy.context.object; o.data.energy=power*size*size; o.data.size=size*2; o.rotation_euler=(center-p).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=center+Vector((1,-3,.9))*size); cam=bpy.context.object; cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=size*1.3; scene.camera=cam
    scene.render.engine='CYCLES'; scene.cycles.samples=8; scene.render.resolution_x=400; scene.render.resolution_y=400; scene.render.resolution_percentage=100
    scene.render.filepath=str(out/'original.png'); bpy.ops.render.render(write_still=True)
(BASE/'raw_inventory.json').write_text(json.dumps(rows,indent=2))
print('RAW_KIT_INSPECTED',len(rows))
