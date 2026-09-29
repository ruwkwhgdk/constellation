import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent
reports=[]
for source in [B/'RunSoft/Heroine_Run_Soft.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(source))
 reports.append({'source':str(source),'images':[{'name':i.name,'path':bpy.path.abspath(i.filepath),'packed':bool(i.packed_file),'exists':Path(bpy.path.abspath(i.filepath)).is_file()} for i in bpy.data.images if i.source=='FILE'],'libraries':[bpy.path.abspath(l.filepath) for l in bpy.data.libraries]})
(P/'blend_dependencies.json').write_text(json.dumps(reports,indent=2))
print('BLEND_DEPENDENCIES_AUDITED')
