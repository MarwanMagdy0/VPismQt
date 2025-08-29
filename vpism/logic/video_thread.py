from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage
import cv2
from vpism.logic.camera_wrapper import CameraWrapper, ImageWrapper
import numpy as np

class VideoThread(QThread):
    frame_signal = pyqtSignal(QImage)

    def __init__(self, source=0):
        super().__init__()
        self.running = True
        self.camera = CameraWrapper(source)

    def run(self):
        while self.running:
            ret, frame = self.camera.read()
            if ret and isinstance(frame, np.ndarray):
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qt_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
                qt_img = qt_img.scaled(640, 480, Qt.KeepAspectRatio)
                self.frame_signal.emit(qt_img)

    def stop(self):
        self.running = False
        self.camera.release()
        self.wait()