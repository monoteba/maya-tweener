"""
tween module - the methods that does the actual work
"""
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds
import maya.mel as mel
from collections import namedtuple

anim_cache = None
curve_key_values = {}

KeyGroup = namedtuple('KeyGroup', 'key_index value prev_value next_value default_value py0 py1 py2 py3')


def prepare(t_type):
    global curve_key_values
    
    # get curves
    if is_graph_editor():
        curves = get_curves()
    else:
        curves = get_curves_from_objects()
    
    # get prev and next values so we can use them to blend while dragging slider
    is_default = bool(t_type == 'default')
    is_curve_tangent = bool(t_type == 'curve')
    
    curve_key_values = {}
    time_range = get_time_slider_range()
    mtime_range = (om.MTime(time_range[0]), om.MTime(time_range[1]))
    
    for curve_node in curves:
        curve_fn = oma.MFnAnimCurve(curve_node.object())
        
        default_val = None
        if is_default:
            default_val = get_default_value(curve_fn)
        
        key_group = KeyGroup(key_index=[],
                             value=[],
                             default_value=default_val,
                             prev_value=[],
                             next_value=[],
                             py0=[],
                             py1=[],
                             py2=[],
                             py3=[])
        
        selected_keys = cmds.keyframe(str(curve_fn.absoluteName()), q=True, selected=True, indexValue=True)
        if time_range[0] - time_range[1] != 0:
            # time range selected on time slider
            indices = cmds.keyframe(str(curve_fn.name()), q=True, time=time_range, iv=True)
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
                add_to_key_group(curve_fn, idx, prev_index, next_index, key_group, is_curve_tangent)
            
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
            
            num_keys = curve_fn.numKeys
            for grp in groups:
                prev_index = grp[0] - 1
                next_index = grp[-1] + 1
                
                if prev_index < 0:
                    prev_index = 0
                
                if next_index >= num_keys:
                    next_index = num_keys - 1
                
                for idx in grp:
                    add_to_key_group(curve_fn, idx, prev_index, next_index, key_group, is_curve_tangent)
            
            curve_key_values[curve_fn] = key_group
        else:
            # no time range or keys selected
            current_index = curve_fn.find(mtime_range[0])
            closest_index = curve_fn.findClosest(mtime_range[0])
            closest_time = curve_fn.input(closest_index)
            if current_index is not None:
                prev_index = closest_index - 1
                next_index = closest_index + 1
            else:
                if (closest_time.value - mtime_range[0].value) <= 0:
                    prev_index = closest_index
                    next_index = closest_index + 1
                else:
                    prev_index = closest_index - 1
                    next_index = closest_index
                
                value = curve_fn.evaluate(mtime_range[0])
                current_index = curve_fn.addKey(mtime_range[0], value, change=anim_cache)
                next_index = next_index + 1
            
            if prev_index < 0:
                prev_index = 0
            
            num_keys = curve_fn.numKeys
            if next_index >= num_keys:
                next_index = num_keys - 1
            
            add_to_key_group(curve_fn, current_index, prev_index, next_index, key_group, is_curve_tangent)
            curve_key_values[curve_fn] = key_group


def add_to_key_group(curve_fn, index, prev_index, next_index, key_group, is_curve_tangent):
    value = curve_fn.value(index)
    prev_val = curve_fn.value(prev_index)
    next_val = curve_fn.value(next_index)
    
    if is_curve_tangent:
        p0 = curve_fn.value(prev_index)
        p3 = curve_fn.value(next_index)
        
        p1 = curve_fn.getTangentXY(prev_index, False)  # inTangent = False
        p1 = p1[1] / 3 + p0
        
        p2 = curve_fn.getTangentXY(next_index, True)  # inTangent = True
        p2 = -p2[1] / 3 + p3
        
        key_group.py0.append(p0)
        key_group.py1.append(p1)
        key_group.py2.append(p2)
        key_group.py3.append(p3)
    
    key_group.key_index.append(index)
    key_group.value.append(value)
    key_group.prev_value.append(prev_val)
    key_group.next_value.append(next_val)


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
    for curve_fn, key_group in curve_key_values.iteritems():
        for i in range(len(key_group.key_index)):
            new_value = lerp_towards(key_group.prev_value[i], key_group.next_value[i], t, key_group.value[i])
            curve_fn.setValue(key_group.key_index[i], new_value, change=anim_cache)


def interpolate_between(t):
    for curve_fn, key_group in curve_key_values.iteritems():
        for i in range(len(key_group.key_index)):
            new_value = lerp_between(key_group.prev_value[i], key_group.next_value[i], t)
            curve_fn.setValue(key_group.key_index[i], new_value, change=anim_cache)


def interpolate_curve_tangent(t):
    t = (t + 1) * 0.5
    tp0 = pow(1 - t, 3)
    tp1 = 3 * t * pow(1 - t, 2)
    tp2 = 3 * pow(t, 2) * (1 - t)
    tp3 = pow(t, 3)
    for curve_fn, key_group in curve_key_values.iteritems():
        for i in range(len(key_group.key_index)):
            new_value = tp0 * key_group.py0[i] + tp1 * key_group.py1[i] + tp2 * key_group.py2[i] + tp3 * \
                        key_group.py3[i]
            curve_fn.setValue(key_group.key_index[i], new_value, anim_cache)


def interpolate_default(t):
    for curve_fn, key_group in curve_key_values.iteritems():
        for i in range(len(key_group.key_index)):
            if key_group.default_value is None:
                continue
            
            new_value = lerp_towards(key_group.value[i] * 2 - key_group.default_value,
                                     key_group.default_value,
                                     t, key_group.value[i])
            curve_fn.setValue(key_group.key_index[i], new_value, change=anim_cache)


def get_curves(sl_filter=om.MFn.kAnimCurve):
    """
    Get selected animation curves.

    We only want to modify the following animCurve types: TL, TA, TU, TT
    - UL, UA, UU, UT are used for set driven keys
    :param sl_filter: selection filter
    :return: list of curve nodes
    """
    sl_list = om.MGlobal.getActiveSelectionList()
    it = om.MItSelectionList(sl_list, sl_filter)
    
    curve_dict = {}
    
    while not it.isDone():
        item = it.itemType()
        if item == it.kDagSelectionItem or \
                item == it.kAnimSelectionItem or \
                item == it.kDNselectionItem:
            obj = it.getDependNode()
            curve_type = obj.apiType()
            if curve_type == om.MFn.kAnimCurveTimeToAngular or \
                    curve_type == om.MFn.kAnimCurveTimeToDistance or \
                    curve_type == om.MFn.kAnimCurveTimeToUnitless or \
                    curve_type == om.MFn.kAnimCurveTimeToTime:
                node = om.MFnDependencyNode(obj)
                # add node to dict using absolute name to avoid duplicates -
                # which happens when curves are selected
                curve_dict[node.absoluteName()] = node
        
        it.next()
    
    return curve_dict.values()


def get_curves_from_objects(sl_filter=om.MFn.kDependencyNode):
    obj_list = []
    sl_list = om.MGlobal.getActiveSelectionList()
    it = om.MItSelectionList(sl_list, sl_filter)
    
    # get dependency node from selected object
    while not it.isDone():
        item = it.itemType()
        if item == it.kDagSelectionItem or \
                item == it.kAnimSelectionItem or \
                item == it.kDNselectionItem:
            node = om.MFnDependencyNode(it.getDependNode())
            obj_list.append(node)
        
        it.next()
    
    curve_list = []
    
    channelbox_attr = get_channelbox_attr()
    
    # get curves
    for dep_node in obj_list:
        attr_count = dep_node.attributeCount()
        for index in range(attr_count):
            attr = dep_node.attribute(index)
            plug = dep_node.findPlug(attr, True)
            connections = plug.connectedTo(True, False)
            if connections:
                conn_node = connections[0].node()
                if conn_node.hasFn(om.MFn.kAnimCurve):
                    if channelbox_attr:
                        attr_name = om.MFnAttribute(attr).shortName
                        if attr_name not in channelbox_attr:
                            continue
                    
                    curve_type = conn_node.apiType()
                    if curve_type == om.MFn.kAnimCurveTimeToAngular or \
                            curve_type == om.MFn.kAnimCurveTimeToDistance or \
                            curve_type == om.MFn.kAnimCurveTimeToUnitless or \
                            curve_type == om.MFn.kAnimCurveTimeToTime:
                        curve_node = om.MFnDependencyNode(conn_node)
                        curve_list.append(curve_node)
    
    return curve_list


def get_default_value(mfn_anim_curve):
    plug = mfn_anim_curve.findPlug('output', True)
    conn = plug.connectedTo(False, True)
    if conn:
        conn_plug = conn[0]
        attr_obj = conn_plug.attribute()
    else:
        return None
    
    # attr_obj = plug.attribute()
    api = attr_obj.apiType()
    
    if api == om.MFn.kNumericAttribute:
        typeFn = om.MFnNumericAttribute(attr_obj)
        return float(typeFn.default)
    
    if api in [om.MFn.kDoubleLinearAttribute, om.MFn.kFloatLinearAttribute]:
        typeFn = om.MFnUnitAttribute(attr_obj)
        default = om.MDistance(typeFn.default)
        return default.value
    
    if api in [om.MFn.kDoubleAngleAttribute, om.MFn.kFloatAngleAttribute]:
        typeFn = om.MFnUnitAttribute(attr_obj)
        default = om.MAngle(typeFn.default)
        return default.value
    
    return None


def get_time_slider_range():
    # get time slider range
    aTimeSlider = mel.eval('$tmpVar=$gPlayBackSlider')
    
    time_range = cmds.timeControl(aTimeSlider, q=True, rangeArray=True)
    time_range = (time_range[0], time_range[1] - 1)  # end is one more than selected
    
    return tuple(time_range)


def get_channelbox_attr():
    """
    Get the names of attributes selected in the channel box
    :return: set of strings
    """
    attr = set()
    
    s1 = cmds.channelBox('mainChannelBox', q=True, selectedMainAttributes=True)
    s2 = cmds.channelBox('mainChannelBox', q=True, selectedShapeAttributes=True)
    s3 = cmds.channelBox('mainChannelBox', q=True, selectedHistoryAttributes=True)
    s4 = cmds.channelBox('mainChannelBox', q=True, selectedOutputAttributes=True)
    
    if s1:
        attr |= set(s1)
    if s2:
        attr |= set(s2)
    if s3:
        attr |= set(s3)
    if s4:
        attr |= set(s4)
    
    if len(attr) == 0:
        return None
    
    return attr


def is_graph_editor():
    """
    Determine if keys are selected in the Graph Editor or Dope Sheet.
    :returns: True or False whether keys are selected in the Graph Editor or Dope Sheet
    :rtype: bool
    """
    sl_list = om.MGlobal.getActiveSelectionList()
    it = om.MItSelectionList(sl_list, om.MFn.kAnimCurve)
    return not it.isDone()


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


def get_anim_layer_curves():
    """
    If a given attribute has a animCurve as input, then save the output and use as a value

    1. Find time of prev and next key using cmds.findKeyframe() - this command respects the currently selected
       animation layer. If multiple layers are selected, the top layer takes priority.
    2. Get the value of the attribute at the given times, using cmds.getAttr(attr, time).
    3. Find the animation curve of the selected animation layer.
    4. Assign the value.
    """
    sl_list = om.MGlobal.getActiveSelectionList()
    it = om.MItSelectionList(sl_list)
    
    blend_node_types = (om.MFn.kBlendNodeAdditiveRotation,
                        om.MFn.kBlendNodeAdditiveScale,
                        om.MFn.kBlendNodeBase,
                        om.MFn.kBlendNodeBoolean,
                        om.MFn.kBlendNodeDouble,
                        om.MFn.kBlendNodeDoubleAngle,
                        om.MFn.kBlendNodeDoubleLinear,
                        om.MFn.kBlendNodeEnum,
                        om.MFn.kBlendNodeFloat,
                        om.MFn.kBlendNodeFloatAngle,
                        om.MFn.kBlendNodeFloatLinear,
                        om.MFn.kBlendNodeInt16,
                        om.MFn.kBlendNodeInt32,
                        om.MFn.kBlendNodeTime)
    
    while not it.isDone():
        node = om.MFnDependencyNode(it.getDependNode())
        for index in range(node.attributeCount()):
            attr = node.attribute(index)
            plug = node.findPlug(attr, True)
            connections = plug.connectedTo(True, False)
            if connections:
                conn = connections[0].node()
                if conn.apiType() in blend_node_types:
                    blend_node = om.MFnDependencyNode(conn)
                    blend_plug = blend_node.findPlug('output', True)
        
        it.next()
