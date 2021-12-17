"""
mods.animlayers
"""
import sys

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

if sys.version_info >= (3, 0):
    import mods.utils as utils
else:
    import utils as utils

def maya_useNewAPI():
    pass


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

BLEND_NODE_ROTATION_TYPES = [om.MFn.kBlendNodeAdditiveRotation]


class AnimationLayer(object):
    def __init__(self, layer=None, selected=False, locked=False):
        """
        Representation of animation layer.
        
        :param layer: Animation layer
        :param selected: Is the layer selected?
        :param locked: Is the layer locked?
        :type layer: om.MObject or None
        :type selected: bool
        :type locked: bool
        """
        self.layer = layer
        self.selected = selected
        self.locked = locked
    
    def reset_selected(self):
        """
        Resets the selected state to the current scene state.
        """
        if self.layer is None:
            self.selected = False
            return
        
        node = om.MFnDependencyNode(self.layer)
        plug = node.findPlug('selected', True)
        self.selected = plug and plug.asBool()
    
    def reset_locked(self):
        """
        Resets the locked state to the current scene state.
        """
        if self.layer is None:
            self.locked = False
            return
        
        node = om.MFnDependencyNode(self.layer)
        plug = node.findPlug('lock', True)
        self.locked = plug and plug.asBool()


class Cache(object):
    """
    Static class that stores the current scene layers, the selected layers and the locked layers.
    """
    def __init__(self):
        self.__scene_layers = None
        self.__selected_layers = None
        self.__locked_layers = None
        self.__unlocked_layers = None
        self.__root = None
        
        self.reset()
    
    def reset(self):
        """
        Resets the cache to the current scene state.
        """
        self.__scene_layers = get_scene_layers(locked=True)
        self.__selected_layers = get_selected_layers()
        self.__locked_layers = get_locked_layers(layers=self.__scene_layers)
        self.__unlocked_layers = get_scene_layers(locked=False)
        
        self.__root = AnimationLayer(layer=get_root_layer())
        self.__root.reset_selected()
        self.__root.reset_locked()
    
    @property
    def root(self):
        """
        Get the root layer as an AnimationLayer.
        
        :return: AnimationLayer object
        :rtype: AnimationLayer
        """
        return self.__root
    
    @property
    def scene_layers(self):
        """
        Get the scene animation layers stored in the cache.
        
        :return: List of animation layers
        :rtype: list of om.MObject or None
        """
        return self.__scene_layers
    
    @property
    def selected_layers(self):
        """
        Get the selected animation layers stored in the cache. Excludes locked layers.
        
        :return: List of animation layers
        :rtype: list of om.MObject or None
        """
        return self.__selected_layers
    
    @property
    def locked_layers(self):
        """
        Get the locked animation layers stored in the cache.
        
        :return: List of animation layers
        :rtype: list of om.MObject or None
        """
        return self.__locked_layers
    
    @property
    def unlocked_layers(self):
        """
        Get the unlocked animation layers stored in the cache.

        :return: List of animation layers
        :rtype: list of om.MObject or None
        """
        return self.__unlocked_layers


def has_anim_layers():
    """
    Checks whether the scene has any animation layers.
    Also returns False if only the root layer exists.
    
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
    
    for layer in cache.scene_layers:
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


def get_scene_layers(locked=False):
    """
    Gets all nodes of type kAnimLayer and returns them as MObjects.
    This is important as MObjects can be compared for equality unlike function sets.
    
    Returns an empty list if there are no anim layers in the scene.
    
    May in some cases return a list of 1 element, which may be the base animation layer.
    
    :param locked: Include locked layers
    :type locked: bool
    :return: list of MObject of anim layers in scene
    :rtype: list of om.MObject or None
    """
    root_layer = get_root_layer()
    
    if not root_layer:
        return None
    
    root_dep_node = om.MFnDependencyNode(root_layer)
    
    layers = [root_layer]
    
    # get the child layers from the root, so we get them in order
    plug = root_dep_node.findPlug('childrenLayers', True)
    for i in range(plug.numElements() - 1, -1, -1):  # walk backwards through the children
        conn = plug.elementByPhysicalIndex(i).connectedTo(True, False)
        if conn:
            layers.append(conn[0].node())
    
    # include locked layers?
    if locked:
        return layers
    
    unlocked_layers = []
    for layer in layers:
        node = om.MFnDependencyNode(layer)
        
        lock_plug = node.findPlug('lock', True)
        if lock_plug and lock_plug.asBool():
            continue
        
        unlocked_layers.append(layer)
    
    return unlocked_layers


def get_selected_layers(layers=None):
    """
    Get all selected layers ordered from top to bottom.
    Excludes locked layers unless a list of layers is passed.
    
    :param layers: Optional list of animation layer objects
    :type layers: list of om.MObject or None
    :return: Selected anim layer
    :rtype: list of om.MObject
    """
    
    if layers is None:
        layers = get_scene_layers(locked=False)
    
    if not layers:
        return None
    
    selected_layers = []
    
    for layer in layers:
        node = om.MFnDependencyNode(layer)
        plug = node.findPlug('selected', True)
        if plug and plug.asBool():
            selected_layers.append(layer)
    
    return selected_layers


def get_locked_layers(layers=None):
    """
    Get the locked animation layers from top to bottom.

    :param layers: Optional list of animation layer objects
    :type layers: list of om.MObject or None
    :return: Locked animation layers
    :rtype: list of om.MObject
    """
    
    if layers is None:
        layers = get_scene_layers(locked=True)
    
    if not layers:
        return None
    
    locked_layers = []
    
    for layer in layers:
        node = om.MFnDependencyNode(layer)
        plug = node.findPlug('lock', True)
        if plug and plug.asBool():
            locked_layers.append(layer)
    
    return locked_layers


def get_anim_curve(plug, layer):
    """
    Get the anim curve for the given attribute plug.
    
    The best layer is the top-most selected layer if the attribute is on it and it is not locked.
    Otherwise it is the top-most layer that contains the attribute, which is not locked.
    The root layer, aka BaseAnimation, is the last fallback, unless it is the selected one or is locked.
    
    If all layers are locked, there is nothing for us to do.
    
    :param plug: The attribute plug
    :param layer: The animation layer to retrieve the curve from
    :type plug: om.MPlug
    :type layer: om.MObject
    :return: Animation curve on the best layer
    :rtype: oma.MFnAnimCurve or None
    """
    # special case for root layer
    if cache.root.layer and layer == cache.root.layer:
        is_root = True
    else:
        is_root = False
    
    scene_layers = cache.scene_layers
    
    it = om.MItDependencyGraph(plug, om.MFn.kInvalid,
                               direction=om.MItDependencyGraph.kUpstream,
                               traversal=om.MItDependencyGraph.kBreadthFirst,
                               level=om.MItDependencyGraph.kNodeLevel)
    
    target_blend = None
    
    while not it.isDone():
        current_node = it.currentNode()
        
        if current_node in scene_layers:
            it.prune()
        
        it.next()
        if current_node.apiType() in BLEND_NODE_TYPES:
            # iterate to the last node if is root
            if is_root:
                target_blend = current_node
                continue
            # otherwise check if the layer connected to weightA is the desired layer
            node_fn = om.MFnDependencyNode(current_node)
            layer_plug = node_fn.findPlug('wa', True)  # weightA
            if layer_plug:
                if layer == layer_plug.source().node():
                    target_blend = current_node
                    break
    
    if target_blend:
        node_fn = om.MFnDependencyNode(target_blend)
        
        if is_root:
            input_plug = node_fn.findPlug('ia', True)  # inputA
        else:
            input_plug = node_fn.findPlug('ib', True)  # inputB
        
        # is the blend node a rotation type?
        if target_blend.apiType() in BLEND_NODE_ROTATION_TYPES:
            idx = 0
            # find which index we come from
            if plug.isChild:
                parent = plug.parent()
                for i in range(parent.numChildren()):
                    if parent.child(i) == plug:
                        idx = i
            
            # try to get the same index from the input
            if input_plug.isCompound and idx < input_plug.numChildren():
                input_plug = input_plug.child(idx)
                curve_node = input_plug.source().node()
                if curve_node and curve_node.apiType() in utils.ANIM_CURVE_TYPES:
                    return curve_node
        
        elif input_plug:
            curve_node = input_plug.source().node()
            if curve_node and curve_node.apiType() in utils.ANIM_CURVE_TYPES:
                return curve_node
    
    return None


def get_best_layer(plug):
    """
    Traverse the attribute plug hiearchy in search of animation layers and find the best candidate.
    
    :param plug: MPlug for where to start the search
    :type plug: om.MPlug
    :return: Best layer or None
    :rtype: om.MObject or None
    """
    root = cache.root
    sel_layers = cache.selected_layers
    scene_layers = cache.scene_layers
    
    # if root layer is selected and not locked, use that
    if root.locked:
        root.layer = None
    elif root.selected and not len(sel_layers) > 1:
        return root.layer
    
    it = om.MItDependencyGraph(plug, om.MFn.kAnimLayer,
                               direction=om.MItDependencyGraph.kDownstream,
                               traversal=om.MItDependencyGraph.kBreadthFirst,
                               level=om.MItDependencyGraph.kNodeLevel)
    # it.pruningOnFilter = True
    best_layer = None
    
    if sel_layers:
        while not it.isDone():
            # store the node, and move iterator immediately
            layer = it.currentNode()
            
            if layer in scene_layers:
                it.prune()
                if layer in sel_layers:
                    best_layer = layer
            
            it.next()
    
    # found a selected layers which was not locked
    if best_layer:
        return best_layer
    
    it.reset()
    unlocked_layers = cache.unlocked_layers
    
    while not it.isDone():
        # store the node, and move iterator immediately
        layer = it.currentNode()
        
        # only add if unlocked
        if layer in scene_layers:
            it.prune()
            if layer in unlocked_layers:
                best_layer = layer
        
        it.next()
    
    # default value is the root layer, which may be None if it is locked
    if not best_layer:
        best_layer = root.layer
    
    # only return at the end of the iteration, because we traverse downstream
    return best_layer


cache = Cache()
