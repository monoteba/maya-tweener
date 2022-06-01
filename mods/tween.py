"""
tween module - the methods that does the actual work
"""
import sys

import maya.api.OpenMaya as om
import maya.cmds as cmds

if sys.version_info >= (3, 0):
    import mods.utils as utils
    import mods.animdata as animdata
    import mods.options as options
else:
    import utils as utils
    import animdata as animdata
    import options as options


def maya_useNewAPI():
    pass


def interpolate(blend, mode):
    """
    Gateway for calling the function based on interpolation type.
    """
    
    if mode == options.BlendingMode.between:
        interpolate_between(blend)
    
    elif mode == options.BlendingMode.towards:
        interpolate_towards(blend)
    
    elif mode == options.BlendingMode.average:
        interpolate_average(blend)
    
    elif mode == options.BlendingMode.curve:
        interpolate_curve_tangent(blend)
    
    elif mode == options.BlendingMode.default:
        interpolate_default(blend)


def interpolate_between(t):
    """
    Linearly interpolate between neighbouring values.
    """
    
    for curve_fn, key_group in animdata.curve_key_values.items():
        for i in range(len(key_group.key_index)):
            new_value = lerp_between(key_group.prev_value[i],
                                     key_group.next_value[i], t)
            curve_fn.setValue(key_group.key_index[i], new_value,
                              change=animdata.anim_cache)


def interpolate_towards(t):
    """
    Interpolate towards the neighbouring values, based on current value.
    """
    
    for curve_fn, key_group in animdata.curve_key_values.items():
        for i in range(len(key_group.key_index)):
            new_value = lerp_towards(key_group.prev_value[i],
                                     key_group.next_value[i], t,
                                     key_group.value[i])
            curve_fn.setValue(key_group.key_index[i], new_value,
                              change=animdata.anim_cache)


def interpolate_average(t):
    """
    Interpolate towards or away from the average value
    """
    
    for curve_fn, key_group in animdata.curve_key_values.items():
        length = len(key_group.key_index)
        is_single = length < 2
        avg_val = 0
        if not is_single:
            avg_val = sum(key_group.value) / float(length)
        for i in range(length):
            if is_single:
                avg_val = (key_group.prev_value[i] + key_group.next_value[
                    i]) * 0.5
            prev_val = key_group.value[i] * 2 - avg_val
            new_value = lerp_towards(prev_val, avg_val, t, key_group.value[i])
            curve_fn.setValue(key_group.key_index[i], new_value,
                              change=animdata.anim_cache)


def interpolate_curve_tangent(t):
    """
    Interpolate based on key tangents.
    """
    
    # pre-calculate certain repeated values
    t = (t + 1) * 0.5  # single segment
    tp0 = pow(1 - t, 3)
    tp1 = 3 * t * pow(1 - t, 2)
    tp2 = 3 * pow(t, 2) * (1 - t)
    tp3 = pow(t, 3)
    
    t1 = t * 2.0  # left segment
    t1p0 = pow(1 - t1, 3)
    t1p1 = 3 * t1 * pow(1 - t1, 2)
    t1p2 = 3 * pow(t1, 2) * (1 - t1)
    t1p3 = pow(t1, 3)
    
    t2 = t * 2.0 - 1.0  # right segment
    t2p0 = pow(1 - t2, 3)
    t2p1 = 3 * t2 * pow(1 - t2, 2)
    t2p2 = 3 * pow(t2, 2) * (1 - t2)
    t2p3 = pow(t2, 3)
    
    for curve_fn, key_group in animdata.curve_key_values.items():
        for i in range(len(key_group.key_index)):
            if key_group.has_two_segments[i]:
                if t < 0.5:
                    p = key_group.tangent_points[i][0]
                    new_value = t1p0 * p[0].y + t1p1 * p[1].y + t1p2 * p[
                        2].y + t1p3 * p[3].y
                else:
                    p = key_group.tangent_points[i][1]
                    new_value = t2p0 * p[0].y + t2p1 * p[1].y + t2p2 * p[
                        2].y + t2p3 * p[3].y
            else:
                p = key_group.tangent_points[i][0]
                new_value = tp0 * p[0].y + tp1 * p[1].y + tp2 * p[2].y + tp3 * \
                            p[3].y
            
            curve_fn.setValue(key_group.key_index[i], new_value,
                              animdata.anim_cache)


def interpolate_default(t):
    """
    Interpolate towards or away from the attributes default value.
    """
    
    for curve_fn, key_group in animdata.curve_key_values.items():
        for i in range(len(key_group.key_index)):
            if key_group.default_value is None:
                continue
            
            new_value = lerp_towards(
                key_group.value[i] * 2 - key_group.default_value,
                key_group.default_value,
                t, key_group.value[i])
            curve_fn.setValue(key_group.key_index[i], new_value,
                              change=animdata.anim_cache)


def lerp_between(a, b, t):
    """
    Linear interpolate between a and b in range [-1;1]

    :param float a: first value
    :param float b: second value
    :param float t: fraction value, a = -1, b = 1 (unclamped)
    :return: value between a and b
    :rtype: float
    """
    
    # remap t to [0;1] from [-1;1]
    t = t * 0.5 + 0.5
    return a + (b - a) * t


def lerp_towards(a, b, t, current):
    """
    Linear interpolate towards a or b from current in range [-1;1]

    :param float a: first value
    :param float b: second value
    :param float t: fraction value, a = -1, b = 1 (unclamped)
    :param float current: neutral value
    :return: value between a and current, or b and current
    :rtype: float
    """

    if t < 0:
        t = t * 2.0 + 1.0  # remap [-1;0] to [-1;1]
        return lerp_between(a, current, t)
    elif t > 0:
        t = t * 2.0 - 1.0  # remap [0;1] to [-1;1]
        return lerp_between(current, b, t)
    else:
        return current


def tick_draw_special(special=True):
    """
    Makes the currently selected keyframes use the special tick color
    """
    
    # set tick color of selected keys in graph editor or dopesheet
    if utils.is_graph_editor_or_dope_sheet():
        cmds.keyframe(tds=special)
        return

    # check if any keys are selected (not allowed when setting tds on time range)
    sl_list = om.MGlobal.getActiveSelectionList()
    it = om.MItSelectionList(sl_list, om.MFn.kAnimCurve)
    
    # clear the active key selection (if needed)
    if not it.isDone():
        cmds.selectKey(clear=True)
    
    # color the keys on the time slider
    time_range = utils.get_time_slider_range()
    cmds.keyframe(tds=special, t=time_range)
    
    # restore previous selection (if needed)
    if not it.isDone():
        om.MGlobal.setActiveSelectionList(sl_list)
