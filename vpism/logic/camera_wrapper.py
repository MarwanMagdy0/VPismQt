import cv2, time

class CameraWrapper:
    def __init__(self, source=0):
        """
        source = 0 (default camera), 
                 'video.mp4' (video file), 
                 or an RTSP/HTTP stream
        """
        self.cap = cv2.VideoCapture(source)

    def read(self):
        """Read one frame. Returns (ret, frame) like cv2.VideoCapture.read()."""
        if not self.cap.isOpened():
            return False, None
        return self.cap.read()

    def release(self):
        """Release the video source."""
        if self.cap.isOpened():
            self.cap.release()

class ImageWrapper:
    def __init__(self, path):
        """
        path = 'image.jpg' (path to an image file)
        """
        self.image = cv2.imread(path, cv2.IMREAD_COLOR)
        self.loaded = self.image is not None

    def read(self):
        """Return (ret, frame) similar to cv2.VideoCapture.read()."""
        time.sleep(0.03)  # simulate a small delay
        if not self.loaded:
            return False, None
        return True, self.image.copy()  # return a copy so original isn’t modified

    def release(self):
        """For compatibility only (nothing to release here)."""
        self.image = None
        self.loaded = False