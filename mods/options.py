"""
options module

Takes care of saving and loading preferences in Maya.
"""

import maya.cmds as cmds


class BlendingMode:
    """
    Static class, which contains the different blending modes.
    """
    
    def __init__(self):
        pass
    
    class Mode:
        def __init__(self, name, idx, tooltip):
            self.name = name
            self.idx = idx
            self.tooltip = tooltip
    
    between = Mode('Between', 0, 'Mode: Between')
    towards = Mode('Towards', 1, 'Mode: Towards')
    average = Mode('Average', 2, 'Mode: Average')
    curve = Mode('Curve', 3, 'Mode: Curve Tangent')
    default = Mode('Default', 4, 'Mode: Default')
    
    # convenience list
    modes = [between, towards, average, curve, default]
    
    @staticmethod
    def get_mode_from_id(idx=0):
        for m in BlendingMode.modes:
            if m.idx == idx:
                return m
        
        return BlendingMode.between


def save_interpolation_mode(idx=0):
    """
    Saves the blending mode using Maya option variables.
    
    :param idx: The blending mode idx
    :type idx: int
    """
    cmds.optionVar(iv=('tweener_interp_type_id', idx))


def load_interpolation_mode():
    """
    Loads the blending mode using Maya option variables.
    
    :return: The loaded blending mode.
    :rtype: BlendingMode.Mode
    """
    if cmds.optionVar(exists='tweener_interp_type_id'):
        idx = int(cmds.optionVar(q='tweener_interp_type_id'))
    else:
        idx = 0
    
    for m in BlendingMode.modes:
        if idx == m.idx:
            return m
    
    return BlendingMode.between


def save_overshoot(value=False):
    """
    Saves the overshoot state using Maya optionVars.
    
    :param value: Current state of the overshoot toggle
    """
    cmds.optionVar(iv=('tweener_overshoot', int(value)))


def load_overshoot():
    """
    Loads the overshoot state from Maya optionVars.
    :return: The loaded toggle state
    :rtype: bool
    """
    if cmds.optionVar(exists='tweener_overshoot'):
        return bool(cmds.optionVar(q='tweener_overshoot'))
    
    return False
