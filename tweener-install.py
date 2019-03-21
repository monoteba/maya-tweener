import sys
import os
import shutil
import urllib2
import json
import uuid
import zipfile
import maya.cmds as cmds
import maya.mel as mel

github_url = 'https://api.github.com/repos/mortenblaa/maya-tweener/releases/latest'


def onMayaDroppedPythonFile(*args):
    sys.stdout.write('# Downloading Tweener...\n')
    zip_path = download()
    plugin_path = install(zip_path)
    load(plugin_path)


def download():
    # get zip url from github
    response = urllib2.urlopen(github_url)
    data = json.load(response)
    
    assets = data['assets']
    if assets is None or len(assets) == 0:
        sys.stderr.write('# Could not locate .zip')
        return
    
    asset = assets[0]
    zip_url = asset['browser_download_url']
    print('zip url: %s' % zip_url)
    
    # download and temporarily save zip file
    name = 'tweener-' + uuid.uuid1().hex + '.zip'
    dir_path = os.path.dirname(__file__)
    zip_path = dir_path + '/' + name
    
    try:
        f = urllib2.urlopen(zip_url)
        
        with open(zip_path, 'wb') as local_file:
            local_file.write(f.read())
    except Exception as e:
        sys.stderr.write('%s\n' % e)
        exit(1)
    finally:
        sys.stdout.write('# Download successful, installing...\n')
    
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
            exit(1)
    
    # extract zip
    extract_path = maya_plug_in_dir + 'tweener'
    
    if os.path.exists(extract_path):
        try:
            shutil.rmtree(extract_path)  # remove existing folder
        except Exception as e:
            sys.stderr.write('%s\n' % e)
            exit(1)
        finally:
            sys.stdout.write('# Removed old installation\n')
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    # create maya modules dir (if it does not exist)
    maya_modules_dir = maya_app_dir + 'modules/'
    if not os.path.exists(maya_modules_dir):
        try:
            sys.stdout.write('# modules directory does not exists, creating it at %s\n' % maya_modules_dir)
            os.makedirs(maya_modules_dir)
        except Exception as e:
            sys.stderr.write('%s\n' % e)
            exit(1)
    
    try:
        with open(maya_modules_dir + 'tweener.mod', 'w') as f:
            f.write('+ Tweener 0.0 %s\n' % extract_path)
            f.write('MAYA_PLUG_IN_PATH +:= \n')
    except Exception as e:
        sys.stderr.write('%s\n' % e)
        exit(1)
    finally:
        sys.stdout.write('# Created module file\n')
    
    # clean-up
    sys.stdout.write('# Cleaning up...\n')
    try:
        os.remove(zip_path)
    except Exception as e:
        sys.stderr.write('%s\n' % e)
        exit(1)
    finally:
        sys.stdout.write('# Removed %s\n' % zip_path)
    
    return extract_path


def load(plugin_path):
    plugin_path = ':%s' % plugin_path
    maya_plugin_path = mel.eval('getenv "MAYA_PLUG_IN_PATH"')
    
    if plugin_path not in maya_plugin_path:
        mel.eval('putenv "MAYA_PLUG_IN_PATH" "' + maya_plugin_path + plugin_path + '"')
    
    try:
        cmds.unloadPlugin('tweener.py', force=True)
    except:
        pass
    
    try:
        import tweener
        reload(tweener)
        tweener.reload_mods()
    except Exception as e:
        sys.stderr.write('%s\n' % e)
    
    cmds.loadPlugin('tweener.py')
    cmds.tweener()
    
    answer = cmds.confirmDialog(t='Tweener Installed!',
                                m='Tweener was successfully installed!\n'
                                  'Would you like to add a shelf button to the current shelf?',
                                button=['Yes', 'No'],
                                db='Yes',
                                cb='No',
                                ds='No')
    
    if answer == 'Yes':
        try:
            tweener.ui.add_shelf_button(path=plugin_path)
        except Exception as e:
            sys.stderr.write('%s\n' % e)
