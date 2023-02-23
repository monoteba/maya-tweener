"""
Tweener is a tool similar to TweenMachine or aTools/animBot. It allows you to quickly create inbetweens in Maya by
favouring adjacent keys and can speed up the animation process.

Please refer to the plug-ins GitHub page for more information at https://github.com/monoteba/maya-tweener
"""

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
import mods.animdata as animdata
import mods.keyhammer as keyhammer
import mods.tool as tool
import mods.options as options


def maya_useNewAPI():
    pass


def reload_mods():
    """
    For development and installation purposes only
    """
    
    import inspect
    
    path = (os.path.dirname(__file__)).lower()
    to_delete = []
    
    for key, module in sys.modules.items():
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
    """
    Initialize plugin commands
    """
    
    plugin_fn = om.MFnPlugin(plugin,
                             "Morten Andersen",
                             g.plugin_version,
                             "Any")
    
    # register TweenerCmd
    try:
        plugin_fn.registerCommand(TweenerCmd.cmd_name, TweenerCmd.cmd_creator,
                                  TweenerCmd.syntax_creator)
    except Exception as e:
        sys.stderr.write("%s\n" % str(e))
        sys.stderr.write("Failed to register command: %s\n" % TweenerCmd.cmd_name)
        raise
    else:
        sys.stdout.write("# Successfully registered command %s\n" % TweenerCmd.cmd_name)
    
    # register TweenerCmd
    try:
        plugin_fn.registerCommand(TweenerUICmd.cmd_name,
                                  TweenerUICmd.cmd_creator,
                                  TweenerUICmd.syntax_creator)
    except Exception as e:
        sys.stderr.write("%s\n" % str(e))
        sys.stderr.write("Failed to register command: %s\n" % TweenerUICmd.cmd_name)
        raise
    else:
        sys.stdout.write("# Successfully registered command %s\n" % TweenerUICmd.cmd_name)
    
    # register KeyHammerCmd
    try:
        plugin_fn.registerCommand(KeyHammerCmd.cmd_name,
                                  KeyHammerCmd.cmd_creator)
    except Exception as e:
        sys.stderr.write("%s\n" % str(e))
        sys.stderr.write("Failed to register command: %s\n" % KeyHammerCmd.cmd_name)
        raise
    else:
        sys.stdout.write("# Successfully registered command %s\n" % KeyHammerCmd.cmd_name)
    
    # register TweenerToolCmd
    try:
        plugin_fn.registerCommand(TweenerToolCmd.cmd_name,
                                  TweenerToolCmd.cmd_creator)
    except Exception as e:
        sys.stderr.write("%s\n" % str(e))
        sys.stderr.write("Failed to register command: %s\n" % TweenerToolCmd.cmd_name)
        raise
    else:
        sys.stdout.write("# Successfully registered command %s\n" % TweenerToolCmd.cmd_name)
    
    g.plugin_path = os.path.dirname(cmds.pluginInfo(plugin_fn.name(), q=True, path=True)) + '/'
    
    # restore the window, if it exists
    try:
        if cmds.workspaceControl('tweenerUIWindowWorkspaceControl', exists=True):
            if not cmds.workspaceControl('tweenerUIWindowWorkspaceControl', q=True, collapse=True):
                cmds.evalDeferred('import maya.cmds as cmds; cmds.tweenerUI(restore=False)', lp=True)
    except Exception as e:
        sys.stderr.write("%s\n" % str(e))
        sys.stderr.write("Failed to restore Tweener window.\n")


def uninitializePlugin(plugin):
    """
    Uninitialize plugin commands
    """
    
    plugin_fn = om.MFnPlugin(plugin)
    
    # deregister TweenerCmd
    try:
        plugin_fn.deregisterCommand(TweenerCmd.cmd_name)
    except Exception:
        sys.stderr.write("Failed to deregister command: %s\n" % TweenerCmd.cmd_name)
        raise
    else:
        sys.stdout.write("# Successfully unregistered command %s\n" % TweenerCmd.cmd_name)
    
    # deregister TweenerCmd
    try:
        plugin_fn.deregisterCommand(TweenerUICmd.cmd_name)
    except Exception:
        sys.stderr.write("Failed to deregister command: %s\n" % TweenerUICmd.cmd_name)
        raise
    else:
        sys.stdout.write("# Successfully unregistered command %s\n" % TweenerUICmd.cmd_name)
    
    # deregister KeyHammerCmd
    try:
        plugin_fn.deregisterCommand(KeyHammerCmd.cmd_name)
    except Exception:
        sys.stderr.write("Failed to deregister command: %s\n" % KeyHammerCmd.cmd_name)
        raise
    else:
        sys.stdout.write("# Successfully unregistered command %s\n" % KeyHammerCmd.cmd_name)
    
    # deregister TweenerToolCmd
    try:
        plugin_fn.deregisterCommand(TweenerToolCmd.cmd_name)
    except Exception:
        sys.stderr.write("Failed to deregister command: %s\n" % TweenerToolCmd.cmd_name)
        raise
    else:
        sys.stdout.write("# Successfully unregistered command %s\n" % TweenerToolCmd.cmd_name)


"""
Maya Command (MPxCommand)
"""


class TweenerCmd(om.MPxCommand):
    """
    tweener command
    """
    
    cmd_name = 'tweener'
    anim_cache = None
    
    # command flags
    interpolant_flag = '-t'
    interpolant_flag_long = '-interpolant'
    type_flag = '-tp'
    type_flag_long = '-type'
    new_cache_flag = '-nc'
    new_cache_long = '-newCache'
    
    # default command argument values
    blend_arg = 0
    new_cache_arg = True
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
        syntax.addFlag(cls.new_cache_flag, cls.new_cache_long, om.MSyntax.kBoolean)
        syntax.addFlag(cls.type_flag, cls.type_flag_long, om.MSyntax.kLong)
        return syntax
    
    def pass_args(self, args):
        arg_data = om.MArgParser(self.syntax(), args)
        
        if arg_data.isFlagSet(self.interpolant_flag):
            self.blend_arg = arg_data.flagArgumentDouble(self.interpolant_flag, 0)
        
        if arg_data.isFlagSet(self.new_cache_flag):
            self.new_cache_arg = arg_data.flagArgumentBool(self.new_cache_flag, 0)
        
        if arg_data.isFlagSet(self.type_flag):
            self.type_arg = arg_data.flagArgumentInt(self.type_flag, 0)
        
        return arg_data.numberOfFlagsUsed
    
    def doIt(self, args):
        # pass arguments, and if 0 flags are given, show the window
        if self.pass_args(args) == 0:
            ui.show()
            return
        
        # the animation cache must be stored in the command instance itself so
        # we pass a reference to the cache to the Lt class, so we can manipulate
        # the currently active cache
        if self.new_cache_arg:
            # initialize, then create a new cache
            self.anim_cache = oma.MAnimCurveChange()
            animdata.anim_cache = self.anim_cache
            animdata.prepare(mode=options.BlendingMode.get_mode_from_id(self.type_arg))
        
        # always interpolate
        self.anim_cache = animdata.anim_cache
        tween.interpolate(blend=self.blend_arg, mode=options.BlendingMode.get_mode_from_id(self.type_arg))
    
    def redoIt(self):
        self.anim_cache.redoIt()
    
    def undoIt(self):
        self.anim_cache.undoIt()
    
    def isUndoable(*args, **kwargs):
        return True


class TweenerUICmd(om.MPxCommand):
    """
    tweener ui command
    """
    
    cmd_name = 'tweenerUI'
    
    # command flags
    restore_flag = '-r'
    restore_flag_lone = '-restore'
    
    # default command argument values
    restore_arg = False
    
    def __init__(self):
        om.MPxCommand.__init__(self)
    
    @staticmethod
    def cmd_creator():
        return TweenerUICmd()
    
    @classmethod
    def syntax_creator(cls):
        syntax = om.MSyntax()
        syntax.addFlag(cls.restore_flag, cls.restore_flag_lone,
                       om.MSyntax.kBoolean)
        return syntax
    
    def pass_args(self, args):
        arg_data = om.MArgParser(self.syntax(), args)
        
        if arg_data.isFlagSet(self.restore_flag):
            self.restore_arg = arg_data.flagArgumentBool(self.restore_flag, 0)
        
        return arg_data.numberOfFlagsUsed
    
    def doIt(self, args):
        # pass arguments, and if 0 flags are given, show the window
        if self.pass_args(args) == 0:
            ui.show()
            return
        
        ui.show(restore=self.restore_arg)
    
    def isUndoable(*args, **kwargs):
        return False


class KeyHammerCmd(om.MPxCommand):
    """
    keyhammer command
    """
    
    cmd_name = 'keyHammer'
    anim_cache = None
    
    def __init__(self):
        om.MPxCommand.__init__(self)
    
    @staticmethod
    def cmd_creator():
        return KeyHammerCmd()
    
    def doIt(self, args):
        self.anim_cache = oma.MAnimCurveChange()
        animdata.anim_cache = self.anim_cache
        self.clearResult()
        self.setResult(keyhammer.do())
    
    def redoIt(self):
        self.anim_cache.redoIt()
    
    def undoIt(self):
        self.anim_cache.undoIt()
    
    def isUndoable(*args, **kwargs):
        return True
    
    def __str__(self):
        return self.cmd_name


class TweenerToolCmd(om.MPxCommand):
    """
    tool command
    """
    
    cmd_name = 'tweenerTool'
    
    def __init__(self):
        om.MPxCommand.__init__(self)
    
    @staticmethod
    def cmd_creator():
        return TweenerToolCmd()
    
    def doIt(self, args):
        tool.activate()
