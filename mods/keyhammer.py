"""
keyhammer

Creates a key on every attribute for every object, for any key on any attribute
"""

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import mods.utils as utils
import maya.cmds as cmds
import maya.mel as mel
import mods.data as data


def do():
    # get main progress bar start progress
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    cmds.progressBar(gMainProgressBar,
                     e=True,
                     beginProgress=True,
                     isInterruptable=False,
                     status='Adding keyframes...',
                     maxValue=100)
    
    # get selection
    if utils.is_graph_editor():
        curves = utils.get_selected_anim_curves()
    else:
        nodes = utils.get_selected_objects()
        curves = utils.get_anim_curves_from_objects(nodes)
    
    # get curve functions
    curve_fns = []
    for curve_node in curves:
        curve_fns.append(oma.MFnAnimCurve(curve_node.object()))
    
    # get time for keyframes
    times = set()
    for curve_fn in curve_fns:
        for i in range(curve_fn.numKeys):
            times.add(curve_fn.input(i).value)
    
    # determine total number of operations
    cmds.progressBar(gMainProgressBar, e=True, maxValue=len(curve_fns))
    
    # convert to MTime()
    m_times = []
    unit = om.MTime.uiUnit()
    for t in times:
        m_times.append(om.MTime(t, unit))
    
    # add keys
    for curve_fn in curve_fns:
        ts = []
        vs = []
        for mt in m_times:
            if not curve_fn.find(mt):
                ts.append(mt)
                vs.append(curve_fn.evaluate(mt))
        
        for t, v in zip(ts, vs):
            curve_fn.addKey(t, v, change=data.anim_cache)
        
        cmds.progressBar(gMainProgressBar, e=True, step=1)
    
    cmds.progressBar(gMainProgressBar, e=True, endProgress=True)
