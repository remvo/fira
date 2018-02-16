#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import time
from threading import Thread


class MacroThread(Thread):

    def __init__(self, parent):
        Thread.__init__(self)
        self.parent = parent
        self.camera = parent.camera_thread
        self.serial = parent.serial_thread

        self.__do_stop = False
        self.data = None

    def stop(self):
        self.__do_stop = True

    def set_data(self, data):
        self.data = data

    def run(self):
        if self.data is None:
            return

        for item in self.data:
            if self.__do_stop:
                break

            if item['checked'] is False:
                continue

            if item['command'] == 'delay':
                logging.info(item)
                for i in range(int(item['data'])):
                    if self.__do_stop:
                        break
                    time.sleep(1)
            elif item['command'] == 'motion':
                logging.info(item)
                self.serial.send_data(item['data'])

        logging.info('Macro finished')
        self.parent.macro.update_widget(False)
