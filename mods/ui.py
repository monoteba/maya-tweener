"""
ui module
"""
import globals as g
import tween

import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import sys
import os

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# PySide2 is for Maya 2017+
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from shiboken2 import wrapInstance

lazytween_window = None


def get_main_maya_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(ptr), QMainWindow)


def show():
    global lazytween_window
    if lazytween_window is None:
        lazytween_window = LazyTweenUI(parent=get_main_maya_window())
    
    lazytween_window.show(dockable=True)  # show the window
    lazytween_window.raise_()  # raise it on top of others
    lazytween_window.activateWindow()  # set focus to it


def delete():
    global lazytween_window
    if lazytween_window is not None:
        lazytween_window.deleteLater()
        lazytween_window = None


class LazyTweenUI(MayaQWidgetDockableMixin, QMainWindow):
    def __init__(self, parent=None):
        super(LazyTweenUI, self).__init__(parent=parent)
        
        # self.window_name = 'LazyTweenUIObj'
        
        # set slider window properties
        self.setWindowTitle('LazyTween')
        # self.setObjectName(self.window_name)
        
        if os.name == 'nt':  # windows platform
            self.setWindowFlags(Qt.Window)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        self.setProperty("saveWindowPref", True)  # maya's automatic window management
        
        # variables
        self.idle_callback = None
        
        # define window dimensions
        self.setMinimumWidth(330)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        # style
        self.setStyleSheet(
            'QLineEdit { padding: 0 3px; border-radius: 2px; }'
            'QLineEdit:disabled { color: rgb(128, 128, 128); background-color: rgb(64, 64, 64); }'
            'QLabel:disabled { background-color: none; }'
            'QPushButton { padding: 0; border-radius: 0px; background-color: rgb(93, 93, 93); }'
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
        self.interp_mode = 'between'
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(2)
        mode_between_btn = ModeButton('between')
        mode_towards_btn = ModeButton('towards')
        mode_curve_tangent_btn = ModeButton('curve')
        mode_default_btn = ModeButton('default')
        
        mode_between_btn.clicked.connect(self.save_mode_button)
        mode_between_btn.setChecked(True)
        mode_towards_btn.clicked.connect(self.save_mode_button)
        mode_curve_tangent_btn.clicked.connect(self.save_mode_button)
        mode_default_btn.clicked.connect(self.save_mode_button)
        
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
        self.overshoot_btn.setToolTip('Overshoot')
        
        misc_button_layout.addWidget(self.overshoot_btn)
        
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
        
        self.slider_label = QLabel(str(self.slider.value()))
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
        
        zero_btn = Pie(radius=12, angle=0.0)
        quater_btn = Pie(radius=12, angle=0.25 * 360)
        third_btn = Pie(radius=12, angle=0.333 * 360)
        half_btn = Pie(radius=12, angle=0.5 * 360)
        two_thirds_btn = Pie(radius=12, angle=0.667 * 360)
        three_quarters_btn = Pie(radius=12, angle=0.75 * 360)
        full_btn = Pie(radius=12, angle=360.0)
        
        zero_btn.clicked.connect(lambda: self.fraction_clicked(0.0))
        quater_btn.clicked.connect(lambda: self.fraction_clicked(0.25))
        third_btn.clicked.connect(lambda: self.fraction_clicked(0.3333))
        half_btn.clicked.connect(lambda: self.fraction_clicked(0.5))
        two_thirds_btn.clicked.connect(lambda: self.fraction_clicked(0.6667))
        three_quarters_btn.clicked.connect(lambda: self.fraction_clicked(0.75))
        full_btn.clicked.connect(lambda: self.fraction_clicked(1.0))
        
        fraction_layout.addWidget(zero_btn)
        fraction_layout.addWidget(quater_btn)
        fraction_layout.addWidget(third_btn)
        fraction_layout.addWidget(half_btn)
        fraction_layout.addWidget(two_thirds_btn)
        fraction_layout.addWidget(three_quarters_btn)
        fraction_layout.addWidget(full_btn)
        
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
        self.slider_label.setText(str(slider_value))
        
        blend = slider_value / 100.0
        tween.interpolate(t=blend, t_type=self.interp_mode)
    
    def slider_released(self):
        slider_value = self.slider.value()
        
        blend = slider_value / 100.0
        cmds.tweener(t=blend, press=False, type=self.interp_mode)
        
        self.slider.setValue(0)
        self.slider_label.setText('0')
        
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
        if cmds.optionVar(exists='lazytween_interp_type'):
            try:
                button = self.mode_button_group.button(int(cmds.optionVar(q='lazytween_interp_type')))
                if button is not None:
                    button.setChecked(True)
            except Exception as e:
                sys.stdout.write('# %s\n' % e)
        
        # overshoot button checked state
        if cmds.optionVar(exists='lazytween_overshoot'):
            try:
                self.overshoot_btn.setChecked(bool(cmds.optionVar(q='lazytween_overshoot')))
            except Exception as e:
                self.overshoot_btn.setChecked(False)
                sys.stdout.write('# %s\n' % e)
        
        self.overshoot_button_clicked()  # simulate button click to setup slider values
    
    def save_mode_button(self):
        cmds.optionVar(iv=('lazytween_interp_type', int(self.mode_button_group.checkedId())))
    
    def overshoot_button_clicked(self):
        checked = self.overshoot_btn.isChecked()
        
        if checked:
            self.slider.setMinimum(-200)
            self.slider.setMaximum(200)
        else:
            self.slider.setMinimum(-100)
            self.slider.setMaximum(100)
        
        # save setting
        cmds.optionVar(iv=('lazytween_overshoot', int(checked)))
    
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


class ModeButton(QPushButton):
    def __init__(self, label='', icon=None):
        super(ModeButton, self).__init__(label)
        
        self.setMinimumSize(65, 20)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.setCheckable(True)
        
        if icon:
            self.setFixedSize(40, 20)
            path = g.plugin_path + icon
            self.setIcon(QIcon(path))


class Pie(QPushButton):
    def __init__(self, radius, angle):
        super(Pie, self).__init__()
        
        stroke_w = 2
        self.padding_y = 3
        self.padding_x = 14
        self.angle = angle
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
        super(Pie, self).paintEvent(event)
        
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
