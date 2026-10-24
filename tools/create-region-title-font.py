import unreal as u
from pathlib import Path
r=Path(u.Paths.project_dir())
f=u.RegionTitleEditorLibrary.create_region_font(str(r/'ArtSource/UI/RegionTitle/Fonts/NanumMyeongjo-Regular.ttf'));assert f
for path in ['/Game/Constellation/UI/RegionTitle/FF_RegionMyeongjo','/Game/Constellation/UI/RegionTitle/F_RegionMyeongjo']:assert u.EditorAssetLibrary.save_asset(path,False)
u.log('REGION_FONT_CREATED')
