import unreal as u
from pathlib import Path
root=Path(u.Paths.project_dir())
SOURCE_DIR=root/'ArtSource/OvergrownHall/Production/v001'
DESTINATION='/Game/Constellation/Environments/OvergrownHall/Production'
MAP_NAME='L_OvergrownHall_Detail'
script=root/'Content/Python/import_overgrown_hall_blockout.py'
exec(compile(script.read_text(),str(script),'exec'),globals())
