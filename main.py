from vpism.gui.ui_scripts.load import Ui_MainWindow
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QLabel, QPushButton, QDialog,
    QVBoxLayout, QComboBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon, QTransform
import sys, os
from pathlib import Path
import PyQt5
from vpism.logic.video_thread import VideoThread
from vpism.gui.brightness_dialog import BrightnessDialog
from vpism.gui.show_files_dialog import ShowFilesDialog
from vpism.logic.led_api import set_brightness, cleanup


# Fix Qt plugin path (for PyQt5 on some platforms)
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.fspath(
    Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
)


class MainWindow(QMainWindow, Ui_MainWindow):
    image_frame: QLabel
    close_button: QPushButton
    brightness_button: QPushButton
    viens_button: QPushButton
    scale_button: QPushButton
    save_showfiles_button: QPushButton
    play_pause_button: QPushButton
    rotate_button: QPushButton

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(800, 480)
        self.rotation_angle = 0
        # Camera wrapper thread
        self.video_thread = VideoThread(source=0)
        self.video_thread.frame_signal.connect(self.update_image)
        self.video_thread.start()
        self.image_frame.setScaledContents(False)

        # Store current frame + zoom factor
        self.current_frame = None
        self.zoom_factor = 1.0

        # Close button → exit program
        self.close_button.clicked.connect(self.close)

        # Brightness dialog
        self.brightness_dialog = None
        self.brightness_button.clicked.connect(self.toggle_brightness_dialog)

        # Scale button → zoom with cropping
        self.scale_button.setText("1x")  # initial label
        self.scale_button.clicked.connect(self.zoom_image)

        # Save/Show files button → open files dialog
        self.save_showfiles_button.clicked.connect(self.open_showfiles_dialog)

        # Play/Pause button logic
        self.play_pause_button.setProperty("paused", False)  # initial state
        self.save_showfiles_button.setProperty("showfiles", True)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        # Rotate button → rotate image
        self.rotate_button.clicked.connect(self.rotate_image)

        self.viens_button.clicked.connect(self.video_thread.switch_mode)

    def toggle_play_pause(self):
        """Toggle play/pause state of video."""
        paused = self.play_pause_button.property("paused")
        if paused:
            self.play_pause_button.setProperty("paused", False)
            self.play_pause_button.setIcon(QIcon(":/imgs/icons/pause.png"))  # adjust to your resource path
            self.save_showfiles_button.setIcon(QIcon(":/imgs/icons/files.png"))
            self.save_showfiles_button.setProperty("showfiles", True)
        else:
            self.play_pause_button.setIcon(QIcon(":/imgs/icons/play.png"))
            self.play_pause_button.setProperty("paused", True)
            self.save_showfiles_button.setIcon(QIcon(":/imgs/icons/save.png"))
            self.save_showfiles_button.setProperty("showfiles", False)

    # ----------------------------
    # Image update & zoom
    # ----------------------------
    def update_image(self, qt_img):
        """Save latest frame and show with zoom applied."""
        if self.play_pause_button.property("paused"):
            return  # Do nothing if paused
        
        transform = QTransform().rotate(self.rotation_angle)
        self.current_frame = QPixmap.fromImage(qt_img)
        self.current_frame = self.current_frame.transformed(transform, Qt.SmoothTransformation)
        self.apply_zoom()

    def apply_zoom(self):
        """Apply zoom (cropping) to current frame and display."""
        if not self.current_frame:
            return

        img = self.current_frame
        w, h = img.width(), img.height()

        # Crop rectangle size depends on zoom
        crop_w = int(w / self.zoom_factor)
        crop_h = int(h / self.zoom_factor)

        # Center crop
        x = (w - crop_w) // 2
        y = (h - crop_h) // 2

        cropped = img.copy(x, y, crop_w, crop_h)

        # Scale cropped region back to label size
        scaled = cropped.scaled(
            self.image_frame.size(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )
        self.image_frame.setPixmap(scaled)

    def zoom_image(self):
        """Cycle zoom levels (1x, 2x)."""
        if self.zoom_factor == 1.0:
            self.zoom_factor = 2.0
        else:
            self.zoom_factor = 1.0

        # Update button label
        self.scale_button.setText(f"{int(self.zoom_factor)}x")

        self.apply_zoom()

    # ----------------------------
    # Brightness dialog
    # ----------------------------
    def toggle_brightness_dialog(self):
        if self.brightness_dialog and self.brightness_dialog.isVisible():
            self.brightness_dialog.close()
            self.brightness_dialog = None
        else:
            self.brightness_dialog = BrightnessDialog(self)
            self.brightness_dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

            # Ensure dialog knows its real size
            self.brightness_dialog.adjustSize()
            self.brightness_dialog.show()   # let Qt compute size
            self.brightness_dialog.hide()   # hide until positioned

            # Button global position
            btn_pos = self.brightness_button.mapToGlobal(
                self.brightness_button.rect().topLeft()
            )
            dlg_geometry = self.brightness_dialog.frameGeometry()

            # Position left of button
            x = btn_pos.x() - dlg_geometry.width() - 5
            y = btn_pos.y()

            self.brightness_dialog.move(x, y)
            self.brightness_dialog.show()

    # ----------------------------
    # ShowFiles dialog
    # ----------------------------
    def open_showfiles_dialog(self):
        showfiles = self.save_showfiles_button.property("showfiles")

        if showfiles:
            # Normal behavior: show the dialog
            dlg = ShowFilesDialog(self)
            dlg.adjustSize()
            dlg.image_selected.connect(self.set_image_from_dialog)

            # Button geometry in global coordinates
            btn_rect = self.save_showfiles_button.rect()
            btn_pos = self.save_showfiles_button.mapToGlobal(btn_rect.bottomLeft())

            # Default: show below button
            x = btn_pos.x()
            y = btn_pos.y() + 5

            # Shift dialog to the left of the button
            x = x - dlg.width() - 5   # 5px margin from button
            y = y - dlg.height() + 100 # 5px margin from button

            dlg.move(x, y)
            dlg.exec_()
        else:
            # Save pixmap to a file inside a folder named with today's date
            pixmap = self.image_frame.pixmap()
            if pixmap:
                from datetime import datetime
                import os

                date_str = datetime.now().strftime("%Y-%m-%d")
                dir_path = os.path.join("saved_images", date_str)
                os.makedirs(dir_path, exist_ok=True)

                file_index = 1
                while True:
                    file_path = os.path.join(dir_path, f"image_{file_index}.png")
                    if not os.path.exists(file_path):
                        break
                    file_index += 1

                pixmap.save(file_path)
                print(f"Saved image to: {file_path}")

    def set_image_from_dialog(self, pixmap: QPixmap):
        """Set the QLabel to show the selected image and update pause button icon."""
        if pixmap is None:
            return

        self.current_frame = pixmap
        self.apply_zoom()
        # Set pause icon
        pause_icon = QIcon(":/imgs/icons/play.png")  # adjust to your resource path
        self.play_pause_button.setIcon(pause_icon)
        self.play_pause_button.setProperty("paused", True)

    # ----------------------------
    # Rotate image
    # ----------------------------
    def rotate_image(self):
        """Rotate the current frame upside down (180°)."""
        if not self.current_frame:
            return
        self.rotation_angle = (self.rotation_angle + 180) % 360
    # ----------------------------
    # Cleanup
    # ----------------------------
    def closeEvent(self, event):
        if self.video_thread:
            self.video_thread.stop()
        event.accept()


# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec_())
