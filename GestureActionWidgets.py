import PyQt5.Qt
import numpy.fft
from pyqtgraph.flowchart import Flowchart, Node
from pyqtgraph.flowchart.library.common import CtrlNode
import pyqtgraph.flowchart.library as fclib
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
from enum import Enum
from PyQt5 import uic
import numpy as np
from sklearn import svm
from sklearn.exceptions import NotFittedError
from scipy import signal
from DIPPID import SensorUDP, SensorSerial, SensorWiimote
from DIPPID_pyqtnode import BufferNode, DIPPIDNode
from recognizer import Recognizer
import sys


class AbstractActionWidget(QtGui.QWidget):

    ACTION_VOLUME = "volume"
    ACTION_FILE = "file"
    ACTION_SCRIPT = "script"

    def __init__(self):
        super().__init__()
        self.action = None
        self.value = None


class VolumeActionWidget(AbstractActionWidget):

    def __init__(self):
        super().__init__()
        self.layout = QtGui.QHBoxLayout()

        self.label = QtGui.QLabel("Adjust Volume to: ")
        self.input = QtGui.QLineEdit()
        self.input.setPlaceholderText("0 - 100")
        self.input.textChanged.connect(self.on_text_changed)
        self.input.setValidator(QtGui.QIntValidator(0, 100))

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.input)

        self.setLayout(self.layout)
        self.action = self.ACTION_VOLUME

    def on_text_changed(self):
        self.value = self.input.text()


class OpenFileWidget(AbstractActionWidget):

    selected_files = None

    def __init__(self):
        super().__init__()
        self.layout = QtGui.QHBoxLayout()

        self.label = QtGui.QLabel("Open File: ")
        self.button = QtGui.QPushButton("Open...")
        self.filename = QtGui.QLineEdit()

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.filename)

        self.button.clicked.connect(self.show_file_dialog)

        self.setLayout(self.layout)
        self.action = self.ACTION_FILE

    def show_file_dialog(self):
        file_dialog = QtGui.QFileDialog()
        file_dialog.show()

        if file_dialog.exec_():
            self.filename.setText(file_dialog.selectedFiles()[0])
            self.selected_files = file_dialog.selectedFiles()[0]
            self.value = file_dialog.selectedFiles()[0]


class ExecuteScriptWidget(AbstractActionWidget):

    def __init__(self):
        super().__init__()
        self.layout = QtGui.QHBoxLayout()

        self.label = QtGui.QLabel("Execute Script: ")
        self.input = QtGui.QPlainTextEdit()
        self.input.setPlaceholderText("Your shell script here...")
        self.input.textChanged.connect(self.on_text_changed)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.input)

        self.setLayout(self.layout)
        self.action = self.ACTION_SCRIPT

    def on_text_changed(self):
        self.value = self.input.toPlainText()
