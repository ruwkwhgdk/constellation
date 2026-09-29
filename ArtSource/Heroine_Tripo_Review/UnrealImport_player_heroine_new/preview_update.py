for filename in ['preview_error.txt','preview_update_error.txt']:
 error_file=P/filename
 if error_file.exists():error_file.unlink()
unreal.EditorAssetLibrary.sync_browser_to_objects([B+'/SK_'+N])
unreal.unregister_slate_post_tick_callback(bridge_handle)
(P/'preview_session_complete.json').write_text(json.dumps({'completed':True,'editor_left_open':True,'map':world.get_path_name(),'preview_image':str(P/'unreal_preview.png'),'physics_status':'preliminary 3-body asset; ragdoll not tuned'},indent=2))
