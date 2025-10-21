from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSlider, QPushButton
from PyQt5.QtCore import Qt, QTimer
from vpism.logic.led_api import set_brightness
from vpism.logic.buzzer_api import beep, buzzer_cleanup


class BrightnessDialog(QDialog):
    value = 50  # default brightness value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Top button (+10)
        self.plus_btn = QPushButton("+", self)
        self.plus_btn.setFixedSize(40, 30)
        self.plus_btn.setStyleSheet("""
            QPushButton {
                background: #3b99fc;
                color: white;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #1a73e8;
            }
        """)
        self.plus_btn.clicked.connect(lambda: self.adjust_value(10))
        layout.addWidget(self.plus_btn, alignment=Qt.AlignCenter)

        # Value label
        self.value_label = QLabel(f"{BrightnessDialog.value}", self)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 16px; font-weight: bold; color: black; background: transparent;")
        layout.addWidget(self.value_label)

        # Slider
        self.slider = QSlider(Qt.Vertical, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(BrightnessDialog.value)
        self.slider.setFixedSize(60, 180)
        self.slider.setStyleSheet("""
            QSlider {
                background: transparent;
            }
            QSlider::groove:vertical {
                background: #3b99fc;
                border-radius: 5px;
                width: 6px;
                margin: 0px;
            }
            QSlider::sub-page:vertical {
                background: #e0e0e0;
                border-radius: 5px;
            }
            QSlider::add-page:vertical {
                background: #3b99fc;
                border-radius: 5px;
            }
            QSlider::handle:vertical {
                background: white;
                border: 2px solid #3b99fc;
                height: 16px;
                width: 16px;
                margin: -5px -5px;
                border-radius: 8px;
            }
            QSlider::handle:vertical:hover {
                background: #f0f0f0;
                border: 2px solid #1a73e8;
            }
        """)
        self.slider.valueChanged.connect(self.update_label)
        layout.addWidget(self.slider, alignment=Qt.AlignCenter)

        # Bottom button (-10)
        self.minus_btn = QPushButton("-", self)
        self.minus_btn.setFixedSize(40, 30)
        self.minus_btn.setStyleSheet("""
            QPushButton {
                background: #3b99fc;
                color: white;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #1a73e8;
            }
        """)
        self.minus_btn.clicked.connect(lambda: self.adjust_value(-10))
        layout.addWidget(self.minus_btn, alignment=Qt.AlignCenter)

        # Window size
        self.resize(100, 300)

        # Optional: beep on button press
        # self.plus_btn.clicked.connect(beep)
        # self.minus_btn.clicked.connect(beep)

    def showEvent(self, event):
        self.activateWindow()
        self.raise_()
        self.setFocus()
        super().showEvent(event)

    def update_label(self, value):
        """Update display and send brightness."""
        self.value_label.setText(str(value))
        BrightnessDialog.value = value
        # Debounced hardware call
        QTimer.singleShot(50, lambda: set_brightness(value))

    def adjust_value(self, delta):
        """Increase or decrease brightness by delta."""
        new_val = max(0, min(100, self.slider.value() + delta))
        self.slider.setValue(new_val)
