import ast
import json
import logging
from collections import OrderedDict

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from game.macro import MacroThread
from utils import sublist, save_value, load_value


class MacroWidget:

    def __init__(self, parent):
        self.parent = parent

        self.macroData = []
        self.macroModel = None
        self.setup_macro_widget()

        self.button_motions = {}
        self.update_kinematic()

        self.thread = None

    def update_kinematic(self):
        self.button_motions = load_value('kinematic', 'button_motions', {})
        self.parent.macroCommandComboBox.clear()

        # Add command list into combobox
        for key in self.button_motions.keys():
            if sublist(['name', 'data'], self.button_motions[key].keys()):
                if self.button_motions[key]['name'] != '-':
                    self.parent.macroCommandComboBox.addItem(self.button_motions[key]['name'])

    def setup_macro_widget(self):
        # Create an empty model for the list's data
        self.macroModel = QStandardItemModel(self.parent.macroListView)
        self.macroModel.itemChanged.connect(self.on_item_changed)
        self.macroModel.setColumnCount(3)
        self.macroModel.setHorizontalHeaderLabels(['', 'Name', 'Data'])

        # Apply the model to the list view
        self.parent.macroListView.setModel(self.macroModel)

        # Add load preset into combobox
        try:
            with open('data/macro.json') as data_file:
                objects = json.load(data_file, object_pairs_hook=OrderedDict)

            for name in objects.keys():
                self.parent.macroCommandLoadComboBox.addItem(name)
        except FileNotFoundError:
            pass

        self.parent.macroStartButton.setEnabled(False)
        self.parent.macroStartButton.clicked.connect(self.start)
        self.parent.macroStopButton.setEnabled(False)
        self.parent.macroStopButton.clicked.connect(self.stop)

        # Button events
        # self.insertKinematicsButton.clicked.connect(self.insert_kinematics_info)
        self.parent.macroInsertCommandButton.clicked.connect(self.insert_command)
        self.parent.macroInsertDelayButton.clicked.connect(self.insert_delay)

        self.parent.saveMacroButton.clicked.connect(self.save)
        self.parent.loadMacroButton.clicked.connect(self.load)
        self.parent.clearMacroButton.clicked.connect(self.clear)

    def insert_command(self):
        name = self.parent.macroCommandComboBox.currentText()
        for key in self.button_motions.keys():
            if self.button_motions[key]['name'] == name:
                data = self.button_motions[key]['data']
        self.append_row_to_model('motion', name, data)

    def insert_delay(self):
        delay = self.parent.macroDelaySpinBox.value()
        self.append_row_to_model('delay', 'delay', delay)

    def append_row_to_model(self, command, name, data, checked=True):
        # create an item with a caption
        item = QStandardItem('')

        # add a checkbox to it
        item.setCheckable(True)
        if checked:
            item.setCheckState(Qt.Checked)

        # Add the item to the model
        item = [item, QStandardItem(name), QStandardItem(str(data))]
        self.macroModel.appendRow(item)

        # Add the item to the data list
        self.macroData.append({
            'checked': checked,
            'command': command,
            'name': name,
            'data': data
        })

    def on_item_changed(self, item):
        data = self.macroData[item.row()]
        if item.column() == 0:
            data['checked'] = True if item.checkState() == 2 else False
        elif item.column() == 1:
            data['name'] = item.text()
        elif item.column() == 2:
            data['data'] = ast.literal_eval(item.text())

        self.macroData[item.row()] = data

    def save(self):
        name = self.parent.saveMacroNameLineEdit.text()
        save_value('macro', name, self.macroData)

    def load(self):
        name = self.parent.macroCommandLoadComboBox.currentText()
        new_data = load_value('macro', name, None)
        if new_data is None:
            return

        self.macroData = []
        self.macroModel.clear()
        self.macroModel.setColumnCount(3)
        self.macroModel.setHorizontalHeaderLabels(['', 'Name', 'Data'])
        for item in new_data:
            self.append_row_to_model(item['command'], item['name'], item['data'], item['checked'])

    def clear(self):
        self.macroData = []
        self.macroModel.clear()
        self.macroModel.setColumnCount(3)
        self.macroModel.setHorizontalHeaderLabels(['', 'Name', 'Data'])

    def start(self):
        logging.info('Macro Start')
        self.update_widget(True)
        self.thread = MacroThread(self.parent)
        self.thread.set_data(self.macroData)
        self.thread.start()

    def stop(self):
        logging.info('Macro Stop')
        self.update_widget(False)
        self.thread.stop()

    def update_widget(self, start):
        if start:
            self.parent.macroStartButton.setEnabled(False)
            self.parent.macroStopButton.setEnabled(True)
            self.parent.macroInsertGroupBox.setEnabled(False)
            self.parent.macroSaveLoadGroupBox.setEnabled(False)
        else:
            self.parent.macroStartButton.setEnabled(True)
            self.parent.macroStopButton.setEnabled(False)
            self.parent.macroInsertGroupBox.setEnabled(True)
            self.parent.macroSaveLoadGroupBox.setEnabled(True)
