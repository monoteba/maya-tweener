"""
ui module
"""

import maya.api.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel
import sys
import os

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# PySide2 is for Maya 2017+
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from shiboken2 import wrapInstance

import globals as g
import tween

tweener_window = None


def maya_useNewAPI():
    pass


def get_main_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QMainWindow)


def show():
    if cmds.workspaceControl('tweenerUIWindowWorkspaceControl', exists=True):
        cmds.deleteUI('tweenerUIWindowWorkspaceControl')
    
    TweenerUIScript()
    
    # global tweener_window
    # if tweener_window is None:
    #     tweener_window = TweenerUI(parent=get_main_maya_window())
    
    # tweener_window.show(dockable=True)  # show the window
    # tweener_window.raise_()  # raise it on top of others
    # tweener_window.activateWindow()  # set focus to it


def delete():
    global tweener_window
    if tweener_window is not None:
        tweener_window.deleteLater()
        tweener_window = None


def add_shelf_button(path=None):
    if not path:
        path = g.plugin_path
    
    if path.endswith('/'):
        icon_path = path
    else:
        icon_path = path + '/'
    
    icon_path = icon_path + 'icons/tweener-icon.svg'
    
    gShelfTopLevel = mel.eval('$tmpVar=$gShelfTopLevel')
    tabs = cmds.tabLayout(gShelfTopLevel, q=True, childArray=True)
    
    for tab in tabs:
        if cmds.shelfLayout(tab, q=True, visible=True):
            cmds.shelfButton(parent=tab, ann='Open Tweener', label='Tweener',
                             image=icon_path,
                             useAlpha=True, style='iconOnly',
                             command='import maya.cmds as cmds; cmds.loadPlugin("tweener.py", quiet=True); cmds.tweener();')


class TweenerUI(MayaQWidgetDockableMixin, QMainWindow):
    def __init__(self, parent=None):
        super(TweenerUI, self).__init__(parent=parent)
        
        # set slider window properties
        self.setWindowTitle('Tweener')
        
        if os.name == 'nt':  # windows platform
            self.setWindowFlags(Qt.Window)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        self.setProperty("saveWindowPref", True)  # maya's automatic window management
        
        # variables
        self.idle_callback = None
        
        # define window dimensions
        self.setMinimumWidth(360)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        # style
        self.setStyleSheet(
            'QLineEdit { padding: 0 3px; border-radius: 2px; }'
            'QLineEdit:disabled { color: rgb(128, 128, 128); background-color: rgb(64, 64, 64); }'
            'QLabel:disabled { background-color: none; }'
            'QPushButton { padding: 0; border-radius: 1px; background-color: rgb(93, 93, 93); }'
            'QPushButton:hover { background-color: rgb(112, 112, 112); }'
            'QPushButton:pressed { background-color: rgb(29, 29, 29); }'
            'QPushButton:checked { background-color: rgb(82, 133, 166); }'
        )
        
        widget_height = 16
        
        # setup central widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # layout window
        layout = QVBoxLayout(main_widget)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(4)
        main_layout.addLayout(layout)
        
        # top button layout
        top_button_layout = QHBoxLayout(main_widget)
        
        # mode buttons
        self.interp_mode = 'Between'
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(2)
        mode_between_btn = ModeButton('Between')
        mode_towards_btn = ModeButton('Towards')
        mode_curve_tangent_btn = ModeButton('Curve')
        mode_default_btn = ModeButton('Default')
        
        mode_between_btn.clicked.connect(self.set_mode_button)
        mode_between_btn.setChecked(True)
        mode_towards_btn.clicked.connect(self.set_mode_button)
        mode_curve_tangent_btn.clicked.connect(self.set_mode_button)
        mode_default_btn.clicked.connect(self.set_mode_button)
        
        self.mode_button_group = QButtonGroup()
        self.mode_button_group.addButton(mode_between_btn)
        self.mode_button_group.addButton(mode_towards_btn)
        self.mode_button_group.addButton(mode_curve_tangent_btn)
        self.mode_button_group.addButton(mode_default_btn)
        
        self.mode_button_group.setId(mode_between_btn, 0)
        self.mode_button_group.setId(mode_towards_btn, 1)
        self.mode_button_group.setId(mode_curve_tangent_btn, 2)
        self.mode_button_group.setId(mode_default_btn, 3)
        
        mode_layout.addWidget(mode_between_btn)
        mode_layout.addWidget(mode_towards_btn)
        mode_layout.addWidget(mode_curve_tangent_btn)
        mode_layout.addWidget(mode_default_btn)
        
        # misc buttons
        misc_button_layout = QHBoxLayout()
        misc_button_layout.setSpacing(2)
        
        self.overshoot_btn = ModeButton(icon='icons/overshoot.svg')
        self.overshoot_btn.clicked.connect(self.overshoot_button_clicked)
        self.overshoot_btn.setToolTip('Toggle Overshoot')
        
        self.keyhammer_btn = ModeButton(icon='icons/keyhammer.svg', is_checkable=False)
        self.keyhammer_btn.clicked.connect(self.keyhammer_button_clicked)
        self.keyhammer_btn.setToolTip('Hammer Keys')
        
        misc_button_layout.addWidget(self.overshoot_btn)
        misc_button_layout.addWidget(self.keyhammer_btn)
        
        # slider
        slider_layout = QVBoxLayout(main_widget)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        slider_layout.setSpacing(4)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFixedHeight(widget_height)
        self.slider.setValue(0)
        self.slider.setMinimum(-100)
        self.slider.setMaximum(100)
        self.slider.setTickInterval(1)
        
        self.slider.sliderPressed.connect(self.slider_pressed)
        self.slider.sliderReleased.connect(self.slider_released)
        
        slider_layout.addWidget(self.slider)
        
        # slider value label and version label
        slider_label_layout = QHBoxLayout(main_widget)
        slider_label_layout.setContentsMargins(0, 0, 0, 0)
        slider_label_layout.setSpacing(0)
        
        self.slider_label = QLabel('')
        self.slider_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        
        version_label = QLabel(g.version)
        version_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        version_label.setStyleSheet('color: rgba(255, 255, 255, 54);')
        
        slider_label_layout.addWidget(QWidget())  # empty widget to balance layout
        slider_label_layout.addWidget(self.slider_label)
        slider_label_layout.addWidget(version_label)
        
        # fraction buttons
        fraction_layout = QHBoxLayout(main_widget)
        fraction_layout.setSpacing(2)
        
        self.preset_0_000_btn = FractionButton(radius=12, fraction=0.0)
        self.preset_0_167_btn = FractionButton(radius=12, fraction=0.167)
        self.preset_0_250_btn = FractionButton(radius=12, fraction=0.25)
        self.preset_0_333_btn = FractionButton(radius=12, fraction=0.333)
        self.preset_0_500_btn = FractionButton(radius=12, fraction=0.5)
        self.preset_0_667_btn = FractionButton(radius=12, fraction=0.667)
        self.preset_0_750_btn = FractionButton(radius=12, fraction=0.75)
        self.preset_0_833_btn = FractionButton(radius=12, fraction=0.833)
        self.preset_1_000_btn = FractionButton(radius=12, fraction=1.0)
        
        self.preset_0_000_btn.clicked.connect(lambda: self.fraction_clicked(0.0))
        self.preset_0_167_btn.clicked.connect(lambda: self.fraction_clicked(0.167))
        self.preset_0_250_btn.clicked.connect(lambda: self.fraction_clicked(0.25))
        self.preset_0_333_btn.clicked.connect(lambda: self.fraction_clicked(0.3333))
        self.preset_0_500_btn.clicked.connect(lambda: self.fraction_clicked(0.5))
        self.preset_0_667_btn.clicked.connect(lambda: self.fraction_clicked(0.6667))
        self.preset_0_750_btn.clicked.connect(lambda: self.fraction_clicked(0.75))
        self.preset_0_833_btn.clicked.connect(lambda: self.fraction_clicked(0.833))
        self.preset_1_000_btn.clicked.connect(lambda: self.fraction_clicked(1.0))
        
        fraction_layout.addWidget(self.preset_0_000_btn)
        fraction_layout.addWidget(self.preset_0_167_btn)
        fraction_layout.addWidget(self.preset_0_250_btn)
        fraction_layout.addWidget(self.preset_0_333_btn)
        fraction_layout.addWidget(self.preset_0_500_btn)
        fraction_layout.addWidget(self.preset_0_667_btn)
        fraction_layout.addWidget(self.preset_0_750_btn)
        fraction_layout.addWidget(self.preset_0_833_btn)
        fraction_layout.addWidget(self.preset_1_000_btn)
        
        # combine layouts
        top_button_layout.addLayout(mode_layout)
        top_button_layout.addStretch()
        top_button_layout.addLayout(misc_button_layout)
        
        layout.addLayout(top_button_layout)
        layout.addLayout(fraction_layout)
        layout.addSpacerItem(QSpacerItem(1, 8, QSizePolicy.Maximum, QSizePolicy.MinimumExpanding))
        layout.addLayout(slider_layout)
        layout.addLayout(slider_label_layout)
        
        self.load_preferences()
        self.set_mode_button()
    
    def slider_pressed(self):
        slider_value = self.slider.value()
        
        blend = slider_value / 100.0
        
        self.interp_mode = self.mode_button_group.checkedButton().text()
        
        # only update when maya is idle to prevent multiple calls without seeing the result
        self.idle_callback = om.MEventMessage.addEventCallback('idle', self.slider_changed)
        
        # disable undo on first call, so we don't get 2 undos in queue
        # both press and release add to the same cache, so it should be safe
        cmds.undoInfo(stateWithoutFlush=False)
        cmds.tweener(t=blend, press=True, type=self.interp_mode)
        cmds.undoInfo(stateWithoutFlush=True)
        
        tween.interpolate(t=blend, t_type=self.interp_mode)
    
    def slider_changed(self, *args):
        slider_value = self.slider.value()
        
        if self.interp_mode == 'Between':
            self.slider_label.setText(str(int(slider_value * 0.5 + 50)))
        elif self.interp_mode in ['Towards', 'Curve', 'Default']:
            self.slider_label.setText(str(slider_value))
        
        blend = slider_value / 100.0
        tween.interpolate(t=blend, t_type=self.interp_mode)
    
    def slider_released(self):
        slider_value = self.slider.value()
        
        blend = slider_value / 100.0
        cmds.tweener(t=blend, press=False, type=self.interp_mode)
        
        self.slider.setValue(0)
        self.slider_label.setText('')
        
        om.MEventMessage.removeCallback(self.idle_callback)
    
    def fraction_clicked(self, value):
        value = value * 2.0 - 1.0
        
        # simulate slider press/release
        self.interp_mode = self.mode_button_group.checkedButton().text()
        cmds.undoInfo(stateWithoutFlush=False)
        cmds.tweener(t=value, press=True, type=self.interp_mode)
        cmds.undoInfo(stateWithoutFlush=True)
        cmds.tweener(t=value, press=False, type=self.interp_mode)
    
    def load_preferences(self):
        # set which mode button is checked
        if cmds.optionVar(exists='tweener_interp_type'):
            try:
                button = self.mode_button_group.button(int(cmds.optionVar(q='tweener_interp_type')))
                if button is not None:
                    button.setChecked(True)
            except Exception as e:
                sys.stdout.write('# %s\n' % e)
        
        # overshoot button checked state
        if cmds.optionVar(exists='tweener_overshoot'):
            try:
                self.overshoot_btn.setChecked(bool(cmds.optionVar(q='tweener_overshoot')))
            except Exception as e:
                self.overshoot_btn.setChecked(False)
                sys.stdout.write('# %s\n' % e)
        
        self.overshoot_button_clicked()  # simulate button click to setup slider values
    
    def set_mode_button(self):
        cmds.optionVar(iv=('tweener_interp_type', int(self.mode_button_group.checkedId())))
        self.interp_mode = self.mode_button_group.checkedButton().text()
        
        if self.interp_mode == 'Between':
            self.preset_0_000_btn.set_fraction(0.0, tooltip="0 %", visible=True)
            self.preset_0_167_btn.set_fraction(0.167, tooltip="17 %", visible=True)
            self.preset_0_250_btn.set_fraction(0.25, tooltip="25 %", visible=True)
            self.preset_0_333_btn.set_fraction(0.333, tooltip="33 %", visible=True)
            self.preset_0_500_btn.set_fraction(0.5, tooltip="50 %", visible=True)
            self.preset_0_667_btn.set_fraction(0.667, tooltip="67 %", visible=True)
            self.preset_0_750_btn.set_fraction(0.75, tooltip="75 %", visible=True)
            self.preset_0_833_btn.set_fraction(0.833, tooltip="83 %", visible=True)
            self.preset_1_000_btn.set_fraction(1.0, tooltip="100 %", visible=True)
        elif self.interp_mode in ['Towards', 'Curve', 'Default']:
            self.preset_0_000_btn.set_fraction(-1.0, tooltip="100 %", visible=True)
            self.preset_0_167_btn.set_fraction(-0.667, tooltip="67 %", visible=True)
            self.preset_0_250_btn.set_fraction(-0.5, tooltip="50 %", visible=True)
            self.preset_0_333_btn.set_fraction(-0.333, tooltip="33 %", visible=True)
            self.preset_0_500_btn.set_fraction(0.0, tooltip="0 %", visible=True)
            self.preset_0_667_btn.set_fraction(0.333, tooltip="33 %", visible=True)
            self.preset_0_750_btn.set_fraction(0.5, tooltip="50 %", visible=True)
            self.preset_0_833_btn.set_fraction(0.67, tooltip="67 %", visible=True)
            self.preset_1_000_btn.set_fraction(1.0, tooltip="100 %", visible=True)
    
    def overshoot_button_clicked(self):
        checked = self.overshoot_btn.isChecked()
        
        if checked:
            self.slider.setMinimum(-200)
            self.slider.setMaximum(200)
        else:
            self.slider.setMinimum(-100)
            self.slider.setMaximum(100)
        
        # save setting
        cmds.optionVar(iv=('tweener_overshoot', int(checked)))
    
    def keyhammer_button_clicked(self):
        cmds.keyHammer()
    
    @staticmethod
    def v_separator_layout():
        layout = QVBoxLayout()
        
        layout.addSpacerItem(QSpacerItem(8, 1, QSizePolicy.Fixed, QSizePolicy.Fixed))
        
        frame = QFrame()
        frame.setFrameShape(QFrame.VLine)
        frame.setFixedWidth(20)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(frame)
        
        layout.addSpacerItem(QSpacerItem(8, 1, QSizePolicy.Fixed, QSizePolicy.Fixed))
        
        return layout


def TweenerUIScript(restore=False):
    global tweener_window
    
    if restore:
        restored_control = omui.MQtUtil.getCurrentPanel()
    
    if tweener_window is None:
        tweener_window = TweenerUI()
        tweener_window.setObjectName("tweenerUIWindow")
    
    if restore:
        mixin_ptr = omui.MQtUtil.findControl(tweener_window.objectName())
        omui.MQtUtil.addWidgetToMayaLayout(long(mixin_ptr), long(restored_control))
    else:
        tweener_window.show(dockable=True, retain=False, uiScript="TweenerUIScript(restore=True)")
    
    return tweener_window


class ModeButton(QPushButton):
    def __init__(self, label='', icon=None, is_checkable=True):
        super(ModeButton, self).__init__(label)
        
        self.setMinimumSize(65, 20)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.setCheckable(is_checkable)
        
        if icon:
            self.setFixedSize(40, 20)
            self.setContentsMargins(0, 0, 0, 0)
            path = g.plugin_path + icon
            qicon = QIcon(path)
            self.setIconSize(QSize(20, 20))  # icons are designed to fit 16x16 but with 2px padding
            self.setIcon(qicon)


class FractionButton(QPushButton):
    def __init__(self, radius, fraction):
        super(FractionButton, self).__init__()
        
        self.fraction = 0
        self.angle = 0
        self.set_fraction(fraction)  # also sets angle
        
        stroke_w = 2
        self.padding_y = 3
        self.padding_x = 3
        self.pie_rect_size = radius + stroke_w
        self.rect = QRect(self.padding_x, self.padding_y + stroke_w, self.pie_rect_size, self.pie_rect_size)
        
        # self.setFixedWidth(radius + self.padding_x * 2 + stroke_w)
        self.setFixedHeight(radius + 3 * stroke_w + self.padding_y * 2)
        # self.setFixedSize(radius + self.padding_x * 2 + stroke_w, radius + 3 * stroke_w + self.padding_y * 2)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        self.stroke_color = QColor(0, 0, 0)
        self.stroke_color.setNamedColor('#BDBDBD')  # light gray
        self.dark_color = QColor(0, 0, 0)
        self.dark_color.setNamedColor('#2B2B2B')  # dark gray
        self.teal_color = QColor(0, 0, 0)
        self.teal_color.setNamedColor('#DF6E41')  # maya orange
    
    def paintEvent(self, event):
        # draw the normal button
        super(FractionButton, self).paintEvent(event)
        
        # init painter
        painter = QPainter(self)
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        x = (self.geometry().width() - (self.padding_x * 2 + self.pie_rect_size)) / 2
        painter.translate(x, 0)
        
        # dark area
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.dark_color)
        painter.drawPie(self.rect, (self.angle - 90.0) * -16, (360 - self.angle) * -16)
        
        # light area
        painter.setBrush(self.teal_color)
        painter.drawPie(self.rect, 90.0 * 16, self.angle * -16)
        
        # stroke
        painter.setPen(QPen(self.stroke_color, 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(self.rect)
        
        painter.end()
    
    def set_fraction(self, fraction, tooltip="", visible=True):
        self.fraction = fraction
        self.angle = fraction * 360
        
        self.setToolTip(tooltip)
        
        if visible:
            self.update()
