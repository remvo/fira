#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import threading
import time

import cv2


class CameraThread(threading.Thread):
    parent = None
    image = None
    camera = None
    __do_stop = False

    def __init__(self, parent, name, width=800, height=600, fps=15, delay=0.05, do_start=True):
        threading.Thread.__init__(self)

        self.parent = parent
        self.name = name
        self.width, self.height, self.fps, self.delay = width, height, fps, delay

        if do_start:
            self.start()

    def run(self):
        logging.debug('Start')

        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.camera.set(cv2.CAP_PROP_FPS, self.fps)
        self.parent.camera_connected.emit()

        while not self.__do_stop:
            grabbed, self.image = self.camera.read()
            time.sleep(self.delay)

        self.camera.release()
        self.image = None
        logging.debug('Exit')
        self.parent.camera_disconnected.emit()

    def do_stop(self):
        self.__do_stop = True

    def get_image(self):
        return self.image
