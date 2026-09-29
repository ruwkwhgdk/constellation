import unreal
from pathlib import Path
p=Path(__file__).resolve().parent
(p/'notify_api.txt').write_text(str(unreal.AnimNotifyEvent.__doc__)+'\n'+str(unreal.AnimationLibrary.add_animation_notify_event_from_source.__doc__)+'\n'+str(unreal.AnimationLibrary.add_animation_notify_event.__doc__)+'\n'+str(unreal.AnimationLibrary.add_animation_notify_event_object.__doc__),encoding='utf-8')
