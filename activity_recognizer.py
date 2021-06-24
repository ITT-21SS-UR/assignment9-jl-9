import numpy.fft
from pyqtgraph.flowchart import Flowchart, Node
from pyqtgraph.flowchart.library.common import CtrlNode
import pyqtgraph.flowchart.library as fclib
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from enum import Enum
from PyQt5 import uic
import numpy as np
from sklearn import svm
from sklearn.exceptions import NotFittedError
from scipy import signal
from DIPPID import SensorUDP, SensorSerial, SensorWiimote
from DIPPID_pyqtnode import BufferNode, DIPPIDNode
import sys


class DrawWidget(QtGui.QWidget):

    GESTURE_NAME = "name"
    GESTURE_POINTS = "points"

    is_painting = False
    points = []
    lines = []
    painter_path = None
    return_dict = {}

    confirm_pressed = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        uic.loadUi("draw_widget_ui.ui", self)
        self.setMouseTracking(True)
        self.drawBox.mousePressEvent = self.box_mouse_press_event
        self.drawBox.mouseReleaseEvent = self.box_mouse_release_event
        self.drawBox.mouseMoveEvent = self.box_mouse_move_event
        self.confirmButton.clicked.connect(self.handle_confirm_clicked)

    def box_mouse_press_event(self, event):
        self.points.clear()
        self.is_painting = True

    def box_mouse_release_event(self, event):
        self.is_painting = False
        print(self.points)

        self.painter_path = QtGui.QPainterPath()
        for x in range(0, len(self.points)):
            if x == 0:
                self.painter_path.moveTo(self.points[0])

            else:
                if self.point_is_in_painting_area(self.points[x]):
                    self.painter_path.lineTo(self.points[x])

        self.update()

    def point_is_in_painting_area(self, point):
        inner_rect = self.drawBox.rect()
        rect = QtCore.QRect(self.drawBox.x(), self.drawBox.y(), inner_rect.width(), inner_rect.height())
        if point.x() < rect.left() or point.x() > rect.right():
            return False

        if point.y() < rect.top() or point.y() > rect.bottom():
            return False

        return True

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.painter_path is not None:
            painter = QtGui.QPainter(self)
            painter.setPen(QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.SolidLine, QtCore.Qt.FlatCap,
                                      QtCore.Qt.MiterJoin))

            painter.drawPath(self.painter_path)

    def box_mouse_move_event(self, event):
        if self.is_painting:
            self.points.append(event.windowPos())

    def handle_confirm_clicked(self):
        if len(self.gestureNameInput.text().strip()) == 0:
            self.gestureNameInput.setStyleSheet("border: 1px solid red")
            return

        self.return_dict[self.GESTURE_NAME] = self.gestureNameInput.text()
        self.return_dict[self.GESTURE_POINTS] = self.points.copy()

        self.confirm_pressed.emit(self.return_dict)
        self.close()


class ShapeRecognitionNode(Node):

    OUTPUT = "output"

    nodeName = "ShapeRecognition"

    draw_gesture_window = ()
    gestures = []

    def __init__(self, name):
        terminals = {
            self.OUTPUT: dict(io='out')
        }

        self._init_ui()

        Node.__init__(self, name, terminals=terminals)

    def _init_ui(self):

        # self.ui = uic.loadUi("draw_widget_ui.ui")
        # self.ui.setMinimumHeight(300)
        # self.ui.drawBox.setFocusPolicy(QtCore.Qt.NoFocus)

        self.ui = QtGui.QWidget()
        self.main_layout = QtGui.QVBoxLayout()
        self.button_layout = QtGui.QGridLayout()
        self.train_layout = QtGui.QHBoxLayout()
        self.gesture_list = QtGui.QListWidget()
        self.train_help_label = QtGui.QLabel()

        self._init_buttons()
        self._init_radio_buttons()

        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.edit_button)
        self.button_layout.addWidget(self.delete_button)

        self.train_layout.addWidget(self.train_button)
        self.train_layout.addWidget(self.predict_button)
        self.train_layout.addWidget(self.idle_button)

        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addLayout(self.train_layout)
        self.main_layout.addWidget(self.train_help_label)
        self.main_layout.addWidget(self.gesture_list)

        self.ui.setLayout(self.main_layout)

    def _init_buttons(self):
        self.add_button = QtGui.QPushButton("Add Gesture")
        self.edit_button = QtGui.QPushButton("Edit Gesture")
        self.delete_button = QtGui.QPushButton("Delete Gesture")

        self.add_button.clicked.connect(self._on_add_button_clicked)
        self.edit_button.clicked.connect(self._on_edit_button_clicked)
        self.delete_button.clicked.connect(self._on_delete_button_clicked)

    def _init_radio_buttons(self):
        self.train_button = QtGui.QRadioButton("Train")
        self.predict_button = QtGui.QRadioButton("Predict")
        self.idle_button = QtGui.QRadioButton("Idle")

        # self.train_button.clicked.connect(lambda: self.on_radio_button_clicked(self.train_button))
        # self.predict_button.clicked.connect(lambda: self.on_radio_button_clicked(self.predict_button))
        # self.idle_button.clicked.connect(lambda: self.on_radio_button_clicked(self.idle_button))

        self.idle_button.setChecked(True)

    def _on_add_button_clicked(self):
        self.draw_gesture_window = DrawWidget()
        self.draw_gesture_window.setMouseTracking(True)
        self.draw_gesture_window.show()
        self.draw_gesture_window.confirm_pressed.connect(lambda e: self.on_new_gesture_added(dict(e)))

    def _on_edit_button_clicked(self):
        # TODO implement
        pass

    def _on_delete_button_clicked(self):
        # TODO implement
        pass

    def on_new_gesture_added(self, e):
        self.gestures.append(e)
        self.gesture_list.addItem(e[DrawWidget.GESTURE_NAME])

    def ctrlWidget(self):
        return self.ui



fclib.registerNodeType(ShapeRecognitionNode, [('Assignment 9',)])

if __name__ == '__main__':
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    win.setWindowTitle('DIPPIDNode demo')
    win.resize(800, 650)
    cw = QtGui.QWidget()
    win.setCentralWidget(cw)
    layout = QtGui.QGridLayout()
    cw.setLayout(layout)

    BUFFER_NODE_SIZE = 32

    # Create an empty flowchart with a single input and output
    fc = Flowchart(terminals={})
    layout.addWidget(fc.widget(), 0, 0, 2, 1)

    shape_node = fc.createNode('ShapeRecognition', pos=(200, -50))

    win.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        sys.exit(QtGui.QApplication.instance().exec_())
