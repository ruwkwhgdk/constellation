import bpy, json, pathlib
root=pathlib.Path('C:/Users/User/Documents/UnrealProjects/Constellation')
base=root/'Saved/LittleGirlEyeRig/Inspections'
result=[]
for folder,name in [('20261019_ForeheadBoundary_01','LittleGirl_ForeheadBoundary_CANDIDATE.blend'),('20261019_SideScalp_01','LittleGirl_SideScalp_CANDIDATE.blend')]:
    path=base/folder/name
    bpy.ops.wm.open_mainfile(filepath=str(path))
    images=[]
    for im in bpy.data.images:
        if im.type in {'RENDER_RESULT','COMPOSITING'}: continue
        packed=list(im.packed_files)
        images.append(dict(name=im.name,source=im.source,filepath=im.filepath,absolute=bpy.path.abspath(im.filepath),packed=bool(im.packed_file or packed),packed_count=len(packed),size=list(im.size),users=im.users))
    result.append(dict(file=str(path),images=images,libraries=[bpy.path.abspath(x.filepath) for x in bpy.data.libraries],external_paths=list(bpy.utils.blend_paths(absolute=True,packed=False))))
(root/'docs/handoffs/bundle_dependencies.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
