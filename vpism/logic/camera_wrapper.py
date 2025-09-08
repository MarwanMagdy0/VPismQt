import cv2
import time
from abc import ABC, abstractmethod
import numpy as np
try:
    from picamera2 import Picamera2
except ImportError:
    print("Picamera2 library not found. Picamera2Wrapper will not work.")

# ---------------------------
# Abstract Interface
# ---------------------------
class CameraInterface(ABC):
    @abstractmethod
    def read(self):
        """
        Capture or read one frame.
        Returns (ret, frame) like cv2.VideoCapture.read().
        """
        pass

    @abstractmethod
    def release(self):
        """Release the resource if needed."""
        pass

    @abstractmethod
    def switch_mode(self):
        """Cycle to the next mode: normal -> inverted -> vein -> normal -> ..."""
        pass

    @property
    @abstractmethod
    def current_mode(self):
        """Return current mode name."""
        pass


# ---------------------------
# Base class with mode logic
# ---------------------------
class ModeMixin:
    modes = ["normal", "inverted", "vein"]

    def __init__(self, mode="normal"):
        self.mode_index = self.modes.index(mode)
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def switch_mode(self):
        """Cycle to the next mode automatically"""
        self.mode_index = (self.mode_index + 1) % len(self.modes)

    @property
    def current_mode(self):
        return self.modes[self.mode_index]

    def _apply_vein_detection(self, frame, clahe_iterations=5, threshold_value=50):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        enhanced = gray.copy()
        for _ in range(clahe_iterations):
            enhanced = self.clahe.apply(enhanced)

        _, mask = cv2.threshold(enhanced, threshold_value, 255, cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        result = frame.copy()
        result[mask > 0] = [0, 255, 0]
        return result

    def _apply_mode(self, frame):
        """Apply the current mode to the frame"""
        mode = self.current_mode
        if mode == "normal":
            return frame
        elif mode == "inverted":
            return cv2.bitwise_not(frame)
        elif mode == "vein":
            return self._apply_vein_detection(frame)
        else:
            return frame


# ---------------------------
# OpenCV Video/Camera Wrapper
# ---------------------------
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


# ---------------------------
# Picamera2 Wrapper
# ---------------------------
class Picamera2Wrapper(ModeMixin, CameraInterface):
    def __init__(self, src='', mode="normal"):
        ModeMixin.__init__(self, mode)
        self.camera = Picamera2()
        self.camera.start()

    def read(self):
        try:
            frame = self.camera.capture_array()
            frame = cv2.resize(frame, (640, 480))
            return True, self._apply_mode(frame)
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return False, None

    def release(self):
        try:
            self.camera.stop()
        except Exception as e:
            print(f"Error releasing camera: {e}")


# ---------------------------
# Image File Wrapper
# ---------------------------
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
