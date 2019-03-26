"""
tween module - the methods that does the actual work
"""
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

import mods.utils as utils
import mods.data as data


def maya_useNewAPI():
    pass


def interpolate(t, t_type):
    if t_type == 'towards':
        interpolate_towards(t)
    
    if t_type == 'between':
        interpolate_between(t)
    
    if t_type == 'curve':
        interpolate_curve_tangent(t)
    
    if t_type == 'default':
        interpolate_default(t)


def interpolate_towards(t):
    for curve_fn, key_group in data.curve_key_values.iteritems():
        for i in range(len(key_group.key_index)):
            new_value = lerp_towards(key_group.prev_value[i], key_group.next_value[i], t, key_group.value[i])
            curve_fn.setValue(key_group.key_index[i], new_value, change=data.anim_cache)


def interpolate_between(t):
    for curve_fn, key_group in data.curve_key_values.iteritems():
        for i in range(len(key_group.key_index)):
            new_value = lerp_between(key_group.prev_value[i], key_group.next_value[i], t)
            curve_fn.setValue(key_group.key_index[i], new_value, change=data.anim_cache)


def interpolate_curve_tangent(t):
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
    
    for curve_fn, key_group in data.curve_key_values.iteritems():
        for i in range(len(key_group.key_index)):
            if key_group.has_two_segments[i]:
                if t < 0.5:
                    p = key_group.tangent_points[i][0]
                    new_value = t1p0 * p[0].y + t1p1 * p[1].y + t1p2 * p[2].y + t1p3 * p[3].y
                else:
                    p = key_group.tangent_points[i][1]
                    new_value = t2p0 * p[0].y + t2p1 * p[1].y + t2p2 * p[2].y + t2p3 * p[3].y
            else:
                p = key_group.tangent_points[i][0]
                new_value = tp0 * p[0].y + tp1 * p[1].y + tp2 * p[2].y + tp3 * p[3].y
            
            curve_fn.setValue(key_group.key_index[i], new_value, data.anim_cache)


def interpolate_default(t):
    for curve_fn, key_group in data.curve_key_values.iteritems():
        for i in range(len(key_group.key_index)):
            if key_group.default_value is None:
                continue
            
            new_value = lerp_towards(key_group.value[i] * 2 - key_group.default_value,
                                     key_group.default_value,
                                     t, key_group.value[i])
            curve_fn.setValue(key_group.key_index[i], new_value, change=data.anim_cache)


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
    t_remapped = t * 0.5 + 0.5
    
    return a + (b - a) * t_remapped


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
        tRemapped = t * 2.0 + 1.0  # remap [-1;0] to [-1;1]
        return lerp_between(a, current, tRemapped)
    elif t > 0:
        tRemapped = t * 2.0 - 1.0  # remap [0;1] to [-1;1]
        return lerp_between(current, b, tRemapped)
    else:
        return current
