#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import sys
import threading
import time

import serial

HEADER = 0
SELECT_MODE = 1
STRIDE_LEFT_LEG = 2
STRIDE_RIGHT_LEG = 3
SPEED = 4
SWING_LEFT_LEG = 5
SWING_RIGHT_LEG = 6
UP_LEFT_LEG = 7
UP_RIGHT_LEG = 8
TURN_LEFT_ANGLE = 9
TURN_RIGHT_ANGLE = 10
OFFSET_LEFT_LEG = 11
OFFSET_RIGHT_LEG = 12
HEAD_LEFT_RIGHT = 13
HEAD_UP_DOWN = 14
END_DATA1 = 15
END_DATA2 = 16


class SerialThread(threading.Thread):
    serial = None
    _do_stop = False
    _rpy = (0, 0, 0)

    def __init__(self, parent, name, port='test', baudrate=9600, timeout=None, delay=1, do_start=True):
        threading.Thread.__init__(self)

        self.parent = parent
        self.name = name
        self.port, self.baudrate, self.timeout = port, baudrate, timeout
        self.delay = delay

        if do_start:
            self.start()

    def run(self):
        logging.debug('Start')

        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            ) if self.port.lower() != 'test' else None
            self.parent.serial_connected.emit()
        except serial.serialutil.SerialException:
            logging.error('SerialException: {}'.format(sys.exc_info()[1]))
            return
        except:
            logging.error('Unexpected error: {}'.format(sys.exc_info()[0]))
            return

        while not self._do_stop:
            data = self.serial.read(5) if self.serial is not None else (255, 1, 2, 3, 254)

            if data is not None and len(data) == 5 and int(data[0]) == 255 and int(data[4]) == 254:
                self._rpy = (int(data[3]), int(data[2]), int(data[1]))
            elif data is not None:
                logging.error('Get unexpected values from serial: {}, len: {}'.format(data, len(data)))
            else:
                logging.debug('Timeout read from serial...')

            time.sleep(self.delay)

        if self.serial is not None and self.serial.isOpen():
            self.serial.close()
        self.serial = None
        logging.debug('Exit')
        self.parent.serial_disconnected.emit()

    def do_stop(self):
        self._do_stop = True

    def get_rpy(self):
        return self._rpy

    def send_data(self, data):
        logging.debug('Send data: {}'.format(data))
        if self.serial is not None:
            self.serial.cancel_read()
            self.serial.write(data)
            logging.debug('Send data succeed')
        elif self.port == 'Test':
            logging.debug('[Test] Send data succeed')
