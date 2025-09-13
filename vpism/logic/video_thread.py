from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage
import cv2
from vpism.logic.camera_wrapper import CameraWrapper, ImageWrapper, Picamera2Wrapper
import numpy as np

class VideoThread(QThread):
    frame_signal = pyqtSignal(QImage)

    def __init__(self, source=0):
        super().__init__()
        self.running = True
        self.camera = Picamera2Wrapper(source)

    def run(self):
        while self.running:
            ret, frame = self.camera.read()
            if ret and isinstance(frame, np.ndarray):
                if len(frame.shape) == 2:
                    h, w = frame.shape
                    bytes_per_line = frame.strides[0]
                    qt_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
                else:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    if not frame.flags['C_CONTIGUOUS']:
                        frame = np.ascontiguousarray(frame)

                    h, w, ch = frame.shape
                    bytes_per_line = frame.strides[0]
                    qt_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

                qt_img = qt_img.scaled(640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                self.frame_signal.emit(qt_img)

    def switch_mode(self):
        self.camera.switch_mode()

    def stop(self):
        self.running = False
        self.camera.release()
        self.wait()
