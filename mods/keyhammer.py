"""
keyhammer

Creates a key on every attribute for every object, for all key
"""

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import mods.utils as utils
import maya.cmds as cmds
import maya.mel as mel

import animdata as animdata


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
    
    # get time range
    time_range = utils.get_time_slider_range()
    is_range = time_range[0] - time_range[1] != 0
    
    # get time for keyframes
    times = set()
    
    if is_range:
        unit = om.MTime.uiUnit()
        min_time = om.MTime(time_range[0], unit)
        max_time = om.MTime(time_range[1], unit)
        for curve_fn in curve_fns:
            start_index = max(0, curve_fn.findClosest(min_time) - 1)  # -1 just to be safe
            end_index = min(curve_fn.numKeys, curve_fn.findClosest(max_time) + 1)  # +1 just to be safe
            for i in range(start_index, end_index):
                times.add(curve_fn.input(i).value)
    else:
        for curve_fn in curve_fns:
            for i in range(curve_fn.numKeys):
                times.add(curve_fn.input(i).value)
    
    # determine total number of operations
    cmds.progressBar(gMainProgressBar, e=True, maxValue=len(curve_fns))
    
    # convert to MTime()
    m_times = []
    unit = om.MTime.uiUnit()
    if is_range:
        for t in times:
            if time_range[0] <= t <= time_range[1]:
                m_times.append(om.MTime(t, unit))
    else:
        for t in times:
            m_times.append(om.MTime(t, unit))
    
    # add keys
    for curve_fn in curve_fns:
        ts = []
        vs = []
        for mt in m_times:
            if curve_fn.find(mt) is None:
                ts.append(mt)
                vs.append(curve_fn.evaluate(mt))
        
        for t, v in zip(ts, vs):
            curve_fn.addKey(t, v, change=animdata.anim_cache)
        
        cmds.progressBar(gMainProgressBar, e=True, step=1)
    
    cmds.progressBar(gMainProgressBar, e=True, endProgress=True)
