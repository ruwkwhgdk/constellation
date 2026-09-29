level.pilot_level_actor(camera)
assert comp.get_editor_property('skeletal_mesh_asset').get_path_name()==B+'/SK_'+N+'.SK_'+N
assert '/RigReferenceFit/' in mesh.get_editor_property('asset_import_data').get_first_filename()
assert abs(comp.get_socket_location('upperarm_l').z-128.05724)<0.01
(P/'final_live_verification.json').write_text(json.dumps({'pass':True,'mesh':mesh.get_path_name(),'shoulder_z_cm':comp.get_socket_location('upperarm_l').z,'map_saved':True},indent=2))
unreal.unregister_slate_post_tick_callback(bridge_handle)
