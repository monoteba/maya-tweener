"""
animlayers module
"""

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

# todo: import utils when done testing, use ANIM_CURVE_TYPES from there
# import mods.utils as utils

# todo: change how animation curve is found, now that we can get the best layer for any given attribute
# todo: [DONE] check if all layers are locked
# todo: [DONE] get the "best layer" for a given attribute
# todo: [DONE] when getting scene layers, only return ones that are not locked
# todo: [DONE] get the animation curve for a given layer (blend node -> check layer -> get input B : get input A)


ANIM_CURVE_TYPES = [om.MFn.kAnimCurveTimeToAngular,
                    om.MFn.kAnimCurveTimeToDistance,
                    om.MFn.kAnimCurveTimeToUnitless,
                    om.MFn.kAnimCurveTimeToTime]

BLEND_NODE_TYPES = [om.MFn.kBlendNodeDoubleLinear,
                    om.MFn.kBlendNodeAdditiveRotation,
                    om.MFn.kBlendNodeAdditiveScale,
                    om.MFn.kBlendNodeBoolean,
                    om.MFn.kBlendNodeEnum,
                    om.MFn.kBlendNodeDouble,
                    om.MFn.kBlendNodeDoubleAngle,
                    om.MFn.kBlendNodeFloat,
                    om.MFn.kBlendNodeFloatAngle,
                    om.MFn.kBlendNodeFloatLinear,
                    om.MFn.kBlendNodeInt16,
                    om.MFn.kBlendNodeInt32,
                    om.MFn.kBlendNodeBase]


def maya_useNewAPI():
    pass


# def scene_has_anim_layers():
#     """
#     Determines if the current scene contains anim layers.
#
#     :return: True if scene has anim layers, False if not
#     """
#
#     # must contain at least 2 items, otherwise it is only the root layer
#     if len(cmds.ls(type="animLayer")) > 1:
#         return True
#
#     return False
#
#
# def object_in_anim_layer(obj, anim_layer):
#     """
#     Determine if the given obj is in the anim layer.
#
#     :return: True if obj is in anim layer, False if not
#     :rtype: bool
#     """
#
#     obj_layers = cmds.animLayer([obj], q=True, affectedLayers=True) or []
#     if anim_layer in obj_layers:
#         return True
#
#     return False
#
#
# def get_anim_curve_for_layer(attr):
#     """
#     Find the anim curve for the given attribute on the given layer.
#     """
#
#     # todo: rewrite this to be more performant and return MFnAnimCurve instead of string
#
#     # get best (fit for new keys) anim layer
#     anim_layer = cmds.animLayer(attr, q=True, bestLayer=True)
#
#     if not object_in_anim_layer(attr, anim_layer):
#         return None
#
#     if anim_layer == cmds.animLayer(q=True, root=True):
#         # For the base animation layer, traverse the chain of animBlendNodes all
#         # the way to the end.  The plug will be "inputA" on that last node.
#         blend_node = cmds.listConnections(attr, type='animBlendNodeBase', s=True, d=False)[0]
#         history = cmds.listHistory(blend_node)
#         last_anim_blend_node = cmds.ls(history, type='animBlendNodeBase')[-1]
#         if cmds.objectType(last_anim_blend_node, isa='animBlendNodeAdditiveRotation'):
#             letter_xyz = attr[-1]
#             plug = '{0}.inputA{1}'.format(last_anim_blend_node, letter_xyz.upper())
#         else:
#             plug = '{0}.inputA'.format(last_anim_blend_node)
#     else:
#         # For every layer other than the base animation layer, we can just use
#         # the "animLayer" command.
#         plug = cmds.animLayer(anim_layer, q=True, layeredPlug=attr)
#
#     conns = cmds.listConnections(plug, s=True, d=False)
#     if conns:
#         return conns[0]
#     else:
#         return None


# def find_anim_curve_recursive(animBlendNode=None):
#     if animBlendNode is not None:
#         return
#
#     # get the selected nodes
#     nodes = []
#     sl_list = om.MGlobal.getActiveSelectionList()
#     sl_filter = om.MFn.kDependencyNode
#     it = om.MItSelectionList(sl_list, sl_filter)
#
#     while not it.isDone():
#         item = it.itemType()
#         if item == it.kDagSelectionItem or item == it.kDNselectionItem:
#             nodes.append(om.MFnDependencyNode(it.getDependNode()))
#
#         it.next()
#
#     # get curves
#     curve_list = []
#     for node in nodes:
#         # get all attributes
#         attr_count = node.attributeCount()
#         for index in range(attr_count):
#             attr = node.attribute(index)
#             plug = node.findPlug(attr, True)
#             connections = plug.connectedTo(True, False)
#
#             # if the attribute has a connection
#             if connections:
#                 conn_node = connections[0].node()
#
#                 print('attribute: %s' % om.MFnAttribute(attr).shortName)
#                 print('node type: %s' % om.MFnDependencyNode(conn_node).typeName)
#
#                 # try to get blend node
#                 if conn_node.apiType() in BLEND_NODE_TYPES:
#                     # is the api type one of the kBlendNode types
#                     # get the node connected to the attribute (blend node or anim curve)
#                     print('conn_node name: %s ' % om.MFnDependencyNode(conn_node).name())
#
#                     blend_node = om.MFnDependencyNode(conn_node)  # the anim blend node
#
#                     # anim curves are attached to input B
#                     # additional layers are attached to input A
#                     # except for the last layer, where input A is the anim curve of the base animation
#                     input_a_plug = blend_node.findPlug('inputA', True)
#                     input_b_plug = blend_node.findPlug('inputB', True)
#
#                     input_a_conn = input_a_plug.connectedTo(True, False)
#                     if input_a_conn:
#                         input_a_conn = input_a_conn[0].node()
#
#                     input_b_conn = input_b_plug.connectedTo(True, False)
#                     if input_b_conn:
#                         input_b_conn = input_b_conn[0].node()
#
#                     if input_a_conn.apiType() in ANIM_CURVE_TYPES:
#                         print('input A is an anim curve')
#                     elif input_a_conn.apiType() in BLEND_NODE_TYPES:
#                         print('input A is a blend node')
#
#                     if input_b_conn.apiType() in ANIM_CURVE_TYPES:
#                         print('input B is an anim curve')
#                     elif input_b_conn.apiType() in BLEND_NODE_TYPES:
#                         print('input B is a blend node')
#
#                     # find the AnimLayer node to compare against
#                     weight_plug = blend_node.findPlug('weightA', True)
#                     conns = weight_plug.connectedTo(True, False)
#                     if conns:
#                         conn = conns[0].node()
#                         print('anim layer: %s' % om.MFnDependencyNode(conn).name())  # AnimLayer node
#
#                 print('\n')
#                 # if the connection is of type kAnimCurve
#                 if conn_node.hasFn(om.MFn.kAnimCurve):
#                     # add the node if it matches one of the types we want
#                     curve_type = conn_node.apiType()
#                     # todo: replace ANIM_CURVE_TYPES with utils.ANIM_CURVE_TYPES
#                     if curve_type in ANIM_CURVE_TYPES:
#                         curve_node = om.MFnDependencyNode(conn_node)
#                         curve_list.append(curve_node)

def has_anim_layers():
    """
    Function that checks whether we have any anim layers
    
    :return: True if the scene contains anim layers otherwise False
    :rtype: bool
    """
    it = om.MItDependencyNodes(om.MFn.kAnimLayer)
    count = 0
    while not it.isDone():
        if count > 0:
            return True
        
        count += 1
        it.next()
    
    return False


def all_layers_locked():
    """
    Returns whether all animation layers are locked or not.
    
    :return: True if all animation layers are locked, otherwise False
    :rtype: bool
    """
    for layer in get_scene_layers(filtered=False):
        node_fn = om.MFnDependencyNode(layer)
        plug = node_fn.findPlug('lock', True)
        if plug and not plug.asBool():
            return False
    
    return True


def get_root_layer():
    """
    Get the root animation layer if it exists.

    :return: Root layer or None
    :rtype: om.MObject or None
    """
    
    root_layer = cmds.animLayer(q=True, root=True)
    if not root_layer:
        return None
    
    # get MObject from root layer name
    sel = om.MSelectionList()
    sel.add(root_layer)
    root_layer = sel.getDependNode(0)
    
    return root_layer


def get_scene_layers(filtered=False):
    """
    Gets all nodes of type kAnimLayer and returns them as MObjects.
    This is important as MObjects can be compared for equality unlike function sets.
    
    Returns an empty list if there are no anim layers in the scene.
    
    May in some cases return a list of 1 element, which may be the base animation layer.
    
    :param filtered: Filter the list to only include editable layers (unlocked layers)
    :type filtered: bool
    :return: list of MObject of anim layers in scene
    :rtype: list of om.MObject
    """
    layers = []
    root_layer = get_root_layer()
    
    if not root_layer:
        return layers
    
    root_dep_node = om.MFnDependencyNode(root_layer)
    
    layers.append(root_layer)
    
    # get the child layers from the root, so we get them in order
    plug = root_dep_node.findPlug('childrenLayers', True)
    for i in range(plug.numElements() - 1, -1, -1):  # walk backwards through the children
        conn = plug.elementByPhysicalIndex(i).connectedTo(True, False)
        if conn:
            layers.append(conn[0].node())
    
    if not filtered:
        return layers
    
    editable_layers = []
    for layer in layers:
        node = om.MFnDependencyNode(layer)
        
        lock_plug = node.findPlug('lock', True)
        if lock_plug and lock_plug.asBool():
            continue
        
        editable_layers.append(layer)
    
    return editable_layers


def get_selected_layer(layers=None):
    """
    Get the top-most selected anim layer.
    
    :param layers: Optional list of animation layer objects
    :type layers: list of om.MObject
    :return: Selected anim layer
    :rtype: om.MObject or None
    """
    
    if layers is None:
        layers = get_scene_layers(filtered=False)
    
    if not layers:
        return None
    
    for layer in layers:
        node = om.MFnDependencyNode(layer)
        plug = node.findPlug('selected', True)
        if plug and plug.asBool():
            return layer
    
    return None


def get_anim_curve(plug, layers=None):
    """
    Get the anim curve for the given attribute plug.
    
    The best layer is the top-most selected layer if the attribute is on it and it is not locked.
    Otherwise it is the top-most layer that contains the attribute, which is not locked.
    The root layer, aka BaseAnimation, is the last fallback, unless it is the selected one or is locked.
    
    If all layers are locked, there is nothing for us to do.
    
    :param plug: The attribute plug
    :param layers: Animation layers in scene.
    :type plug: om.MPlug
    :type layers: list of om.MObject
    :return: Anim curve on the "best layer"
    :rtype: oma.MFnAnimCurve or None
    """
    if layers is None:
        layers = get_scene_layers(filtered=True)
    
    if not layers:
        return None
    
    return find_anim_curve(plug, layers)


def find_anim_curve(plug, layers):
    """
    Recursive function that tries to find the anim curve on the "best layer".
    
    :param plug: The attribute plug
    :param layers: Animation layers in scene.
    :type plug: om.MPlug
    :type layers: list of om.MObject
    :return: Anim curve on the "best layer"
    :rtype: oma.MFnAnimCurve or None
    """
    
    connections = plug.connectedTo(True, False)
    
    if not connections:
        cmds.warning('Did not find any connections')
        return None
    
    conn_node = connections[0].node()
    
    # if the connected node is of type anim curve, return it
    if conn_node.apiType() in ANIM_CURVE_TYPES:
        print('Found curve! But not in layers')
        return oma.MFnAnimCurve(conn_node)
    
    # if the connected node is a blend node, check if
    if conn_node.apiType() in BLEND_NODE_TYPES:
        dep_node = om.MFnDependencyNode(conn_node)
        
        # get the possible layer connected to weight A, both weight A and B should be connected to the anim layer
        layer_node = None
        weight_plug = dep_node.findPlug('weightA', True)
        if weight_plug:
            weight_conns = weight_plug.connectedTo(True, False)
            if weight_conns:
                weight_node = weight_conns[0].node()
                if weight_node.hasFn(om.MFn.kAnimLayer):
                    layer_node = weight_node
        
        # is the current layer in the list of possible layers?
        if layer_node:
            if layer_node in layers:
                input_b_plug = dep_node.findPlug('inputB', True)
                if input_b_plug:
                    b_conns = input_b_plug.connectedTo(True, False)
                    if b_conns:
                        anim_curve = b_conns[0].node()
                        if anim_curve.hasFn(om.MFn.kAnimCurve):
                            print('Found anim curve %s on layer %s' % (oma.MFnAnimCurve(anim_curve).name(),
                                                                       om.MFnDependencyNode(layer_node).name()))
                            return oma.MFnAnimCurve(anim_curve)
                        else:
                            cmds.warning('Unexpected: Anim curve was not attached to inputB (1)')
                            return None
                    else:
                        cmds.warning('Animation curve was not found on %s' % om.MFnDependencyNode(layer_node).name())
                        return None
        else:
            cmds.warning('Layer was not found on weightA')
        
        input_a_plug = dep_node.findPlug('inputA', True)
        if input_a_plug:
            return find_anim_curve(input_a_plug, layers)
        
        cmds.warning('Nothing was attached to inputA')
        return None


def get_best_layer(plug):
    """
    Traverse the attribute plug hiearchy in search of anim layers and find the best candidate.
    
    :param plug: MPlug for where to start the search
    :type plug: om.MPlug
    :return: Best layer or None
    :rtype: om.MObject or None
    """
    root_layer = get_root_layer()
    
    if not root_layer:
        return None
    
    # if root layer is selected, use that
    root_fn = om.MFnDependencyNode(root_layer)
    lock_plug = root_fn.findPlug('lock', True)
    if lock_plug and not lock_plug.asBool():
        sel_plug = root_fn.findPlug('selected', True)
        if sel_plug and sel_plug.asBool():
            return root_layer
    
    sel_layer = get_selected_layer()
    node_fn = om.MFnDependencyNode(sel_layer)
    lock_plug = node_fn.findPlug('lock', True)
    sel_layer_locked = lock_plug and lock_plug.asBool()
    print('selected layer locked: %s' % sel_layer_locked)
    
    # iterate over the hiearchy to find the first
    it = om.MItDependencyGraph(plug, om.MFn.kAnimLayer,
                               direction=om.MItDependencyGraph.kDownstream,
                               traversal=om.MItDependencyGraph.kBreadthFirst)
    
    last_layer = None
    
    while not it.isDone():
        # store the node, and move iterator immediately
        layer = it.currentNode()
        it.next()
        
        # skip if locked
        node_fn = om.MFnDependencyNode(layer)
        lock_plug = node_fn.findPlug('lock', True)
        if lock_plug and lock_plug.asBool():
            continue
        
        # return layer if selected
        if layer == sel_layer:
            return layer
        
        # only return the layer at the end, because we traverse down stream
        last_layer = layer
    
    return last_layer


print('\n\n\n\n==== NEW RUN ====\n')

# a = get_scene_layers()
# l = get_selected_layer(a)
# # print(om.MFnDependencyNode(l).name())

sl = om.MSelectionList()
sl.add('pCube1')
mobj = sl.getDependNode(0)
mobj_fn = om.MFnDependencyNode(mobj)
attr = mobj_fn.findPlug('tx', True)
get_anim_curve(attr)

best_layer = get_best_layer(attr)
if best_layer:
    print('best layer: %s' % om.MFnDependencyNode(best_layer).name())
else:
    print('no layer available!')

print('\n==== END RUN ====\n')
