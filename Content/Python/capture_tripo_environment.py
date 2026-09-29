from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('verify_tripo_environment.py')))
script=Path(__file__).with_name('capture_hall_exposure.py')
source=script.read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v001').replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout','/Game/Environment/OvergrownHall/TripoReplacement/Maps/L_OvergrownHall_TripoReview').replace('unreal_exposure_fixed.png','unreal_review.png')
exec(compile(source,str(script),'exec'))
