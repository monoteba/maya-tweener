import sys
import os
import shutil
import urllib2
import json
import uuid
import zipfile
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from shiboken2 import wrapInstance

github_url = 'https://api.github.com/repos/mortenblaa/maya-tweener/releases/latest'
gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')


def onMayaDroppedPythonFile(*args):
    qApp.processEvents()
    utils.executeDeferred(main)


def main():
    result = cmds.confirmDialog(t='Tweener Installation',
                                m='Would you like to download and install Tweener?',
                                button=['Yes', 'No'],
                                db='Yes',
                                cb='No',
                                ds='No')
    
    if result == 'No':
        return
    
    sys.stdout.write('# Downloading Tweener...\n')
    
    qApp.processEvents()
    zip_path = download()
    
    plugin_path = install(zip_path)
    load(plugin_path)


def download():
    # get zip url from github
    response = urllib2.urlopen(github_url, timeout=5)
    data = json.load(response)
    
    assets = data['assets']
    if assets is None or len(assets) == 0:
        sys.stderr.write('# Could not locate zip from url %s' % github_url)
        cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
        exit(1)
    
    asset = assets[0]
    zip_url = asset['browser_download_url']
    
    # download and temporarily save zip file
    name = 'tweener-' + uuid.uuid1().hex + '.zip'
    dir_path = os.path.dirname(__file__)
    zip_path = dir_path + '/' + name
    
    # url
    f = urllib2.urlopen(zip_url, timeout=5)
    
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
                qApp.processEvents()
    
    except Exception as e:
        sys.stderr.write('%s\n' % e)
        cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
        exit(1)
    finally:
        sys.stdout.write('# Download successful, installing...\n')
    
    cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
    return zip_path


def install(zip_path):
    # maya plug-ins dir
    maya_app_dir = cmds.internalVar(userAppDir=True)
    
    # create maya plug-ins dir (if it does not exist)
    maya_plug_in_dir = maya_app_dir + 'plug-ins/'
    if not os.path.exists(maya_plug_in_dir):
        try:
            sys.stdout.write('# plug-ins directory does not exists, creating it at %s\n' % maya_plug_in_dir)
            os.makedirs(maya_plug_in_dir)
        except Exception as e:
            sys.stderr.write('%s\n' % e)
            cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
            exit(2)
    
    # extract zip
    extract_path = maya_plug_in_dir + 'tweener'
    
    if os.path.exists(extract_path):
        try:
            shutil.rmtree(extract_path)  # remove existing folder
        except Exception as e:
            sys.stderr.write('%s\n' % e)
            cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
            exit(3)
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
            sys.stderr.write('%s\n' % e)
            cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
            exit(4)
    
    try:
        with open(maya_modules_dir + 'tweener.mod', 'w') as f:
            f.write('+ Tweener 0.0 %s\n' % extract_path)
            f.write('MAYA_PLUG_IN_PATH +:= \n')
    except Exception as e:
        sys.stderr.write('%s\n' % e)
        cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
        exit(5)
    finally:
        sys.stdout.write('# Created module file at "%s"\n' % maya_modules_dir)
    
    # clean-up
    sys.stdout.write('# Cleaning up...\n')
    try:
        os.remove(zip_path)
    except Exception as e:
        sys.stderr.write('%s\n' % e)
        cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
        exit(6)
    finally:
        sys.stdout.write('\t# Removed %s\n' % zip_path)
    
    return extract_path


def load(plugin_path):
    if os.name == 'nt':
        env_path = ';%s' % plugin_path
    else:
        env_path = ':%s' % plugin_path
    
    maya_plugin_path = mel.eval('getenv "MAYA_PLUG_IN_PATH"')
    
    if plugin_path not in maya_plugin_path:
        mel.eval('putenv "MAYA_PLUG_IN_PATH" "' + maya_plugin_path + env_path + '"')
    
    if cmds.pluginInfo('tweener.py', q=True, r=True):
        try:
            cmds.unloadPlugin('tweener.py', force=True)
        except:
            pass
    
    sys.path.append(plugin_path)
    
    try:
        import tweener
        reload(tweener)
        tweener.reload_mods()
    except Exception as e:
        sys.stderr.write('%s\n' % e)
    
    cmds.loadPlugin('tweener.py')
    cmds.tweener()
    
    answer = cmds.confirmDialog(t='Tweener Installed!',
                                m='Tweener was successfully installed at:\n'
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
            sys.stderr.write('%s\n' % e)
    
    sys.stdout.write('# Tweener install completed! See the Script Editor for more information.\n')
