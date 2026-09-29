"""Map-local luminance lock, independent of the project's EV100 UI mode."""
import unreal as u,math
def apply_hall_exposure(volume):
    extended=u.SystemLibrary.get_console_variable_int_value('r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange')!=0
    attenuation=u.SystemLibrary.get_console_variable_float_value('r.EyeAdaptation.LensAttenuation')
    luminance_max=.78/max(attenuation,.01)
    white_point=1024.0
    value=math.log2(white_point/luminance_max) if extended else white_point
    s=volume.get_editor_property('settings')
    for key,val in [('override_auto_exposure_method',True),('auto_exposure_method',u.AutoExposureMethod.AEM_HISTOGRAM),('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',value),('auto_exposure_max_brightness',value),('override_auto_exposure_bias',True),('auto_exposure_bias',0.0)]:
        s.set_editor_property(key,val)
    volume.modify(); volume.set_editor_property('settings',s)
    volume.set_editor_property('priority',10.0)
    return dict(extended_luminance=extended,stored_value=value,white_point_luminance=white_point,exposure_bias=0)
