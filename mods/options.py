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


def save_live_preview(value=True):
    """
    Saves the live preview state using Maya optionVars.
    :param value: Current state of the live preview toggle
    :return:
    """
    cmds.optionVar(iv=('tweener_live_preview', int(value)))


def load_live_preview():
    """
    Loads the live preview state from Maya optionVars.
    :return:  The loaded live preview state
    :rtype: bool
    """
    if cmds.optionVar(exists='tweener_live_preview'):
        return bool(cmds.optionVar(q='tweener_live_preview'))
    
    return True


def save_toolbar(visible=True):
    """
    Saves the visibility of window buttons
    :param visible: Whether the toolbar is visible
    """
    cmds.optionVar(iv=('tweener_toolbar', int(visible)))


def load_toolbar():
    """
    Loads the visibility of the toolbar
    :rtype: bool
    """
    if cmds.optionVar(exists='tweener_toolbar'):
        return bool(cmds.optionVar(q='tweener_toolbar'))
    
    return True  # default


def save_presets(visible=True):
    """
    Saves the visibility of the preset buttons
    :param visible: Whether the preset buttons are visible
    """
    cmds.optionVar(iv=('tweener_presets', int(visible)))


def load_presets():
    """
    Loads the visibility of the preset buttons
    :rtype: bool
    """
    if cmds.optionVar(exists='tweener_presets'):
        return bool(cmds.optionVar(q='tweener_presets'))
    
    return True  # default


def save_tick_draw_special(visible=True):
    """
    Saves the visibility of the preset buttons
    :param visible: Whether the preset buttons are visible
    """
    cmds.optionVar(iv=('tweener_tick_draw_special', int(visible)))


def load_tick_draw_special():
    """
    Loads the visibility of the preset buttons
    :rtype: bool
    """
    if cmds.optionVar(exists='tweener_tick_draw_special'):
        return bool(cmds.optionVar(q='tweener_tick_draw_special'))
    
    return False  # default
