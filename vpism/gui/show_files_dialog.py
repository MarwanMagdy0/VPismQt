from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton,
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox,
    QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap, QIcon
from pathlib import Path
import sys

# -----------------------------
# Frameless confirmation dialog
# -----------------------------
class ConfirmDialog(QDialog):
    """Modern frameless, dark-mode confirmation dialog."""
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        self.setFixedSize(320, 120)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                border-radius: 12px;
            }
            QLabel {
                background-color: #2b2b2b;
                font-size: 14px;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #6272a4;
                color: #ffffff;
                border: none;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #7083c2;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.label = QLabel(message)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        btn_layout = QHBoxLayout()
        self.yes_btn = QPushButton("Yes")
        self.no_btn = QPushButton("No")
        btn_layout.addWidget(self.yes_btn)
        btn_layout.addWidget(self.no_btn)
        layout.addLayout(btn_layout)

        self.yes_btn.clicked.connect(self.accept)
        self.no_btn.clicked.connect(self.reject)


# -----------------------------
# Show files dialog
# -----------------------------
class ShowFilesDialog(QDialog):
    """Dark, frameless file viewer with thumbnails."""
    image_selected = pyqtSignal(QPixmap)  # signal to send image on double-click

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup | Qt.WindowStaysOnTopHint)
        self.base_dir = Path("saved_images")

        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #e0e0e0; font-family: 'Segoe UI'; font-size: 13px; }
            QComboBox { background-color: #3c3f41; color: #e0e0e0; border: 1px solid #555; padding: 4px 6px; border-radius: 4px; min-width: 120px; }
            QComboBox::drop-down { border: none; }
            QPushButton { border: none; background-color: transparent; color: #e0e0e0; }
            QPushButton:hover { background-color: #44475a; border-radius: 4px; }
            QListWidget { background-color: #2b2b2b; border: 1px solid #555; color: #e0e0e0; }
            QListWidget::item { background-color: #3c3f41; margin: 4px; border-radius: 6px; padding: 4px; }
            QListWidget::item:selected { background-color: #6272a4; color: #ffffff; }
        """)

        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        self.date_box = QComboBox()
        top_layout.addWidget(self.date_box)

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon(":/imgs/icons/bin.png"))
        self.delete_btn.setIconSize(QSize(24, 24))
        self.delete_btn.setFixedSize(32, 32)
        top_layout.addWidget(self.delete_btn)
        self.delete_btn.clicked.connect(self.delete_selected_file)

        layout.addLayout(top_layout)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(QSize(200, 200))
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setSpacing(10)
        layout.addWidget(self.list_widget)

        self.date_box.currentTextChanged.connect(self.load_images)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.load_dates()

    # -----------------------------
    # Load images
    # -----------------------------
    def load_dates(self):
        if not self.base_dir.exists(): return
        dates = [f.name for f in self.base_dir.iterdir() if f.is_dir()]
        dates.sort(reverse=True)
        self.date_box.clear()
        self.date_box.addItems(dates)
        if dates:
            self.load_images(dates[0])

    def load_images(self, date_str):
        self.list_widget.clear()
        date_dir = self.base_dir / date_str
        if not date_dir.exists(): return
        for file in sorted(date_dir.iterdir()):
            if file.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
                pixmap = QPixmap(str(file))
                if not pixmap.isNull():
                    item = QListWidgetItem(file.stem)
                    item.setIcon(QIcon(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
                    self.list_widget.addItem(item)

    # -----------------------------
    # Double-click → emit image
    # -----------------------------
    def on_item_double_clicked(self, item: QListWidgetItem):
        date_str = self.date_box.currentText()
        supported_exts = [".png", ".jpg", ".jpeg", ".bmp", ".gif"]
        file_path = None
        for ext in supported_exts:
            path = self.base_dir / date_str / (item.text() + ext)
            if path.exists():
                file_path = path
                break
        if file_path:
            pixmap = QPixmap(str(file_path))
            if not pixmap.isNull():
                self.image_selected.emit(pixmap)
                print(f"Emitted image from {file_path}")
                self.close()

    # -----------------------------
    # Delete image
    # -----------------------------
    def delete_selected_file(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items: return
        item = selected_items[0]
        file_name = item.text()
        date_str = self.date_box.currentText()
        supported_exts = [".png", ".jpg", ".jpeg", ".bmp", ".gif"]
        file_path = None
        for ext in supported_exts:
            path = self.base_dir / date_str / (file_name + ext)
            if path.exists():
                file_path = path
                break
        if not file_path: return
        confirm_dialog = ConfirmDialog(f"Do you really want to delete '{file_path.name}'?", self)
        if confirm_dialog.exec() == QDialog.Accepted:
            file_path.unlink()
            self.load_images(date_str)
