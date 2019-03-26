"""
utils

Functions for getting objects, curves, keys etc.
"""

import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel
from collections import namedtuple

Point = namedtuple('Point', 'x y')


def maya_useNewAPI():
    pass


def get_selected_objects():
    """
    Gets the active selection filtered by MFn.kDependencyNode.
    :return: List of selected objects' dependencyNode
    :rtype: list
    """
    nodes = []
    sl_list = om.MGlobal.getActiveSelectionList()
    sl_filter = om.MFn.kDependencyNode
    it = om.MItSelectionList(sl_list, sl_filter)
    
    while not it.isDone():
        item = it.itemType()
        if item == it.kDagSelectionItem or item == it.kDNselectionItem:
            nodes.append(om.MFnDependencyNode(it.getDependNode()))
        
        it.next()
    
    return nodes


def get_anim_curves_from_objects(nodes=[]):
    """
    Gets the animation curves connected to nodes.
    :param nodes: List with MFnDependencyNode
    :type nodes: list
    :return: List of nodes' animCurves as dependencyNodes
    :rtype: list
    """
    
    curve_list = []
    channelbox_attr = get_channelbox_attributes()
    
    # get curves
    for node in nodes:
        attr_count = node.attributeCount()
        for index in range(attr_count):
            attr = node.attribute(index)
            plug = node.findPlug(attr, True)
            connections = plug.connectedTo(True, False)
            
            if connections:
                conn_node = connections[0].node()
                
                if conn_node.hasFn(om.MFn.kAnimCurve):
                    # filter out attributes not selected in channelbox
                    if channelbox_attr:
                        attr_name = om.MFnAttribute(attr).shortName
                        if attr_name not in channelbox_attr:
                            continue
                    
                    # add the node if it matches one of the types we want
                    curve_type = conn_node.apiType()
                    if curve_type == om.MFn.kAnimCurveTimeToAngular or \
                            curve_type == om.MFn.kAnimCurveTimeToDistance or \
                            curve_type == om.MFn.kAnimCurveTimeToUnitless or \
                            curve_type == om.MFn.kAnimCurveTimeToTime:
                        curve_node = om.MFnDependencyNode(conn_node)
                        curve_list.append(curve_node)
    
    return curve_list


def get_selected_anim_curves():
    """
    Get directly selected animation curve nodes.

    We only want to modify the following animCurve types: TL, TA, TU, TT
    - UL, UA, UU, UT are used for set driven keys
    :return: dictionary with curve names as key and node as value
    :rtype: dict
    """
    
    sl_list = om.MGlobal.getActiveSelectionList()
    it = om.MItSelectionList(sl_list, om.MFn.kAnimCurve)
    
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


def get_anim_layer_curves():
    # todo: not yet implemented
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


def get_anim_curve_default_value(anim_curve):
    """
    Get the default value of
    :param anim_curve:
    :type anim_curve: om.MFn.
    :return: Default value of attribute curve is connected to.
    """
    # todo: does not work with animation layers
    plug = anim_curve.findPlug('output', True)
    conn = plug.connectedTo(False, True)
    
    if conn:
        conn_plug = conn[0]
        attr_obj = conn_plug.attribute()
    else:
        return None
    
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


def get_channelbox_attributes():
    """
    Get the short names of attributes selected in the channel box.
    :return: Set of attributes short name as strings or None
    :rtype: set, None
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


def get_time_slider_range():
    """
    Get the time range selected on the Time Slider.
    :return: time range start and end
    :rtype: tuple
    """
    # get time slider range
    aTimeSlider = mel.eval('$tmpVar=$gPlayBackSlider')
    
    time_range = cmds.timeControl(aTimeSlider, q=True, rangeArray=True)
    time_range = (time_range[0], time_range[1] - 1)  # end is one more than selected
    
    return tuple(time_range)


def get_curve_tangents_bezier_points(curve_fn, start_index, end_index):
    """
    Determines the 4 points that form the bezier curve between start_index and end_index for a given animation curve.
    :param curve_fn: MFnAnimCurve
    :param start_index: Key index for the animation curve function
    :param end_index: Key index for the animation curve function
    :return: 4 points that form a cubic bezier curve with x,y coordinates
    :rtype: tuple
    """
    
    p1 = Point(curve_fn.input(start_index).asUnits(om.MTime.kSeconds), curve_fn.value(start_index))
    p4 = Point(curve_fn.input(end_index).asUnits(om.MTime.kSeconds), curve_fn.value(end_index))
    
    p2 = curve_fn.getTangentXY(start_index, False)  # inTangent = False
    p2 = Point(p1.x + p2[0] / 3, p1.y + p2[1] / 3)
    
    p3 = curve_fn.getTangentXY(end_index, True)  # inTangent = True
    p3 = Point(p4.x - p3[0] / 3, p4.y - p3[1] / 3)
    
    return p1, p2, p3, p4
