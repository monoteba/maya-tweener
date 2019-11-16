# Tweener <img src="icons/tweener-icon.svg" width="32px" height="32px">

<p align="center">
<img src="tweener-screenshot.png" width="50%" height="auto">
</p>

Tweener has nothing to do with young people, basketball or [that tennis move between your legs](https://en.wikipedia.org/wiki/Tweener_(tennis)).

Instead, Tweener is a tool similar to TweenMachine or aTools/animBot. It allows you to quickly create in-betweens or adjust 
existing keys by interpolating towards adjacent keyframes, and can speed-up your workflow when creating breakdowns and 
in-betweens.

I am an animator myself and so I very much tailor the tool to my own needs.

## Requirements

Maya 2017 Update 3 or later.

## Installation

Download [tweener-install.py](https://github.com/mortenblaa/maya-tweener/raw/master/tweener-install.py) and drag 
the file into Maya's viewport.

If you prefer to manually install the plug-in, refer to "Installation" page in the wiki.

## Description

Tweener is quite simple. Select the tween mode and drag the slider to interpolate between poses. I'll encourage you to 
explore each type. See the description of each mode below.

### In-between Modes

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


## Known Limitations and Issues
The tool is still at an early stage and there are few limitations to be aware of. 

- Does not work with animation layers!

Refer to the [issues](https://github.com/mortenblaa/maya-tweener/issues) page for known issues.

## Additional Information

Refer to the [wiki](https://github.com/mortenblaa/maya-tweener/wiki) for more information.

## Support Development

<a href="https://www.buymeacoffee.com/O6Q5vN9" target="_blank" style="display: inline-block; width: 217px; height: 51px;"><img src="https://cdn.buymeacoffee.com/buttons/default-blue.png" alt="Buy Me A Coffee"></a>