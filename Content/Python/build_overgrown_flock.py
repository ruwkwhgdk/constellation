"""Repeatable, map-local flock choreography using native Sequencer tracks."""
import unreal as u, json, math
from pathlib import Path
P=globals().get('FLOCK_DEST','/Game/Environment/OvergrownHall/Production'); B='/Game/Environment/OvergrownHall/Bird/Tripo'
E=u.EditorAssetLibrary; L=u.get_editor_subsystem(u.LevelEditorSubsystem); A=u.get_editor_subsystem(u.EditorActorSubsystem)
AT=u.AssetToolsHelpers.get_asset_tools()
assert L.load_level(P+'/Maps/'+globals().get('FLOCK_MAP','L_OvergrownHall_Detail'))
for actor in A.get_all_level_actors():
    if actor.get_actor_label().startswith('OH_Flock_'): A.destroy_actor(actor)
path=P+'/Sequences/LS_OvergrownHall_Flock'
seq=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset('LS_OvergrownHall_Flock',P+'/Sequences',u.LevelSequence,u.LevelSequenceFactoryNew())
seq.modify()
for binding in seq.get_bindings(): binding.remove()
seq.set_display_rate(u.FrameRate(48,1)); seq.set_tick_resolution_directly(u.FrameRate(24000,1))
seq.set_playback_start(0); seq.set_playback_end(960)
mesh=E.load_asset(B+'/Meshes/SK_OH_Pigeon'); clips={n:E.load_asset(B+'/Clips/A_OH_Pigeon_'+n) for n in ['Fly','Glide','FlyToGlide','GlideToFly']}
assert mesh and all(clips.values())
rows=[]
for i in range(12):
    actor=A.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(0,0,500),u.Rotator())
    actor.set_actor_label('OH_Flock_Bird_%02d'%(i+1)); c=actor.skeletal_mesh_component
    c.set_skeletal_mesh_asset(mesh); c.set_mobility(u.ComponentMobility.MOVABLE); c.set_collision_profile_name('NoCollision')
    binding=seq.add_possessable(actor)
    track=binding.add_track(u.MovieScene3DTransformTrack); section=track.add_section(); section.set_range(0,961)
    channels=section.get_all_channels(); samples=[]; previous=None
    for frame in range(0,961,8):
        angle=math.tau*(frame/960+i/12)
        rx=270+10*i; ry=320+4*i
        x=rx*math.cos(angle); y=970+ry*math.sin(angle); z=360+25*i+15*math.sin(2*angle)
        dx=-rx*math.sin(angle); dy=ry*math.cos(angle); dz=30*math.cos(2*angle)
        yaw=math.degrees(math.atan2(dy,dx))-90
        if previous is not None:
            while yaw-previous>180: yaw-=360
            while yaw-previous< -180: yaw+=360
        previous=yaw
        # Mesh imported from Blender faces UE +Y; roll pitches this local forward axis.
        values=[x,y,z,math.degrees(math.atan2(dz,math.hypot(dx,dy))),0,yaw,1,1,1]
        for channel,value in zip(channels,values):
            channel.add_key(u.FrameNumber(frame),value,interpolation=u.MovieSceneKeyInterpolation.LINEAR)
        samples.append(dict(frame=frame,position_cm=[x,y,z],rotation_xyz=values[3:6]))
    actor.set_actor_location(u.Vector(*samples[0]['position_cm']),False,False)
    actor.set_actor_rotation(u.Rotator(pitch=0,yaw=samples[0]['rotation_xyz'][2],roll=samples[0]['rotation_xyz'][0]),False)
    anim=binding.add_track(u.MovieSceneSkeletalAnimationTrack)
    offset=i*2
    for name,start,end in [('Fly',-offset,192-offset),('FlyToGlide',192-offset,204-offset),('Glide',204-offset,276-offset),('GlideToFly',276-offset,288-offset),('Fly',288-offset,960)]:
        s=anim.add_section(); s.set_range(start,end); params=s.get_editor_property('params'); params.animation=clips[name]; s.set_editor_property('params',params)
    rows.append(dict(name=actor.get_actor_label(),samples=samples,phase_offset_frames=offset))
# Geometric guard for this prescribed choreography (not dynamic avoidance).
minimum=min(math.dist(a['samples'][j]['position_cm'],b['samples'][j]['position_cm']) for i,a in enumerate(rows) for b in rows[i+1:] for j in range(121))
assert minimum>80,minimum
player=A.spawn_actor_from_class(u.LevelSequenceActor,u.Vector(),u.Rotator()); player.set_actor_label('OH_Flock_Sequence'); player.set_sequence(seq)
settings=player.get_editor_property('playback_settings'); settings.auto_play=True; settings.loop_count=u.MovieSceneSequenceLoopCount(-1); player.set_editor_property('playback_settings',settings)
assert E.save_loaded_asset(seq,only_if_is_dirty=False); assert L.save_current_level()
folder=Path(globals().get('FLOCK_OUT',Path(u.Paths.project_dir())/'ArtSource/OvergrownHall/Bird/Flock_v001')); folder.mkdir(exist_ok=True)
(folder/'routes.json').write_text(json.dumps(dict(seconds=20,fps=48,birds=rows,minimum_center_distance_cm=minimum),indent=2))
u.log('FLOCK_BUILD_PASS min_spacing_cm='+str(minimum))
