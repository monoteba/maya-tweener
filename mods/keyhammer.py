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
    gmainprogressbar = mel.eval('$tmp = $gmainprogressbar')
    cmds.progressbar(gmainprogressbar,
                     e=true,
                     beginprogress=true,
                     isinterruptable=false,
                     status='adding keyframes...',
                     maxvalue=100)
    
    # get selection
    if utils.is_graph_editor():
        curves = utils.get_selected_anim_curves()
    else:
        nodes = utils.get_selected_objects()
        curves = utils.get_anim_curves_from_objects(nodes)
    
    # get curve functions
    curve_fns = []
    for curve_node in curves:
        curve_fns.append(oma.mfnanimcurve(curve_node.object()))
    
    # get time range
    time_range = utils.get_time_slider_range()
    is_range = time_range[0] - time_range[1] != 0
    
    # get time for keyframes
    times = set()
    
    if is_range:
        unit = om.mtime.uiunit()
        min_time = om.mtime(time_range[0], unit)
        max_time = om.mtime(time_range[1], unit)
        for curve_fn in curve_fns:
            start_index = max(0, curve_fn.findclosest(min_time) - 1)  # -1 just to be safe
            end_index = min(curve_fn.numkeys, curve_fn.findclosest(max_time) + 1)  # +1 just to be safe
            for i in range(start_index, end_index):
                times.add(curve_fn.input(i).value)
    else:
        for curve_fn in curve_fns:
            for i in range(curve_fn.numkeys):
                times.add(curve_fn.input(i).value)
    
    # determine total number of operations
    cmds.progressbar(gmainprogressbar, e=true, maxvalue=len(curve_fns))
    
    # convert to mtime()
    m_times = []
    unit = om.mtime.uiunit()
    if is_range:
        for t in times:
            if time_range[0] <= t <= time_range[1]:
                m_times.append(om.mtime(t, unit))
    else:
        for t in times:
            m_times.append(om.mtime(t, unit))
    
    # add keys
    for curve_fn in curve_fns:
        ts = []
        vs = []
        for mt in m_times:
            if curve_fn.find(mt) is none:
                ts.append(mt)
                vs.append(curve_fn.evaluate(mt))
        
        for t, v in zip(ts, vs):
            curve_fn.addkey(t, v, change=data.anim_cache)
        
        cmds.progressbar(gmainprogressbar, e=true, step=1)
    
    cmds.progressbar(gmainprogressbar, e=true, endprogress=true)
