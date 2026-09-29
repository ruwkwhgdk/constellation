import bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'TripoReplacement/v002/13_Floor'
bpy.ops.wm.open_mainfile(filepath=str(p/'prepared.blend'))
obj=bpy.data.objects['SM_OH_T_13_Floor'];bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.075));col=bpy.context.object;col.name='UCX_'+obj.name+'_00';col.dimensions=(2,2,.15);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
obj.select_set(True);bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.fbx(filepath=str(p/(obj.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
col.hide_render=True;col.hide_set(True);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(p/'prepared.blend'))
