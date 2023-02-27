"""
mods.animdata
"""
from collections import namedtuple
import sys

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

if sys.version_info >= (3, 0):
    import mods.options as options
    import mods.utils as utils
else:
    import options as options
    import utils as utils

anim_cache = None
curve_key_values = {}

KeyGroup = namedtuple('KeyGroup', 'key_index value prev_value next_value default_value tangent_points has_two_segments')


def maya_useNewAPI():
    pass


def prepare(mode):
    """
    Prepares the dictionary of animation curves along with values before/after required to interpolate.
    """
    global anim_cache
    global curve_key_values
    
    # get curves
    if utils.is_graph_editor_or_dope_sheet():
        curves = utils.get_selected_anim_curves()
        plugs = None
    else:
        nodes = utils.get_selected_objects()
        curves, plugs = utils.get_anim_curves_from_objects(nodes)
    
    # get prev and next values, so we can use them to blend while dragging slider
    is_default = bool(mode == options.BlendingMode.default)
    is_curve_tangent = bool(mode == options.BlendingMode.curve)
    
    curve_key_values = {}
    time_range = utils.get_time_slider_range()
    unit = om.MTime.uiUnit()
    mtime_range = (om.MTime(time_range[0], unit), om.MTime(time_range[1], unit))
    
    for plug_idx, curve_node in enumerate(curves):
        curve_fn = oma.MFnAnimCurve(curve_node.object())
        
        default_val = None
        if is_default:
            if plugs:
                default_val = utils.get_attribute_default_value(plugs[plug_idx])
            else:
                default_val = utils.get_anim_curve_default_value(curve_fn)
        
        key_group = KeyGroup(key_index=[],
                             value=[],
                             default_value=default_val,
                             prev_value=[],
                             next_value=[],
                             tangent_points=[],
                             has_two_segments=[])
        
        selected_keys = cmds.keyframe(str(curve_fn.absoluteName()), q=True, selected=True, indexValue=True)
        if time_range[0] - time_range[1] != 0:
            # time range selected on time slider
            indices = cmds.keyframe(str(curve_fn.absoluteName()), q=True, time=time_range, indexValue=True)
            if indices is None:
                continue
            
            if indices[0] == 0:
                prev_index = 0
            else:
                prev_index = indices[0] - 1
            
            num_keys = curve_fn.numKeys
            next_index = indices[-1] + 1
            if next_index >= num_keys:
                next_index = num_keys - 1
            
            for idx in indices:
                add_to_key_group(curve_fn, idx, prev_index, next_index, key_group)
            
            if is_curve_tangent:
                for idx in indices:
                    add_tangent_points_to_key_group(key_group, curve_fn, prev_index, next_index, idx)
            
            curve_key_values[curve_fn] = key_group
        
        elif selected_keys is not None:
            # keys selected in graph editor or dope sheet
            index_group = []
            groups = []
            
            # find groups of consecutive key indices
            index_group.append(selected_keys[0])
            for i in range(1, len(selected_keys)):
                if selected_keys[i] - selected_keys[i - 1] < 2:
                    index_group.append(selected_keys[i])
                else:
                    groups.append(index_group)
                    index_group = [selected_keys[i]]
            
            # append last iteration
            groups.append(index_group)
            
            for grp in groups:
                prev_index = max(0, grp[0] - 1)
                next_index = min(grp[-1] + 1, curve_fn.numKeys - 1)
                
                for idx in grp:
                    add_to_key_group(curve_fn, idx, prev_index, next_index, key_group)
                
                if is_curve_tangent:
                    for idx in grp:
                        add_tangent_points_to_key_group(key_group, curve_fn, prev_index, next_index, index=idx)
            
            curve_key_values[curve_fn] = key_group
        else:
            # no time range or keys selected
            current_index = curve_fn.find(mtime_range[0])
            closest_index = curve_fn.findClosest(mtime_range[0])
            closest_time = curve_fn.input(closest_index)
            if current_index is not None:
                prev_index = max(0, closest_index - 1)
                next_index = min(curve_fn.numKeys - 1, closest_index + 1)
                
                # key exists, so two curve tangent segments
                if is_curve_tangent:
                    add_tangent_points_to_key_group(key_group, curve_fn, prev_index, next_index, current_index)
            else:
                if (closest_time.value - mtime_range[0].value) <= 0:
                    prev_index = closest_index
                    next_index = closest_index + 1
                else:
                    prev_index = closest_index - 1
                    next_index = closest_index
                
                if prev_index < 0:
                    prev_index = 0
                
                # add new key
                value = curve_fn.evaluate(mtime_range[0])
                current_index = curve_fn.addKey(mtime_range[0], value, change=anim_cache)
                
                next_index = min(curve_fn.numKeys - 1, next_index + 1)
                
                # there isn't any key yet, so we only have one tangent segment and thus index=None
                if is_curve_tangent:
                    add_tangent_points_to_key_group(key_group, curve_fn, prev_index, next_index, index=current_index)
                
            add_to_key_group(curve_fn, current_index, prev_index, next_index, key_group)
            curve_key_values[curve_fn] = key_group


def add_to_key_group(curve_fn, index, prev_index, next_index, key_group):
    """
    Adds a single curve function object to the collection of keys we wish to manipulate.
    """
    value = curve_fn.value(index)
    prev_val = curve_fn.value(prev_index)
    next_val = curve_fn.value(next_index)
    
    key_group.key_index.append(index)
    key_group.value.append(value)
    key_group.prev_value.append(prev_val)
    key_group.next_value.append(next_val)


def add_tangent_points_to_key_group(key_group, curve_fn, prev_index, next_index, index=None):
    """
    Adds one or two tangent bezier point sets depending on whether index is None.
    
    If index is None, one set will be added between prev and next index.
    Otherwise two sets will be added; one between prev and current and one between current and next.
    
    :param key_group: KeyGroup
    :param curve_fn: MFnAnimCurve
    :param prev_index: Key index for the animation curve function
    :param next_index: Key index for the animation curve function
    :param index: Key index for the animation curve function
    """
    if index is None:
        key_group.has_two_segments.append(False)
        # comma to indicate tuple (my_value,)
        bezier_set = (utils.get_curve_tangents_bezier_points(curve_fn, prev_index, next_index),)
    else:
        key_group.has_two_segments.append(True)
        bezier_set = (utils.get_curve_tangents_bezier_points(curve_fn, prev_index, index),
                      utils.get_curve_tangents_bezier_points(curve_fn, index, next_index))
    
    key_group.tangent_points.append(bezier_set)
