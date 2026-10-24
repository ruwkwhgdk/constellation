import bpy,json
from pathlib import Path
bpy.context.scene.frame_set(1)
rows=[]
for o in bpy.context.scene.objects:
    if o.type=="MESH" and o.data.shape_keys:
        keys=o.data.shape_keys
        rows.append({"object":o.name,"action":str(keys.animation_data.action.name if keys.animation_data and keys.animation_data.action else None),
                     "nonzero":[[k.name,k.value] for k in keys.key_blocks if k.value!=0]})
print(json.dumps(rows,ensure_ascii=False),flush=True)
rig=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
print("NONIDENTITY_BONES",json.dumps([[b.name,list(b.location),list(b.rotation_quaternion),list(b.scale)] for b in rig.pose.bones if b.matrix_basis.to_translation().length>.00001 or b.matrix_basis.to_quaternion().angle>.00001 or (b.scale-__import__('mathutils').Vector((1,1,1))).length>.00001]),flush=True)
deps=bpy.context.evaluated_depsgraph_get()
for o in bpy.context.scene.objects:
    if o.type=="MESH" and o.find_armature()==rig:
        evaluated=o.evaluated_get(deps)
        mesh=evaluated.to_mesh()
        bad=[v.index for v in mesh.vertices if (o.matrix_world@v.co).length>3]
        if bad:
            print("DISTANT_VERTICES",o.name,len(bad),bad[:12],flush=True)
        if "Hair" in o.name:
            longest=max(((mesh.vertices[e.vertices[0]].co-mesh.vertices[e.vertices[1]].co).length for e in mesh.edges),default=0)
            print("HAIR_MAX_EDGE",o.name,longest,flush=True)
        evaluated.to_mesh_clear()
