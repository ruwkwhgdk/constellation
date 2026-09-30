import unreal as u
from pathlib import Path
root=Path(u.Paths.project_dir())
SOURCE_DIR=root/'ArtSource/OvergrownHall/Production/v001'
MAP_PATH='/Game/Constellation/Environments/OvergrownHall/Production/Maps/L_OvergrownHall_Detail'
script=root/'Content/Python/verify_overgrown_hall_blockout.py'
exec(compile(script.read_text(),str(script),'exec'),globals())
