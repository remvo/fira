#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import sys

import cv2
from PyQt5 import uic
from PyQt5.QtCore import QTimer, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QWidget

import widget
from threads import CameraThread, SerialThread
from utils import get_serial_port_list, save_value, load_value, resize_image

mainFormClassFile = 'design/mainwindow.ui'
main_form_class = uic.loadUiType(mainFormClassFile)[0]

logging_config = {
    'console': {
        'format': '[%(asctime)-15s][%(levelname)s] %(threadName)s %(message)s',
        'level': logging.DEBUG
    },
    'widget': {
        'format': '[%(asctime)-15s] %(message)s',
        'level': logging.INFO
    }
}


class ImageWidget(QWidget):
    """이미지 출력을 위한 위젯"""

    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.image = None
        self.pressed = False
        self.pressed_point = None
        self.current_point = None

    def set_image(self, image):
        """
        출력을 위한 이미지 설정
        :param image: QImage 객체
        :return: None
        """
        self.image = image
        sz = image.size()
        self.setMinimumSize(sz)
        self.update()

    def mouse_press(self, point):
        self.pressed = True
        self.pressed_point = point
        self.setMouseTracking(True)

    def mouse_release(self):
        self.pressed = False
        self.pressed_point = None
        self.current_point = None
        self.setMouseTracking(False)

    def mouseMoveEvent(self, event):
        self.current_point = event.pos()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QPoint(0, 0), self.image)
            if self.pressed and self.pressed_point is not None and self.current_point is not None:
                qp.drawRect(QRect(self.pressed_point, self.current_point))
        qp.end()


class DisplayWindowClass(QMainWindow, main_form_class):
    camera_thread = None
    serial_thread = None

    serial_port = load_value('serial', 'port', 'Test')
    serial_port_action_list = []

    logger = pyqtSignal(str)
    camera_connected = pyqtSignal()
    camera_disconnected = pyqtSignal()
    serial_connected = pyqtSignal()
    serial_disconnected = pyqtSignal()

    def __init__(self, parent=None):
        super(DisplayWindowClass, self).__init__(parent)
        self.setupUi(self)

        # logging
        self.logger.connect(self.append_log)
        log_text_edit = QPlainTextEditLogger(self)
        log_text_edit.setFormatter(logging.Formatter(logging_config['widget']['format']))
        log_text_edit.setLevel(logging_config['widget']['level'])
        logging.getLogger().addHandler(log_text_edit)

        # setup menus and shortcut
        self.setup_file_menu()
        self.setup_serial_menu()
        self.setup_shortcut()

        self.cameraWidget = ImageWidget(self.cameraWidget)
        self.rpyLabel.setText('RPY: Disconnected')

        # signal and slot
        self.serial_connected.connect(self.update_window_serial_connected)
        self.serial_disconnected.connect(self.update_window_serial_disconnected)
        self.camera_connected.connect(self.update_window_camera_connected)
        self.camera_disconnected.connect(self.update_window_camera_disconnected)

        # update widget every 100ms
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_window)
        self.timer.start(100)  # 100ms

        # macro
        self.macro = widget.MacroWidget(self)
        self.kinematic = widget.KinematicWidget(self)

    def setup_file_menu(self):
        self.actionQuit.triggered.connect(self.close)

        self.actionCameraConnect.triggered.connect(self.camera_connect)
        self.actionCameraDisconnect.triggered.connect(self.camera_disconnect)

        self.actionSerialConnect.triggered.connect(self.serial_connect)
        self.actionSerialDisconnect.triggered.connect(self.serial_disconnect)

    def setup_serial_menu(self):
        port_list = get_serial_port_list()
        if len(port_list):
            for port in port_list:
                action = QAction(port, self)
                action.setEnabled(True)
                action.setCheckable(True)
                self.menuSerialPort.addAction(action)
                self.serial_port_action_list.append(action)

                if self.serial_port == port:
                    action.setChecked(True)
        else:
            action = QAction('Cannot detect usable port ...', self)
            action.setEnabled(False)
            action.setCheckable(False)
            self.menuSerialPort.addAction(action)
            self.serial_port_action_list.append(action)

        action = QAction('Test', self)
        action.setEnabled(True)
        action.setCheckable(True)
        self.menuSerialPort.addSeparator()
        self.menuSerialPort.addAction(action)
        self.serial_port_action_list.append(action)
        if self.serial_port == 'Test':
            action.setChecked(True)

        self.menuSerialPort.triggered[QAction].connect(self.select_serial_port)

    def setup_shortcut(self):
        # game start & stop menu action
        # self.actionGameStart.shortcut = QShortcut(QKeySequence(Qt.Key_4, Qt.Key_5, Qt.Key_6), self)
        # self.actionGameStart.shortcut.activated.connect(self.game_start)
        # self.actionGameStart.triggered.connect(self.game_start)

        # self.actionGameStop.shortcut = QShortcut(QKeySequence(Qt.Key_3, Qt.Key_2, Qt.Key_1), self)
        # self.actionGameStop.shortcut.activated.connect(self.game_stop)
        # self.actionGameStop.triggered.connect(self.game_stop)
        pass

    def select_serial_port(self, action):
        # un-check all menu actions
        for item in self.serial_port_action_list:
            item.setChecked(False)

        # check selected serial port action
        action.setChecked(True)
        self.serial_port = action.text()
        save_value('serial', 'port', self.serial_port)

    def serial_connect(self):
        self.statusBar.showMessage('Serial connecting...')
        self.serial_thread = SerialThread(
            parent=self,
            name='SerialThread',
            port=self.serial_port,
            baudrate=load_value('serial', 'baudrate', 9600),
            timeout=load_value('serial', 'timeout', 5),
            delay=load_value('serial', 'delay', 1),
        )

    def serial_disconnect(self):
        self.statusBar.showMessage('Serial disconnecting...')
        if self.serial_thread is not None:
            self.serial_thread.do_stop()
            self.serial_thread.join()
            self.serial_thread = None

    def camera_connect(self):
        self.statusBar.showMessage('Camera connecting...')
        self.camera_thread = CameraThread(
            self,
            name='CameraThread',
            width=load_value('camera', 'width', 800),
            height=load_value('camera', 'height', 600),
            fps=load_value('camera', 'fps', 15),
            delay=load_value('camera', 'delay', 0.05)
        )

    def camera_disconnect(self):
        self.statusBar.showMessage('Camera disconnecting...')
        if self.camera_thread is not None:
            self.camera_thread.do_stop()
            self.camera_thread.join()
            self.camera_thread = None

    def update_window(self):
        if self.camera_thread:
            img = self.camera_thread.get_image()
            if img is not None:
                width = load_value('camera', 'width', 300)
                height = load_value('camera', 'height', 240)
                main_img = resize_image(img, width, height)
                main_img = cv2.cvtColor(main_img, cv2.COLOR_BGR2RGB)

                height, width, bpc = main_img.shape
                bpl = bpc * width
                main_image = QImage(main_img.data, width, height, bpl, QImage.Format_RGB888)
                self.cameraWidget.set_image(main_image)

        if self.serial_thread:
            rpy = self.serial_thread.get_rpy()
            self.rpyLabel.setText('RPY: ({}, {}, {})'.format(rpy[0], rpy[1], rpy[2]))

    def update_window_serial_connected(self):
        self.actionSerialConnect.setEnabled(False)
        self.actionSerialDisconnect.setEnabled(True)
        self.macroStartButton.setEnabled(True)
        self.macroStopButton.setEnabled(False)

        # kinematic
        self.kinematicOptionSend.setEnabled(True)
        self.kinematicOptionLoadAndSend.setEnabled(True)
        self.kinematicSendButton.setEnabled(True)

        self.rpyLabel.setText('RPY: Connected')
        self.statusBar.showMessage('Serial Connected')

    def update_window_serial_disconnected(self):
        self.actionSerialConnect.setEnabled(True)
        self.actionSerialDisconnect.setEnabled(False)
        self.macroStartButton.setEnabled(False)
        self.macroStopButton.setEnabled(False)

        # kinematic
        self.kinematicOptionSend.setEnabled(False)
        self.kinematicOptionLoadAndSend.setEnabled(False)
        self.kinematicSendButton.setEnabled(False)

        self.rpyLabel.setText('RPY: Disconnected')
        self.statusBar.showMessage('Serial Disconnected')

    def update_window_camera_connected(self):
        self.actionCameraConnect.setEnabled(False)
        self.actionCameraDisconnect.setEnabled(True)
        self.statusBar.showMessage('Camera Connected')

    def update_window_camera_disconnected(self):
        self.actionCameraConnect.setEnabled(True)
        self.actionCameraDisconnect.setEnabled(False)
        self.statusBar.showMessage('Camera Disconnected')

    def append_log(self, msg):
        self.logPlainTextEdit.appendPlainText(msg)

    def closeEvent(self, event):
        self.camera_disconnect()
        self.serial_disconnect()


class QPlainTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = parent.logPlainTextEdit
        self.widget.setReadOnly(True)
        self.logger = parent.logger

    def emit(self, record):
        msg = self.format(record)
        self.logger.emit(msg)

    def write(self, msg):
        pass


if __name__ == '__main__':
    # logging config
    logging.basicConfig(level=logging_config['console']['level'], format=logging_config['console']['format'])

    app = QApplication(sys.argv)
    display = DisplayWindowClass()
    display.show()
    sys.exit(app.exec_())
