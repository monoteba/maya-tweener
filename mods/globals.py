"""
globals
"""
import os
import maya.cmds as cmds

plugin_name = 'tweener.py'
plugin_path = ''
plugin_version = '1.0.6'


def refresh_plug_in_path():
    global plugin_name
    global plugin_path
    
    try:
        plugin_path = os.path.dirname(
            cmds.pluginInfo(plugin_name, q=True, path=True)) + '/'
    except Exception as e:
        cmds.warning(str(e))
