"""
Tool

- Allows Tweener to be used as a Maya tool using mouse drag.
- The tool can also be assigned a hotkey using the tweenerTool command.
"""

import os

import maya.cmds as cmds

import globals as g
import options
import tween
import utils

tool = None


def reset():
    """
    Checks for existing tool contexts and initializes a new Tool object.
    """
    if cmds.draggerContext('tweenerToolContext', q=True, exists=True):
        cmds.deleteUI('tweenerToolContext')


def activate():
    """
    Activates the Tweener Tool in Maya.
    """
    global tool
    if tool is None:
        tool = Tool()
    
    cmds.setToolTo('tweenerToolContext')


class Tool:
    """
    Creates a dragger context in Maya with the required functions.
    """
    
    def __init__(self):
        """
        Initializes the instance variables and sets up the dragger context.
        """
        self.press_position = [0, 0, 0]
        self.drag_position = [0, 0, 0]
        
        self.interpolation_mode = options.load_interpolation_mode()
        self.overshoot = options.load_overshoot()
        
        icon_path = g.plugin_path + '/icons/tweener-icon.png'
        
        cmds.draggerContext('tweenerToolContext',
                            name='tweenerTool',
                            pressCommand=self.press,
                            dragCommand=self.drag,
                            releaseCommand=self.release,
                            space='screen',
                            image1=icon_path,
                            undoMode='step')
    
    def press(self):
        """
        Dragger context press event handler.
        
        Gets the initial position and reads in the available options. An
        initial interpolation is also performed.
        """
        self.press_position = cmds.draggerContext('tweenerToolContext',
                                                  q=True,
                                                  anchorPoint=True)
        self.interpolation_mode = options.load_interpolation_mode()
        self.overshoot = options.load_overshoot()
        
        # disable undo on first call, so we don't get 2 undos in queue
        # both press and release add to the same cache, so it should be safe
        cmds.undoInfo(stateWithoutFlush=False)
        cmds.tweener(t=0.0, press=True, type=self.interpolation_mode.idx)
        cmds.undoInfo(stateWithoutFlush=True)
        
        tween.interpolate(blend=0.0, mode=self.interpolation_mode)
        cmds.refresh()
    
    def drag(self):
        """
        Dragger context drag event handler.
        """
        self.blend()
    
    def release(self):
        """
        Dragger context release event handler.
        """
        self.blend()
    
    def blend(self):
        """
        Updates the drag position, gets the blend value and calls for an
        interpolation.
        """
        self.drag_position = cmds.draggerContext('tweenerToolContext',
                                                 q=True,
                                                 dragPoint=True)
        
        blend = self.get_blend()
        tween.interpolate(blend=blend, mode=self.interpolation_mode)
        cmds.refresh()
    
    def get_blend(self):
        """
        Calculates the blend value based on the distance dragged.
        
        :return: Blend value
        :rtype: float
        """
        # calculate distance dragged
        x = self.drag_position[0] - self.press_position[0]
        
        blend = x / 150.0  # 150.0 is just a sensivity
        
        if not self.overshoot:
            blend = utils.clamp(blend, -1.0, 1.0)
        
        return blend


reset()
