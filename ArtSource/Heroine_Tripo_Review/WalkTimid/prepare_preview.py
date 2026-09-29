from pathlib import Path
P=Path(__file__).resolve().parent
code=(P.parent/'RigReferenceFit/preview_unreal.py').read_text()
code=code.replace("'_PreviewRelaxed'","'_Walk_Timid'").replace('Relaxed preview','Timid walk preview')
code=code.replace("'_ReferenceFit'","'_Walk_Timid'")
code=code.replace('unreal_reference_fit.png','unreal_walk_timid.png').replace('preview_result.json','walk_preview_result.json')
code=code.replace("start=time.time(); state={'capture':False}","level.pilot_level_actor(camera)\nstart=time.time(); state={'capture':False}")
(P/'preview_unreal.py').write_text(code)
