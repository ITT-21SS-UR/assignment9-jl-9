import os.path

from pyqtgraph.Qt import QtGui, QtCore, QtWidgets


class AbstractActionWidget(QtGui.QWidget):

    ACTION_FILE = "file"
    ACTION_SCRIPT = "script"
    ACTION_URL = "url"

    def __init__(self):
        super().__init__()
        self.action = None
        self.value = None

    def is_valid(self):
        """
        Returns True if input is valid
        Shows a message box and returns False if input is empty
        """
        if self.value is None or len(self.value.strip()) == 0:
            self.show_warning()
            return False

        return True

    def show_warning(self):
        message_box = QtGui.QMessageBox()
        message_box.setText("Please enter a valid action value!")
        message_box.setWindowTitle("Warning - Empty value")
        message_box.setIcon(QtGui.QMessageBox.Warning)
        message_box.exec_()


class OpenFileWidget(AbstractActionWidget):

    selected_files = None

    def __init__(self):
        super().__init__()
        self.layout = QtGui.QHBoxLayout()

        self.label = QtGui.QLabel("Open File: ")
        self.button = QtGui.QPushButton("Open...")
        self.filename = QtGui.QLineEdit()
        self.filename.textChanged.connect(self.on_text_changed)

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

    def on_text_changed(self):
        self.value = self.filename.text()

    def is_valid(self):
        """
        Custom implementation to check whether the specified file exists or not
        """
        if self.value is not None and os.path.exists(self.value):
            return True

        else:
            self.show_warning()
            return False


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


class OpenUrlWidget(AbstractActionWidget):

    def __init__(self):
        super().__init__()
        self.layout = QtGui.QHBoxLayout()

        self.label = QtGui.QLabel("Open an URL: ")
        self.input = QtGui.QLineEdit()
        self.input.setPlaceholderText("https://elearning.ur.de/")
        self.input.textChanged.connect(self.on_text_changed)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.input)

        self.setLayout(self.layout)
        self.action = self.ACTION_URL

    def on_text_changed(self):
        self.value = self.input.text()


# class VolumeActionWidget(AbstractActionWidget):
#     """
#     Didn't end up using this since it's not working on linux
#     Press F
#     """
#
#     def __init__(self):
#         super().__init__()
#         self.layout = QtGui.QHBoxLayout()
#
#         self.label = QtGui.QLabel("Adjust Volume to: ")
#         self.input = QtGui.QLineEdit()
#         self.input.setPlaceholderText("0 - 100")
#         self.input.textChanged.connect(self.on_text_changed)
#         self.input.setValidator(QtGui.QIntValidator(0, 100))
#
#         self.layout.addWidget(self.label)
#         self.layout.addWidget(self.input)
#
#         self.setLayout(self.layout)
#         self.action = self.ACTION_VOLUME
#
#     def on_text_changed(self):
#         self.value = self.input.text()