import logging
from enum import Enum
from functools import partial

from PyQt5.QtWidgets import QPushButton

from utils.file_control import load_value, save_value


INIT_DATA = [255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 254, 254]


class ButtonMode(Enum):
    NORMAL = 1
    SAVE = 2
    DELETE = 3


class KinematicWidget:
    fields = [
        'dir',
        'strideLeft', 'strideRight',
        'speed',
        'swingLeft', 'swingRight',
        'upLeft', 'upRight',
        'turnLeft', 'turnRight',
        'offsetLeft', 'offsetRight',
        'headLeftRight', 'headUpDown'
    ]

    max_row = 15
    max_col = 4
    button_mode = ButtonMode.NORMAL

    def __init__(self, parent):
        self.parent = parent

        self.buttons = {}
        self.button_motions = load_value('kinematic', 'button_motions', {})
        self.setup_kinematic_widget()

        self.thread = None

    def setup_kinematic_widget(self):
        layout = self.parent.robotMotionsGroupboxLayout

        for i in range(0, self.max_row):
            for j in range(0, self.max_col):
                key = '{:02d}_{:02d}'.format(i, j)
                if key not in self.button_motions.keys():
                    self.button_motions[key] = {
                        'name': '-',
                        'data': [],
                        'shortcut': None
                    }

                button = QPushButton(self.button_motions[key]['name'])
                button.clicked.connect(partial(self.button_click, key))
                self.buttons[key] = button

                # add to the layout
                layout.addWidget(self.buttons[key], i, j)

        save_value('kinematic', 'button_motions', self.button_motions)
        self.set_buttons_enable(True)

        # Button events
        self.parent.kinematicSendButton.clicked.connect(self.click_send_data)
        self.parent.kinematicSaveButton.clicked.connect(self.click_save)
        self.parent.kinematicDeleteButton.clicked.connect(self.click_delete)
        self.parent.kinematicClearButton.clicked.connect(self.click_clear)

    def get_kinematics_info(self):
        # header
        data = [255]

        # data
        for field in self.fields:
            item = getattr(self.parent, '{}SpinBox'.format(field))
            data.append(item.value())

        # end data
        data.append(254)
        data.append(254)

        return data

    def set_kinematics_info(self, data):
        # data
        for idx, field in enumerate(self.fields):
            item = getattr(self.parent, '{}SpinBox'.format(field))
            item.setValue(data[idx + 1])

    def send_data(self, data):
        if self.parent.serial_thread:
            self.parent.serial_thread.send_data(data)
        else:
            logging.error('Serial is not connected')

    def click_send_data(self):
        self.send_data(self.get_kinematics_info())

    def button_click(self, key):
        motion = self.button_motions[key]

        if self.button_mode == ButtonMode.SAVE and motion['name'] == '-':
            self.button_motions[key]['name'] = self.parent.kinematicNameLineEdit.text()
            self.button_motions[key]['data'] = self.get_kinematics_info()
            self.buttons[key].setText(self.button_motions[key]['name'])
            save_value('kinematic', 'button_motions', self.button_motions)
            self.after_save()
            return

        if self.button_mode == ButtonMode.DELETE and motion['name'] != '-':
            self.button_motions[key]['name'] = '-'
            self.button_motions[key]['data'] = INIT_DATA
            self.buttons[key].setText(self.button_motions[key]['name'])
            save_value('kinematic', 'button_motions', self.button_motions)
            self.after_delete()
            return

        if self.parent.kinematicOptionLoad.isChecked():
            self.set_kinematics_info(motion['data'])
            self.parent.kinematicNameLineEdit.setText(motion['name'])
        elif self.parent.kinematicOptionSend.isChecked():
            self.send_data(motion['data'])
        elif self.parent.kinematicOptionLoadAndSend.isChecked():
            self.set_kinematics_info(motion['data'])
            self.send_data(motion['data'])

    def set_buttons_enable(self, flag):
        """
        Kinematic 버튼들을 flag에 따라 활성화 또는 비활성화
        flag:
            - True: 할당되어 있는 버튼들을 활성화
            - False: 할당되지 않은 버튼들을 활성화
        """
        for i in range(0, self.max_row):
            for j in range(0, self.max_col):
                key = '{:02d}_{:02d}'.format(i, j)
                if flag:
                    self.buttons[key].setEnabled(self.buttons[key].text() != '-')
                else:
                    self.buttons[key].setEnabled(self.buttons[key].text() == '-')

    def click_save(self):
        if self.button_mode == ButtonMode.NORMAL:
            if self.parent.kinematicNameLineEdit.text() == '':
                logging.error('Please input kinematic name')
                return

            self.before_save()
        elif self.button_mode == ButtonMode.SAVE:
            self.after_save()

    def before_save(self):
        self.button_mode = ButtonMode.SAVE
        self.parent.kinematicSaveButton.setText('Cancel')
        self.parent.kinematicDeleteButton.setEnabled(False)
        self.parent.kinematicClearButton.setEnabled(False)
        self.set_buttons_enable(False)

    def after_save(self):
        self.button_mode = ButtonMode.NORMAL
        self.parent.kinematicSaveButton.setText('Save')
        self.parent.kinematicDeleteButton.setEnabled(True)
        self.parent.kinematicClearButton.setEnabled(True)
        self.set_buttons_enable(True)
        self.parent.macro.update_kinematic()
        self.parent.kinematicsWidget.update()

    def click_delete(self):
        if self.button_mode == ButtonMode.NORMAL:
            self.before_delete()
        elif self.button_mode == ButtonMode.DELETE:
            self.after_delete()

    def before_delete(self):
        self.button_mode = ButtonMode.DELETE
        self.parent.kinematicDeleteButton.setText('Cancel')
        self.parent.kinematicSaveButton.setEnabled(False)
        self.parent.kinematicClearButton.setEnabled(False)
        self.set_buttons_enable(True)

    def after_delete(self):
        self.button_mode = ButtonMode.NORMAL
        self.parent.kinematicDeleteButton.setText('Delete')
        self.parent.kinematicSaveButton.setEnabled(True)
        self.parent.kinematicClearButton.setEnabled(True)
        self.set_buttons_enable(True)
        self.parent.macro.update_kinematic()
        self.parent.kinematicsWidget.update()

    def click_clear(self):
        self.set_kinematics_info(INIT_DATA)
        self.parent.kinematicNameLineEdit.clear()

    def update_widget(self, start):
        pass
