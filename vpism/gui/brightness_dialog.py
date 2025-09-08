from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSlider
from PyQt5.QtCore import Qt
from vpism.logic.led_api import set_brightness

class BrightnessDialog(QDialog):
    value = 50  # default brightness value
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Big label for value only
        self.value_label = QLabel(f"{BrightnessDialog.value}", self)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        # Vertical slider
        self.slider = QSlider(Qt.Vertical, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(BrightnessDialog.value)
        # self.slider.setInvertedAppearance(True)   # flip so it starts from bottom
        self.slider.setFixedSize(120, 300)         # thinner and taller
        self.slider.setStyleSheet("""
            QSlider::groove:vertical {
                border: 1px solid #999999;
                width: 15px;                      /* thinner groove */
                background: #cccccc;
                border-radius: 3px;
            }
            QSlider::add-page:vertical {
                background: #3b99fc;
                border: 1px solid #777;
                width: 15px;
                border-radius: 3px;
            }
            QSlider::sub-page:vertical {
                background: #eeeeee;
                border: 1px solid #777;
                width: 15px;
                border-radius: 3px;
            }
            QSlider::handle:vertical {
                background: #ffffff;
                border: 2px solid #3b99fc;
                width: 20px;                     /* smaller handle */
                height: 20px;
                margin: -2px -7px;               /* keep it centered on groove */
                border-radius: 10px;
            }
            QSlider::handle:vertical:hover {
                background: #e6f0ff;
                border: 2px solid #1a73e8;
            }
        """)
        self.slider.valueChanged.connect(self.update_label)

        layout.addWidget(self.value_label)
        layout.addWidget(self.slider, alignment=Qt.AlignCenter)

        self.resize(120, 360)

    def update_label(self, value):
        self.value_label.setText(str(value))
        BrightnessDialog.value = value
        set_brightness(value)
