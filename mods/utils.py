"""
mods.utils

Functions for getting objects, curves, keys etc.
"""

from collections import namedtuple

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds
import maya.mel as mel

import animlayers

Point = namedtuple('Point', 'x y')

ANIM_CURVE_TYPES = [om.MFn.kAnimCurveTimeToAngular,
                    om.MFn.kAnimCurveTimeToDistance,
                    om.MFn.kAnimCurveTimeToUnitless,
                    om.MFn.kAnimCurveTimeToTime]

OBJECT_SELECTION_ITEMS = [om.MItSelectionList.kDagSelectionItem,
                          om.MItSelectionList.kDNselectionItem]

ANIM_CURVE_SELECTION_ITEMS = [om.MItSelectionList.kDagSelectionItem,
                              om.MItSelectionList.kAnimSelectionItem,
                              om.MItSelectionList.kDNselectionItem]


def maya_useNewAPI():
    pass


def get_selected_objects():
    """
    Gets the active selection filtered by MFn.kDependencyNode.
    
    :return: List of selected objects' dependencyNode
    :rtype: list of om.MFnDependencyNode
    """
    
    nodes = []
    sl_list = om.MGlobal.getActiveSelectionList()
    sl_filter = om.MFn.kDependencyNode
    it = om.MItSelectionList(sl_list, sl_filter)
    
    while not it.isDone():
        item = it.itemType()
        if item in OBJECT_SELECTION_ITEMS:
            nodes.append(om.MFnDependencyNode(it.getDependNode()))
        
        it.next()
    
    return nodes


def get_anim_curves_from_objects(nodes):
    """ Gets the animation curves connected to nodes.
    
    :param nodes: List with MFnDependencyNode
    :type nodes: list of om.MFnDependencyNode
    :return: List of anim curves as dependency nodes
    :rtype: list of om.MFnDependencyNode
    """
    
    curve_list = []
    channelbox_attr = get_channelbox_attributes()
    
    animlayers.cache.reset()  # always reset cache before querying for animation layers!
    has_anim_layers = animlayers.has_anim_layers()
    
    if has_anim_layers and animlayers.all_layers_locked():
        cmds.warning('All animation layers are locked!')
    
    # get curves
    for node in nodes:
        # get all attributes
        attr_count = node.attributeCount()
        for index in range(attr_count):
            attr = node.attribute(index)
            plug = node.findPlug(attr, True)
            
            if plug.isLocked or not plug.isKeyable:
                continue
            
            connections = plug.connectedTo(True, False)
            
            # if the attribute has a connection
            if connections:
                conn_node = connections[0].node()
                
                api = conn_node.apiType()
                if api in ANIM_CURVE_TYPES:
                    # filter out attributes not selected in channelbox
                    if channelbox_attr:
                        attr_name = om.MFnAttribute(attr).shortName
                        if attr_name not in channelbox_attr:
                            continue
                    
                    # add the node if it matches one of the types we want
                    curve_list.append(om.MFnDependencyNode(conn_node))
                
                # find curve in animation layer
                elif has_anim_layers and api in animlayers.BLEND_NODE_TYPES:
                    # filter out attributes not selected in channelbox
                    if channelbox_attr:
                        attr_name = om.MFnAttribute(attr).shortName
                        if attr_name not in channelbox_attr:
                            continue
                    
                    # for testing purposes
                    # print('Attribute: %s' % plug)
                    
                    # benchmark_start = time.clock()
                    best_layer = animlayers.get_best_layer(plug)
                    if not best_layer:
                        continue
                    
                    # for testing purposes
                    # try:
                    #     print('-> Best layer is %s' % (om.MFnDependencyNode(best_layer).name()))
                    # except Exception as e:
                    #     pass
                    
                    curve_node = animlayers.get_anim_curve(plug, best_layer)
                    # animlayers.cache.benchmark += time.clock() - benchmark_start
                    if curve_node:
                        curve_list.append(om.MFnDependencyNode(curve_node))
    
    # sys.stdout.write('# Retrieved %d curves in %.4f sec\n' % (len(curve_list), animlayers.cache.benchmark))
    return curve_list


def get_selected_anim_curves():
    """
    Get directly selected animation curve nodes.

    We only want to modify the following animCurve types: TL, TA, TU, TT
    - UL, UA, UU, UT are used for set driven keys
    
    :return: Dictionary with curve names as key and node as value
    :rtype: list of om.MFnDependencyNode
    """
    
    sl_list = om.MGlobal.getActiveSelectionList()
    it = om.MItSelectionList(sl_list, om.MFn.kAnimCurve)
    
    curve_dict = {}
    
    while not it.isDone():
        if it.itemType() in ANIM_CURVE_SELECTION_ITEMS:
            obj = it.getDependNode()
            if obj.apiType() in ANIM_CURVE_TYPES:
                # add node to dict using absolute name to avoid duplicates - which happens when curves are selected
                node = om.MFnDependencyNode(obj)
                curve_dict[node.absoluteName()] = node
        
        it.next()
    
    return curve_dict.values()


def get_attribute_default_value(plug):
    """ Get the default value for the given plug
    
    :param plug: Plug for the attribute
    :type plug: om.MPlug
    :return: Default value of the attribute found on the plug
    :rtype: float or None
    """
    attr = plug.attribute()
    api = attr.apiType()
    
    if api == om.MFn.kNumericAttribute:
        typeFn = om.MFnNumericAttribute(attr)
        return float(typeFn.default)
    
    if api in [om.MFn.kDoubleLinearAttribute, om.MFn.kFloatLinearAttribute]:
        typeFn = om.MFnUnitAttribute(attr)
        default = om.MDistance(typeFn.default)
        return default.value
    
    if api in [om.MFn.kDoubleAngleAttribute, om.MFn.kFloatAngleAttribute]:
        typeFn = om.MFnUnitAttribute(attr)
        default = om.MAngle(typeFn.default)
        return default.value
    
    return None


def get_anim_curve_default_value(anim_curve):
    """
    Get the default value of the given anim curve
    
    :param anim_curve: Animation curve
    :type anim_curve: oma.MFnAnimCurve
    :return: Default value of attribute curve is connected to.
    :rtype: float or None
    """
    # todo: May be better (and simpler) to look for kDagNode objects, though other objects may be relevant as well, like
    #  polyCube1 or other input nodes. Maybe there is a way to know the end of a nodes effect? Probably not.
    #  Then again, it is only difficult when a curve is selected and there are nodes in-between the anim curve and the
    #  target attribute, so maybe it is a very rare edge case.
    
    if not anim_curve.hasAttribute('output'):
        return None
    
    plug = anim_curve.findPlug('output', True)
    
    if plug:
        destinations = plug.destinations()
        
        if not destinations:
            return None
        
        for dst_plug in destinations:
            # if the first node we hit does not have an output, assume it is the node we want to animate
            if not om.MFnDependencyNode(dst_plug.node()).hasAttribute('output'):
                return get_attribute_default_value(dst_plug)
            
            it = om.MItDependencyGraph(dst_plug, om.MFn.kInvalid,
                                       direction=om.MItDependencyGraph.kDownstream,
                                       traversal=om.MItDependencyGraph.kDepthFirst,
                                       level=om.MItDependencyGraph.kNodeLevel)
            
            output_plug = None
            
            while not it.isDone():
                current_node = it.currentNode()
                
                dep_node = om.MFnDependencyNode(current_node)
                
                if dep_node.hasAttribute('output'):
                    op = dep_node.findPlug('output', True)
                    if op:
                        output_plug = op
                else:
                    it.prune()
                    if output_plug:
                        break
                
                it.next()
            
            if output_plug:
                # resolve compound attribute (like rotation)
                if dst_plug.isChild and output_plug.isCompound:
                    parent = dst_plug.parent()
                    idx = -1
                    for i in range(parent.numChildren()):
                        if parent.child(i) == dst_plug:
                            idx = i
                            break
                    
                    if output_plug.numChildren() > idx:
                        for p in output_plug.child(idx).destinations():
                            if p.isChild:
                                return get_attribute_default_value(p)
                # resolve non-compound attribute
                else:
                    for p in output_plug.destinations():
                        return get_attribute_default_value(p)
    
    return None


def get_channelbox_attributes():
    """
    Get the short names of attributes selected in the channel box.
    
    :return: Set of attributes short name as strings or None
    :rtype: set of string or None
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
    
    visible_panels = cmds.getPanel(vis=True)
    graph_panels = cmds.getPanel(sty='graphEditor')
    dope_panels = cmds.getPanel(sty='dopeSheetPanel')
    
    if graph_panels is not None:
        graph_vis = any(x in graph_panels for x in visible_panels)
    else:
        graph_vis = False
    
    if dope_panels is not None:
        dope_vis = any(x in dope_panels for x in visible_panels)
    else:
        dope_vis = False
    
    return not it.isDone() and (graph_vis or dope_vis)


def get_time_slider_range():
    """
    Get the time range selected on the Time Slider.
    
    :return: time range start and end
    :rtype: tuple of (float, float)
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


def clamp(value, min_value, max_value):
    """
    Clamp a value between min and max.
    
    :param value: Supplied numeric value
    :param min_value: Lowest value
    :param max_value: Highest value
    :return: Value clamped between min and max
    :rtype: float
    """
    if value < min_value:
        return min_value
    elif value > max_value:
        return max_value
    else:
        return value
