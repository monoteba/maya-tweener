"""
keyhammer
"""
import sys

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds
import maya.mel as mel

if sys.version_info >= (3, 0):
    import mods.animdata as animdata
    import mods.utils as utils
else:
    import animdata as animdata
    import utils as utils
    

def do():
    """
    Creates a key on all attributes at any time-value, where a key exists in the curves list
    :return True on complete, False if cancelled
    :rtype bool
    """
    # get selection
    if utils.is_graph_editor_or_dope_sheet():
        curves = utils.get_selected_anim_curves()
    else:
        nodes = utils.get_selected_objects()
        curves, plugs = utils.get_anim_curves_from_objects(nodes)
    
    # get curve functions
    curve_fns = []
    for curve_node in curves:
        curve_fns.append(oma.MFnAnimCurve(curve_node.object()))
    
    if len(curve_fns) == 0:
        sys.stdout.write('# No anim curves to set keys on\n')
        return True
    
    # get time range
    time_range = utils.get_time_slider_range()
    is_range = time_range[0] - time_range[1] != 0
    
    # get time for keyframes
    times = set()
    selected_keys = cmds.keyframe(q=True, selected=True, timeChange=True) if is_range is False else None
    
    if is_range:
        unit = om.MTime.uiUnit()
        min_time = om.MTime(time_range[0], unit)
        max_time = om.MTime(time_range[1], unit)
        for curve_fn in curve_fns:
            start_index = max(0, curve_fn.findClosest(min_time))  # -1 just to be safe, is checked later
            end_index = min(curve_fn.numKeys, curve_fn.findClosest(max_time))  # +1 just to be safe
            for i in range(start_index, end_index):
                times.add(curve_fn.input(i).value)
    elif selected_keys is not None:
        times = set(selected_keys)
    else:
        for curve_fn in curve_fns:
            for i in range(curve_fn.numKeys):
                times.add(curve_fn.input(i).value)
    
    # get main progress bar start progress
    gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
    cmds.progressBar(gMainProgressBar,
                     e=True,
                     beginProgress=True,
                     isInterruptable=True,
                     status='Adding keyframes...',
                     maxValue=len(curve_fns))
    
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
    key_count = 0
    cancelled = False
    for curve_fn in curve_fns:
        ts = []
        vs = []
        for mt in m_times:
            if curve_fn.find(mt) is None:
                ts.append(mt)
                vs.append(curve_fn.evaluate(mt))
        
        for t, v in zip(ts, vs):
            curve_fn.addKey(t, v, change=animdata.anim_cache)
            key_count += 1
        
        cmds.progressBar(gMainProgressBar, e=True, step=1)
        
        if cmds.progressBar(gMainProgressBar, q=True, isCancelled=True):
            cancelled = True
            break
    
    cmds.progressBar(gMainProgressBar, e=True, endProgress=True)
    
    if cancelled:
        sys.stdout.write('# Keyhammer cancelled...\n')
        return False
    else:
        sys.stdout.write('# Added %d key%s\n' % (key_count, '' if key_count == 1 else 's'))
        
    return True
