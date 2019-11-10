<img src="icons/tweener-icon.svg" width="32px" height="32px">

# Tweener

<p align="center">
<img src="tweener-screenshot.png" width="50%" height="auto">
</p>

Tweener has nothing to do with young people, basketball or that tennis move between your legs.

Instead, Tweener is a tool similar to TweenMachine or aTools/animBot. It allows you to quickly create inbetweens or adjust 
existing keys by interpolating towards adjacent keyframes, and can speed-up your workflow when creating breakdowns and 
inbetweens.

I am an animator myself and so I very much tailor the tool to my own needs.

## Requirements

Maya 2017 Update 3 or later.

## Installation

Download [tweener-install.py](https://github.com/mortenblaa/maya-tweener/raw/master/tweener-install.py) and drag 
the file into Maya's viewport.

If you prefer to manually install the plug-in, refer to "Manual Installation" further down this page.

## Description

Tweener is quite simple. Select the tween mode and drag the slider to interpolate between poses. I'll encourage you to 
explore each type. See the description of each mode below.

### Tween Modes

| Icon | Mode | Description |
| :---: | :--- | :--- |
| <img src="icons/between.svg" width="20" height="20"> | Between | Interpolates between two adjacent keys, ignoring the current key. |
| <img src="icons/towards.svg" width="20" height="20"> | Towards | Interpolates towards two adjacent keys based on the current key. |
| <img src="icons/average.svg" width="20" height="20"> | Average | Interpolates towards the average value of the selected keys. |
| <img src="icons/curve.svg" width="20" height="20"> | Curve | Interpolates along the curve formed by the two adjacent keys' tangents. |
| <img src="icons/default.svg" width="20" height="20"> | Default | Interpolates towards or away from the default value of each attribute. |

### Additional Buttons

| Icon | Name | Description |
| :---: | :--- | :--- |
| <img src="icons/overshoot.svg" width="20" height="20"> | Overshoot | Extends the interpolation from `[-100:100]` to `[-200:200]` and allows you to go past the target. |
| <img src="icons/keyhammer.svg" width="20" height="20"> | Key Hammer | Adds a key for every attribute for any key on selected objects. The manual equivalent method would be to go to the first key and press `S`, go to the next keyframe and press `S`, go to the next keyframe and press `S` etc. for every keyframe. |
| <img src="icons/tick-special.svg" width="20" height="20"> | Special Tick Color | Sets the current frame, selected keys, or time range to the special keyframe tick color. |
| <img src="icons/tick-normal.svg" width="20" height="20"> | Normal Tick Color | Sets the current frame, selected keys, or time range to the normal keyframe tick color. |


## Known Limitations
The tool is still at an early stage and there are few limitations to be aware of. 

- Does not work with animation layers!

## Manual Installation

### 1. Download

Download the latest release from the [Releases](https://github.com/mortenblaa/maya-tweener/releases) page. 

### 2. Copy to plug-ins folder

Unzip the file and copy the contents to a folder named **tweener** inside your Maya's plug-ins folder.

Typical locations for the plug-ins folder:

**Windows:** `C:\Users\<username>\Documents\maya\plug-ins\`

**macOS:** `~/Library/Preferences/Autodesk/maya/plug-ins/`

In some cases the plug-ins folder will not exists, in which case you can just create it.

### 3. Create module file

Go to the **modules** folder inside your Maya preferences directory. Again, if it doesn't exist you need to create it.

Create a new file and name it **tweener.mod** inside the **modules** folder, and add the following lines where you replace the path to your own plug-ins directory:

Windows example:

```
+ Tweener 0.0 C:\Users\<username>\Documents\maya\modules\
MAYA_PLUG_IN_PATH +:= 
```

macOS example:

```
+ Tweener 0.0 /Users/username/Library/Preferences/Autodesk/maya/plug-ins/tweener
MAYA_PLUG_IN_PATH +:= 
```

### 4. Restart Maya

You need to restart Maya after copying the files. You can verify the installation of the plug-in by seeing if `tweener.py` shows up in the Plug-in Manager. All plug-in paths can be found using the following Python code in the Script Editor:

```python
import maya.mel
paths = maya.mel.eval('getenv MAYA_PLUG_IN_PATH').split(':')
for p in paths:
    print p
```

### 5. Launch Tweener and add a shelf button

After the plug-in is succesfully installed, execute the following three lines as Python or add them to a shelf button:

```python
import maya.cmds as cmds
cmds.loadPlugin(tweener.py, q=True)
cmds.tweener()
```

The icon is located in the **icons** folder where you installed the plug-in.

## Uninstall
Tweener installs a few files in your local Maya preferences directory. The typical locations are:

**Windows:** `C:\Users\<username>\Documents\maya\`

**macOS:** `~/Library/Preferences/Autodesk/maya/`

Remove the `tweener.mod` inside the `modules` folder, and the `tweener` folder inside the `plug-ins` folder.