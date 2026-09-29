import unreal
from pathlib import Path
out=[]
for n in ['AnimMontageFactory','AnimMontage','AnimSegment','AnimTrack','SlotAnimationTrack','CompositeSection','AnimationLibrary']:
 obj=getattr(unreal,n,None);out.append(n+'\n'+str(getattr(obj,'__doc__','')))
out.append(str(unreal.AnimMontage.create_slot_animation_as_dynamic_montage_with_blend_settings.__doc__))
(Path(__file__).resolve().parent/'montage_api.txt').write_text('\n'.join(out),encoding='utf-8')
