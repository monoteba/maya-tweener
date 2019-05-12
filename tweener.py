"""
Tweener is a tool similar to TweenMachine or aTools/animBot. It allows you to quickly create inbetweens in Maya by
favouring adjacent keys and can speed-up the animation process.

Please refer to the plug-ins GitHub page for more information at https://github.com/mortenblaa/maya-tweener
"""

# todo: support for animation layers
# todo: should we traverse down to inputs? -> yes in case of anim layers
# todo: hammer keys (set key on every key)

# todo: record/apply change --> maybe separate tool, incl. mirroring (name: poser)
# todo: add/remove inbetween buttons --> maybe separate tool (name: nudger)

# standard modules
import sys
import os

# maya modules
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.cmds as cmds

# tweener modules
import mods.globals as g
import mods.ui as ui
import mods.tween as tween
import mods.data as data
import mods.keyhammer as keyhammer


def maya_useNewAPI():
    pass


def reload_mods():
    """
    For development purposes only
    """
    import inspect
    
    path = (os.path.dirname(__file__)).lower()
    to_delete = []
    
    for key, module in sys.modules.iteritems():
        try:
            if module is None:
                continue
            
            module_path = inspect.getfile(module).lower()
            
            if module_path == __file__.lower():
                continue
            
            if module_path.startswith(path):
                to_delete.append(key)
        
        except TypeError as te:
            pass  # TypeError is from inspect.getfile() if it's builtin
        except Exception as e:
            sys.stdout.write('%s\n' % e)
    
    for module_key in to_delete:
        del (sys.modules[module_key])


"""
Plugin registration
"""


def initializePlugin(plugin):
    plugin_fn = om.MFnPlugin(plugin, "Morten Andersen", "1.0", "Any")
    
    # register TweenerCmd
    try:
        plugin_fn.registerCommand(TweenerCmd.cmd_name, TweenerCmd.cmd_creator, TweenerCmd.syntax_creator)
    except:
        sys.stderr.write("Failed to register command: %s\n" % TweenerCmd.cmd_name)
        raise
    else:
        sys.stdout.write('# Successfully registered command %s\n' % TweenerCmd.cmd_name)
    
    # register KeyHammerCmd
    try:
        plugin_fn.registerCommand(KeyHammerCmd.cmd_name, KeyHammerCmd.cmd_creator)
    except:
        sys.stderr.write("Failed to register command: %s\n" % KeyHammerCmd.cmd_name)
        raise
    else:
        sys.stdout.write('# Successfully registered command %s\n' % KeyHammerCmd.cmd_name)
    
    g.plugin_path = os.path.dirname(cmds.pluginInfo(plugin_fn.name(), q=True, path=True)) + '/'


def uninitializePlugin(plugin):
    plugin_fn = om.MFnPlugin(plugin)
    
    # deregister TweenerCmd
    try:
        plugin_fn.deregisterCommand(TweenerCmd.cmd_name)
    except:
        sys.stderr.write("Failed to deregister command: %s\n" % TweenerCmd.cmd_name)
        raise
    else:
        sys.stdout.write('# Successfully unregistered command %s\n' % TweenerCmd.cmd_name)
    
    # deregister KeyHammerCmd
    try:
        plugin_fn.deregisterCommand(KeyHammerCmd.cmd_name)
    except:
        sys.stderr.write("Failed to deregister command: %s\n" % KeyHammerCmd.cmd_name)
        raise
    else:
        sys.stdout.write('# Successfully unregistered command %s\n' % KeyHammerCmd.cmd_name)


"""
Maya Command (MPxCommand)
"""


class TweenerCmd(om.MPxCommand):
    cmd_name = 'tweener'
    anim_cache = None
    
    # command flags
    interpolant_flag = '-t'
    interpolant_flag_long = '-interpolant'
    press_flag = '-p'
    press_flag_long = '-press'
    type_flag = '-tp'
    type_flag_long = '-type'
    
    # default command argument values
    blend_arg = 0
    press_arg = False
    type_arg = None
    
    def __init__(self):
        om.MPxCommand.__init__(self)
    
    @staticmethod
    def cmd_creator():
        return TweenerCmd()
    
    @classmethod
    def syntax_creator(cls):
        syntax = om.MSyntax()
        
        # add flags
        syntax.addFlag(cls.interpolant_flag, cls.interpolant_flag_long, om.MSyntax.kDouble)
        syntax.addFlag(cls.press_flag, cls.press_flag_long, om.MSyntax.kBoolean)
        syntax.addFlag(cls.type_flag, cls.type_flag_long, om.MSyntax.kString)
        return syntax
    
    def pass_args(self, args):
        arg_data = om.MArgParser(self.syntax(), args)
        
        if arg_data.isFlagSet(self.interpolant_flag):
            self.blend_arg = arg_data.flagArgumentDouble(self.interpolant_flag, 0)
        
        if arg_data.isFlagSet(self.press_flag):
            self.press_arg = arg_data.flagArgumentDouble(self.press_flag, 0)
        
        if arg_data.isFlagSet(self.type_flag):
            self.type_arg = arg_data.flagArgumentString(self.type_flag, 0)
        
        return arg_data.numberOfFlagsUsed
    
    def doIt(self, args):
        # pass arguments, and if 0 flags are given, show the window
        if self.pass_args(args) == 0:
            ui.show()
            return
        
        # the animation cache must be stored in the command instance itself so
        # we pass a reference to the cache to the Lt class, so we can manipulate
        # the currently active cache
        if self.press_arg:
            # if press, then create a new cache
            self.anim_cache = oma.MAnimCurveChange()
            data.anim_cache = self.anim_cache
            data.prepare(t_type=self.type_arg)
        else:
            # else use the existing stored at module level
            self.anim_cache = data.anim_cache
            tween.interpolate(t=self.blend_arg, t_type=self.type_arg)
    
    def redoIt(self):
        self.anim_cache.redoIt()
    
    def undoIt(self):
        self.anim_cache.undoIt()
    
    def isUndoable(*args, **kwargs):
        return True


class KeyHammerCmd(om.MPxCommand):
    cmd_name = 'keyHammer'
    anim_cache = None
    
    def __init__(self):
        om.MPxCommand.__init__(self)
    
    @staticmethod
    def cmd_creator():
        return KeyHammerCmd()
    
    def doIt(self, args):
        self.anim_cache = oma.MAnimCurveChange()
        data.anim_cache = self.anim_cache
        keyhammer.do()
    
    def redoIt(self):
        self.anim_cache.redoIt()
    
    def undoIt(self):
        self.anim_cache.undoIt()
    
    def isUndoable(*args, **kwargs):
        return True
