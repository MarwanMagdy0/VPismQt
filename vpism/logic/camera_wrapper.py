import sys
import cv2
import time
import numpy as np
from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None
    print("Picamera2 library not found. Picamera2Wrapper will not work.")


# =========================
# Abstract Camera Interface
# =========================
class CameraInterface(ABC):
    @abstractmethod
    def read(self):
        """Return (ret, frame) just like cv2.VideoCapture.read()"""
        pass

    @abstractmethod
    def release(self):
        pass

    @abstractmethod
    def switch_mode(self):
        pass

    @property
    @abstractmethod
    def current_mode(self):
        pass


# =========================
# Mode Mixin
# =========================
class ModeMixin:
    modes = ["normal", "inverted", "vein"]

    def __init__(self, mode="normal"):
        self.mode_index = self.modes.index(mode)
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def switch_mode(self):
        self.mode_index = (self.mode_index + 1) % len(self.modes)

    @property
    def current_mode(self):
        return self.modes[self.mode_index]

    def _apply_vein_detection(self, frame, clahe_iterations=1):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        enhanced = gray.copy()
        for _ in range(clahe_iterations):
            enhanced = self.clahe.apply(enhanced)
        return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

    def _apply_mode(self, frame, roi_ratio=0.5, alpha=0.7):
        """
        roi_ratio: how big the ROI is compared to the frame (0.5 = half)
        alpha: transparency of background (1 = solid white, 0 = fully original)
        """
        h, w = frame.shape[:2]

        # ROI square based on ratio
        roi_size = int(min(h, w) * roi_ratio)
        x1 = (w - roi_size) // 2
        y1 = (h - roi_size) // 2
        x2 = x1 + roi_size
        y2 = y1 + roi_size

        # Make white overlay
        white_bg = np.ones_like(frame, dtype=np.uint8) * 255

        # Blend frame with white to get semi-transparent effect
        output = cv2.addWeighted(frame, 1 - alpha, white_bg, alpha, 0)

        # Extract ROI from original
        roi = frame[y1:y2, x1:x2]

        # Apply current mode only to ROI
        mode = self.current_mode
        if mode == "normal":
            processed_roi = roi
        elif mode == "inverted":
            processed_roi = cv2.bitwise_not(roi)
        elif mode == "vein":
            processed_roi = self._apply_vein_detection(roi)
        else:
            processed_roi = roi

        # Paste back ROI into blended output
        output[y1:y2, x1:x2] = processed_roi
        return output


# =========================
# OpenCV Camera Wrapper
# =========================
class CameraWrapper(ModeMixin, CameraInterface):
    def __init__(self, source=0, mode="normal"):
        ModeMixin.__init__(self, mode)
        self.cap = cv2.VideoCapture(source)

    def read(self):
        if not self.cap.isOpened():
            return False, None
        ret, frame = self.cap.read()
        if not ret:
            return ret, None
        return True, self._apply_mode(frame)

    def release(self):
        if self.cap.isOpened():
            self.cap.release()


# =========================
# Raspberry Pi Picamera2 Wrapper
# =========================
class Picamera2Wrapper(ModeMixin, CameraInterface):
    def __init__(self, src=0, mode="normal"):
        if Picamera2 is None:
            raise RuntimeError("Picamera2 library not available")
        ModeMixin.__init__(self, mode)
        self.camera = Picamera2()
        config = self.camera.create_preview_configuration(
            main={"format": "RGB888", "size": (640, 480)}
        )
        self.camera.configure(config)
        self.camera.start()

    def read(self):
        try:
            frame = self.camera.capture_array()
            return True, self._apply_mode(frame)
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return False, None

    def release(self):
        try:
            self.camera.stop()
        except Exception as e:
            print(f"Error releasing camera: {e}")


# =========================
# Image Wrapper (Static Image)
# =========================
class ImageWrapper(ModeMixin, CameraInterface):
    def __init__(self, src, mode="normal"):
        ModeMixin.__init__(self, mode)
        self.image = cv2.imread(src, cv2.IMREAD_COLOR)
        self.loaded = self.image is not None

    def read(self):
        time.sleep(0.03)  # simulate delay
        if not self.loaded:
            return False, None
        return True, self._apply_mode(self.image.copy())

    def release(self):
        self.image = None
        self.loaded = False
