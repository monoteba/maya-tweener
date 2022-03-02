import sys
import os
import shutil
import json
import uuid
import zipfile
import logging
import ssl
from functools import partial

if sys.version_info >= (3, 0):
    from urllib.request import urlopen
else:
    from urllib2 import urlopen
    
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from shiboken2 import wrapInstance

github_url = 'https://api.github.com/repos/mortenblaa/maya-tweener/releases/latest'
gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')

plugin_name = 'tweener.py'


def onMayaDroppedPythonFile(*args):
    QApplication.processEvents()
    utils.executeDeferred(main)


def main():
    result = cmds.confirmDialog(t='Tweener Installation',
                                m='Would you like to download and install Tweener?',
                                button=['Download', 'Offline Installation', 'Cancel'],
                                db='Download',
                                cb='Cancel',
                                ds='Cancel')
    
    if result == 'Cancel':
        return
    
    if result == 'Offline Installation':
        show_offline_window()
        return
    
    sys.stdout.write('# Downloading Tweener...\n')
    
    QApplication.processEvents()
    zip_path = download()
    if zip_path is None:
        show_offline_window()
        return
    
    plugin_path = install(zip_path)
    load(plugin_path)


def download():
    try:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS) if sys.version_info >= (3, 0) else ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    except Exception as e:
        sys.stdout.write('Error: %s\n' % e)
        sys.stdout.write('# Failed to set SSL Context.\n')
        return None
        
    try:
        # get zip url from github        
        response = urlopen(github_url, timeout=10, context=ssl_context)
        data = json.load(response)
    except Exception as e:
        sys.stdout.write('Error: %s\n' % e)
        sys.stdout.write('# No internet connection: using offline installation.\n')
        return None
    
    try:
        assets = data['assets']
    except Exception as e:
        logging.exception(e)
        return None
    
    if assets is None or len(assets) == 0:
        sys.stderr.write('# Could not locate zip from url %s' % github_url)
        cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
        return None
    
    asset = assets[0]
    zip_url = asset['browser_download_url']
    
    # download and temporarily save zip file
    name = 'tweener-' + uuid.uuid1().hex + '.zip'
    dir_path = os.path.dirname(__file__)
    zip_path = dir_path + '/' + name
    
    # url
    try:
        f = urlopen(zip_url, timeout=10, context=ssl_context)
    except Exception as e:
        logging.exception(e)
        return None
    
    # try to get file size
    try:
        total_size = f.info().getheader('Content-Length').strip()
        header = True
    except AttributeError:
        header = False  # a response doesn't always include the "Content-Length" header
    
    if header:
        total_size = int(total_size)
    else:
        total_size = 1
    
    cmds.progressBar(gMainProgressBar,
                     edit=True,
                     beginProgress=True,
                     isInterruptable=False,
                     status='"Downloading Tweener...',
                     maxValue=total_size)
    
    try:
        with open(zip_path, 'wb') as local_file:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                cmds.progressBar(gMainProgressBar, e=True, step=len(chunk))
                local_file.write(chunk)
                QApplication.processEvents()
    
    except Exception as e:
        logging.exception(e)
        cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
        return None
    finally:
        sys.stdout.write('# Download successful, installing...\n')
    
    cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
    return zip_path


def install(zip_path, remove_zip=True):
    # maya plug-ins dir
    maya_app_dir = cmds.internalVar(userAppDir=True)
    
    # create maya plug-ins dir (if it does not exist)
    maya_plug_in_dir = maya_app_dir + 'plug-ins/'
    if not os.path.exists(maya_plug_in_dir):
        try:
            sys.stdout.write('# plug-ins directory does not exists, creating it at %s\n' % maya_plug_in_dir)
            os.makedirs(maya_plug_in_dir)
        except Exception as e:
            logging.exception(e)
            cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
            return None
    
    # extract zip
    extract_path = maya_plug_in_dir + 'tweener'
    
    if os.path.exists(extract_path):
        try:
            shutil.rmtree(extract_path)  # remove existing folder
        except Exception as e:
            logging.exception(e)
            cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
            return None
        finally:
            sys.stdout.write('# Removed old installation!\n')
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    # create maya modules dir (if it does not exist)
    maya_modules_dir = maya_app_dir + 'modules/'
    if not os.path.exists(maya_modules_dir):
        try:
            os.makedirs(maya_modules_dir)
        except Exception as e:
            logging.exception(e)
            cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
            return None
    
    try:
        with open(maya_modules_dir + 'tweener.mod', 'w') as f:
            f.write('+ Tweener 0.0 %s\n' % extract_path)
            f.write('MAYA_PLUG_IN_PATH +:= \n')
    except Exception as e:
        logging.exception(e)
        cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
        return None
    finally:
        sys.stdout.write('# Created module file at "%s"\n' % maya_modules_dir)
    
    # clean-up
    if remove_zip:
        try:
            sys.stdout.write('# Cleaning up...\n')
            os.remove(zip_path)
        except Exception as e:
            logging.exception(e)
            cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
        finally:
            sys.stdout.write('# Removed %s\n' % zip_path)
    
    return extract_path


def load(plugin_path):
    if os.name == 'nt':
        env_path = ';%s' % plugin_path
    else:
        env_path = ':%s' % plugin_path
    
    maya_plugin_path = mel.eval('getenv "MAYA_PLUG_IN_PATH"')
    
    if plugin_path not in maya_plugin_path:
        mel.eval('putenv "MAYA_PLUG_IN_PATH" "' + maya_plugin_path + env_path + '"')
    
    if cmds.pluginInfo(plugin_name, q=True, r=True):
        try:
            cmds.unloadPlugin(plugin_name, force=True)
        except Exception as e:
            logging.exception(e)
    
    sys.path.append(plugin_path)
    
    try:
        import tweener
        
        if sys.version_info >= (3, 0):
            import importlib
            importlib.reload(tweener)
        else:
            reload(tweener)
            
        tweener.reload_mods()
    except Exception as e:
        logging.exception(e)
    
    try:
        cmds.loadPlugin(plugin_name)
        if cmds.pluginInfo(plugin_name, q=True, r=True):
            cmds.pluginInfo(plugin_name, e=True, autoload=True)
    except Exception as e:
        logging.exception(e)
    
    try:
        cmds.tweener()
    except Exception as e:
        cmds.warning('Could not execute tweener command: %s' % str(e))
    
    answer = cmds.confirmDialog(t='Tweener Installed!',
                                m='Tweener was installed at:\n'
                                  '%s\n\n'
                                  'Would you like to add a shelf button to the current shelf?' % plugin_path,
                                button=['Yes', 'No'],
                                db='Yes',
                                cb='No',
                                ds='No')
    
    if answer == 'Yes':
        try:
            tweener.ui.add_shelf_button(path=plugin_path)
        except Exception as e:
            logging.exception(e)
    
    sys.stdout.write('# Tweener install completed! See the Script Editor for more information.\n')


def show_offline_window():
    window = cmds.window(title="Tweener Offline Install", resizeToFitChildren=True, sizeable=False)
    form = cmds.formLayout(nd=100)
    
    column = cmds.columnLayout(adjustableColumn=True)
    cmds.text(label='Tweener was not downloadeded automatically.', align='left')
    cmds.text(label=' ')
    cmds.text(label='Please download the latest release from:', align='left')
    cmds.text(
        label='<a style="color:#ff8a00;" href="https://github.com/mortenblaa/maya-tweener/releases/latest">'
              'https://github.com/mortenblaa/maya-tweener/releases/latest</a>',
        align='left',
        hyperlink=True,
        highlightColor=[1.0, 1.0, 1.0])
    cmds.text(label=' ')
    cmds.text(label='The file is called \"tweener-1.0.0.zip\" or similar.', align='left')
    cmds.text(label=' ')
    cmds.text(label=' ')
    cmds.setParent('..')
    
    button = cmds.button(label='Install from .zip', command=partial(offline_install, window))
    cmds.setParent('..')
    
    cmds.formLayout(form, e=True, attachForm=[(column, 'left', 10),
                                              (column, 'top', 10),
                                              (column, 'right', 10),
    
                                              (button, 'left', 10),
                                              (button, 'bottom', 10),
                                              (button, 'right', 10)])
    cmds.showWindow(window)


def offline_install(window, *args):
    cmds.deleteUI(window)
    zip_path = get_zip()
    
    if not zip_path:
        show_offline_window()
        return
    
    print(zip_path)
    plugin_path = install(zip_path[0], remove_zip=False)
    load(plugin_path)


def get_zip():
    zipFilter = 'ZIP file (*.zip)'
    return cmds.fileDialog2(fileFilter=zipFilter, dialogStyle=2, fileMode=1)
