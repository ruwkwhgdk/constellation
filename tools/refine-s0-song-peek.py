import unreal as u,json,shutil
from pathlib import Path
P=lambda o,k:o.get_editor_property(k)
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');s=list(P(a,'steps'));c=s[45];assert P(c,'type')==u.DirectorNodeType.CAMERA_MOVE
pts=list(P(c,'motion_points'));pts[-1].set_editor_property('position',u.Vector(3165,0,218.1));pts[-1].set_editor_property('rotation',u.Vector(0,-15,180));c.set_editor_property('motion_points',pts)
d=P(c,'destination');d.set_editor_property('value',u.Vector(3165,0,218.1));c.set_editor_property('destination',d)
r=P(c,'rotation');r.set_editor_property('value',u.Vector(0,-15,180));c.set_editor_property('rotation',r)
a.set_editor_property('steps',s);result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result,result;assert u.EditorAssetLibrary.save_loaded_asset(a,False)
u.log('SONG_PEEK_REFINED '+result)


