
import os
import subprocess
import webbrowser
import platform
from PyQt5 import uic
import numpy as np
from GestureActionWidgets import *
from subprocess import Popen
from recognizer import Recognizer
import sys


class GestureTemplate:
    def __init__(self, name, points):
        super(GestureTemplate, self).__init__()
        self.name = name
        self.points = points


class RecognizedGestureDisplayWidget(QtGui.QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QtGui.QVBoxLayout()

        self.header = QtGui.QLabel("Last recognized Gesture:")
        self.gesture_name_label = QtGui.QLabel("---")
        self.gesture_match_label = QtGui.QLabel("---")

        self.layout.addWidget(self.header)
        self.layout.addWidget(self.gesture_name_label)
        self.layout.addWidget(self.gesture_match_label)

        self.setLayout(self.layout)

    def set_gesture_name(self, name):
        self.gesture_name_label.setText(name)

    def set_match(self, match):
        self.gesture_match_label.setText(str(match) + "% match")


class DrawWidget(QtGui.QWidget):

    background_color = None
    line_color = None

    gesture_drawn = QtCore.pyqtSignal(list)

    def __init__(self, width=500, height=500):
        super().__init__()
        self.resize(width, height)
        self.is_painting = False
        self.painter_path = None
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.points = []
        self.setMinimumSize(50, 350)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.points.clear()
            self.painter_path = QtGui.QPainterPath()
            self.painter_path.moveTo(event.localPos())
            self.is_painting = True

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_painting = False
            self.gesture_drawn.emit(self.points)

    def mouseMoveEvent(self, event):
        if self.is_painting:
            current_point = event.localPos()
            self.points.append(current_point)

            # if self.point_is_in_painting_area(current_point):
            self.painter_path.lineTo(current_point)

            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)

        painter.setBrush(self.background_color if self.background_color is not None else QtCore.Qt.gray)
        painter.drawRect(event.rect())
        painter.setBrush(QtCore.Qt.NoBrush)

        if self.painter_path is not None:
            color = self.line_color if self.line_color is not None else QtCore.Qt.red
            painter.setPen(QtGui.QPen(color, 1, QtCore.Qt.SolidLine, QtCore.Qt.FlatCap,
                                      QtCore.Qt.MiterJoin))

            painter.drawPath(self.painter_path)

    def point_is_in_painting_area(self, point):
        inner_rect = self.rect()
        rect = QtCore.QRect(self.x(), self.y(), inner_rect.width(), inner_rect.height())
        if point.x() < rect.left() or point.x() > rect.right():
            return False

        if point.y() < rect.top() or point.y() > rect.bottom():
            return False

        return True

    def set_line_color(self, color):
        self.line_color = color

    def set_background_color(self, color):
        self.background_color = color

    def set_points(self, points):
        self.points = points.copy()
        self.painter_path = QtGui.QPainterPath()

        for i in range(0, len(points)):
            if i == 0:
                self.painter_path.moveTo(points[0].x(), points[0].y())
            else:
                self.painter_path.lineTo(points[i].x(), points[i].y())

        self.update()


class SetGestureActionWindow(QtGui.QWidget):

    confirmed = QtCore.pyqtSignal(list)

    def __init__(self, gesture_id):
        super().__init__()
        uic.loadUi("action_widget_ui.ui", self)
        self.gesture_id = gesture_id
        self.fileButton.setChecked(True)
        self.last_button = self.fileButton

        self.fileButton.clicked.connect(lambda: self.on_radio_button_clicked(self.fileButton))
        self.scriptButton.clicked.connect(lambda: self.on_radio_button_clicked(self.scriptButton))
        self.linkButton.clicked.connect(lambda: self.on_radio_button_clicked(self.linkButton))

        self.settings_widget = OpenFileWidget()
        self.widgetLayout.addWidget(self.settings_widget)

        self.confirmButton.clicked.connect(self.on_confirm_clicked)
        self.cancelButton.clicked.connect(lambda: self.close())

    def on_radio_button_clicked(self, button):

        self.widgetLayout.removeWidget(self.settings_widget)

        if button is self.fileButton and self.last_button is not self.fileButton:
            self.settings_widget = OpenFileWidget()
            self.last_button = self.fileButton

        elif button is self.scriptButton and self.last_button is not self.scriptButton:
            self.settings_widget = ExecuteScriptWidget()
            self.last_button = self.scriptButton

        elif button is self.linkButton and self.last_button is not self.linkButton:
            self.settings_widget = OpenUrlWidget()
            self.last_button = self.linkButton

        self.widgetLayout.addWidget(self.settings_widget)

    def on_confirm_clicked(self):
        if self.settings_widget.is_valid():
            self.confirmed.emit([self.gesture_id, (self.settings_widget.action, self.settings_widget.value)])
            self.close()


class AddGestureWindow(QtGui.QWidget):

    GESTURE_NAME = "name"
    GESTURE_POINTS = "points"
    GESTURE_ID = "id"

    is_painting = False
    lines = []
    painter_path = None
    return_dict = {}

    confirm_pressed = QtCore.pyqtSignal(dict)

    def __init__(self, gesture_id):
        super().__init__()
        uic.loadUi("add_gesture_widget.ui", self)
        self.gesture_id = gesture_id
        self._init_draw_widget()
        self.confirmButton.clicked.connect(self.handle_confirm_clicked)
        self.cancelButton.clicked.connect(lambda: self.close())

    def _init_draw_widget(self):
        self.draw_widget = DrawWidget()
        self.drawLayout.addWidget(self.draw_widget)

    def handle_confirm_clicked(self):
        if len(self.gestureNameInput.text().strip()) == 0:
            self.gestureNameInput.setStyleSheet("border: 1px solid red")
            return

        if len(self.draw_widget.points) <= 0:
            message_box = QtGui.QMessageBox()
            message_box.setText("Please draw a gesture!")
            message_box.setWindowTitle("Warning - No Gesture")
            message_box.setIcon(QtGui.QMessageBox.Warning)
            message_box.exec_()
            return

        self.return_dict[self.GESTURE_NAME] = self.gestureNameInput.text()
        self.return_dict[self.GESTURE_POINTS] = self.draw_widget.points.copy()
        self.return_dict[self.GESTURE_ID] = self.gesture_id

        self.confirm_pressed.emit(self.return_dict)
        self.close()

    def set_gesture_name(self, name):
        self.gestureNameInput.setText(name)


class GestureListItem(QtGui.QWidget):

    def __init__(self, parent=None):
        super(GestureListItem, self).__init__(parent)
        self.label = QtGui.QLabel("ee")
        self.button = QtGui.QPushButton()
        self.init_ui()
        self.show()

    def init_ui(self):
        item_layout = QtGui.QHBoxLayout()

        item_layout.addWidget(self.label)
        item_layout.addWidget(self.button)

        self.setLayout(item_layout)

    def set_label_text(self, text):
        self.label.setText(text)

    def set_button_text(self, text):
        self.button.setText(text)

    def set_button_icon(self, icon):
        self.button.setIcon(icon)

    def get_label_text(self):
        return self.label.text()


class ShapeRecognitionNode(QtGui.QWidget):

    GESTURE_NAME = "name"
    GESTURE_POINTS = "points"
    GESTURE_ACTION = "action"

    draw_gesture_window = ()
    gestures = {}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouse Gesture Recognizer")
        self.gesture_id_counter = 0
        self.gesture_action_window = ()
        self._init_ui()
        self.recognizer = Recognizer()
        self.setMinimumSize(500, 700)

    def _init_ui(self):

        self.main_layout = QtGui.QVBoxLayout()
        self.button_layout = QtGui.QGridLayout()
        self.gesture_list = QtGui.QListWidget()
        self.train_help_label = QtGui.QLabel()
        self.draw_widget = DrawWidget()
        self.draw_widget.gesture_drawn.connect(self.on_gesture_drawn)
        self.recognized_gesture_widget = RecognizedGestureDisplayWidget()

        self._init_buttons()
        self._init_confirm_window()

        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.edit_button)
        self.button_layout.addWidget(self.delete_button)

        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.gesture_list)
        self.main_layout.addWidget(self.draw_widget)
        self.main_layout.addWidget(self.recognized_gesture_widget)

        self.setLayout(self.main_layout)

    def _init_buttons(self):
        self.add_button = QtGui.QPushButton("Add Gesture")
        self.edit_button = QtGui.QPushButton("Edit Gesture")
        self.delete_button = QtGui.QPushButton("Delete Gesture")

        self.add_button.clicked.connect(self._on_add_button_clicked)
        self.edit_button.clicked.connect(self._on_edit_button_clicked)
        self.delete_button.clicked.connect(self._on_delete_button_clicked)

    def _init_confirm_window(self):
        self.confirm_window_delete_gesture = uic.loadUi("confirm_action_ui.ui")
        self.confirm_window_delete_gesture.confirmButton.clicked.connect(self.delete_selected_gesture)
        self.confirm_window_delete_gesture.cancelButton.clicked.connect(lambda:
                                                                        self.confirm_window_delete_gesture.close())

    def _on_add_button_clicked(self):
        self.draw_gesture_window = AddGestureWindow(self.gesture_id_counter)
        self.draw_gesture_window.setMouseTracking(True)
        self.draw_gesture_window.show()
        self.draw_gesture_window.confirm_pressed.connect(lambda e: self.on_new_gesture_added(dict(e)))

    def _on_edit_button_clicked(self):
        if self.gesture_list.currentItem() is None:
            return

        self.draw_gesture_window = AddGestureWindow(self.gesture_list.currentItem().identifier)
        self.draw_gesture_window.confirmButton.setText("Confirm")
        self.draw_gesture_window.setMouseTracking(True)
        self.draw_gesture_window.show()
        self.draw_gesture_window.confirm_pressed.connect(lambda e: self.on_gesture_edited(dict(e)))

        self.draw_gesture_window\
            .set_gesture_name(self.gestures[self.gesture_list.currentItem().identifier][self.GESTURE_NAME])
        self.draw_gesture_window.draw_widget\
            .set_points(self.gestures[self.gesture_list.currentItem().identifier][self.GESTURE_POINTS])

    def _on_delete_button_clicked(self):
        if self.confirm_window_delete_gesture is None:
            self.confirm_window_delete_gesture = uic.loadUi("confirm_action_ui.ui")

        if self.gesture_list.currentItem() is None:
            return

        self.confirm_window_delete_gesture.show()

    def on_gesture_edited(self, e):
        self.gestures[e[AddGestureWindow.GESTURE_ID]][self.GESTURE_NAME] = e[AddGestureWindow.GESTURE_NAME]
        self.gestures[e[AddGestureWindow.GESTURE_ID]][self.GESTURE_POINTS] = e[AddGestureWindow.GESTURE_POINTS]

        point_list = []
        for point in e[AddGestureWindow.GESTURE_POINTS]:
            point_list.append([point.x(), point.y()])

        template = GestureTemplate(e[AddGestureWindow.GESTURE_ID], point_list)
        self.recognizer.addTemplate(template, e[AddGestureWindow.GESTURE_ID])

        self.gesture_list.itemWidget(self.gesture_list.currentItem()).set_label_text(e[AddGestureWindow.GESTURE_NAME])

    def delete_selected_gesture(self):
        self.gestures.pop(self.gesture_list.currentItem().identifier, None)
        self.recognizer.removeTemplate(self.gesture_list.currentItem().identifier)
        row = self.gesture_list.currentRow()
        self.gesture_list.takeItem(row)
        self.confirm_window_delete_gesture.close()

    def on_new_gesture_added(self, e):
        self.gestures[e[AddGestureWindow.GESTURE_ID]] = {}
        self.gestures[e[AddGestureWindow.GESTURE_ID]][self.GESTURE_NAME] = e[AddGestureWindow.GESTURE_NAME]
        self.gestures[e[AddGestureWindow.GESTURE_ID]][self.GESTURE_POINTS] = e[AddGestureWindow.GESTURE_POINTS]
        self.gestures[e[AddGestureWindow.GESTURE_ID]][self.GESTURE_ACTION] = None

        self.add_gesture_to_list(e[AddGestureWindow.GESTURE_ID], e[AddGestureWindow.GESTURE_NAME])

        point_list = []
        for point in e[AddGestureWindow.GESTURE_POINTS]:
            point_list.append([point.x(), point.y()])

        template = GestureTemplate(e[AddGestureWindow.GESTURE_ID], point_list)
        self.recognizer.addTemplate(template, e[AddGestureWindow.GESTURE_ID])
        self.gesture_id_counter += 1

    def add_gesture_to_list(self, gesture_id, name):
        my_list_widget = GestureListItem()
        my_list_widget.set_label_text(name)
        my_list_widget.set_button_text(" Edit Gesture Action")

        # edit icon from flaticon.com, by Kiranshastry - Free for personal and commercial purpose with attribution link:
        # https://www.flaticon.com/free-icon/edit_1159633?term=edit&page=1&position=2&page=1&position=2&related_id=
        # 1159633&origin=tag
        my_list_widget.set_button_icon(QtGui.QIcon('edit.png'))

        list_item = QtGui.QListWidgetItem(self.gesture_list)
        list_item.setSizeHint(my_list_widget.sizeHint())
        list_item.identifier = gesture_id
        self.gesture_list.addItem(list_item)
        self.gesture_list.setItemWidget(list_item, my_list_widget)
        self.gesture_list.setCurrentItem(list_item)

        my_list_widget.button.clicked.connect(lambda: self.on_set_gesture_action_clicked(list_item.identifier))

    def on_gesture_drawn(self, points):
        points_as_list = []
        for point in points:
            points_as_list.append([point.x(), point.y()])

        matched_template, score = self.recognizer.recognize(points_as_list)

        if matched_template is None or score is None:
            return

        score = round(score * 100, 2)
        self.recognized_gesture_widget.set_gesture_name(self.gestures[matched_template.name][self.GESTURE_NAME])
        self.recognized_gesture_widget.set_match(score)

        self.perform_gesture_action(matched_template.name)

    def perform_gesture_action(self, gesture_id):
        gesture = self.gestures[gesture_id]

        if gesture[self.GESTURE_ACTION] is None:
            return

        elif gesture[self.GESTURE_ACTION][0] is AbstractActionWidget.ACTION_FILE:
            path = gesture[self.GESTURE_ACTION][1]
            print(os.path.abspath(gesture[self.GESTURE_ACTION][1]))

            if platform.system() == 'Windows':
                os.startfile(path)
            else:
                subprocess.run(['open', path], check=True)

        elif gesture[self.GESTURE_ACTION][0] is AbstractActionWidget.ACTION_SCRIPT:
            script = gesture[self.GESTURE_ACTION][1]
            Popen(['sh', "-c", script])

        elif gesture[self.GESTURE_ACTION][0] is AbstractActionWidget.ACTION_URL:
            webbrowser.open(gesture[self.GESTURE_ACTION][1], new=2)

    def on_set_gesture_action_clicked(self, gesture_id):
        self.gesture_action_window = SetGestureActionWindow(gesture_id)
        self.gesture_action_window.show()
        self.gesture_action_window.confirmed.connect(lambda e: self.on_gesture_action_set(e))

    def on_gesture_action_set(self, action_list):
        """
        Called when a gesture action has been set and confirmed
        action_list is a list of length two
        Index 0 is the id of the gesture
        Index 1 is a tuple of ((int) Action Type, (Str) Action Parameter)
        """

        self.gestures[action_list[0]][self.GESTURE_ACTION] = action_list[1]


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = ShapeRecognitionNode()
    widget.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        sys.exit(QtGui.QApplication.instance().exec_())
