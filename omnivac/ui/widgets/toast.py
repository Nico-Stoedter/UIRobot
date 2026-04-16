from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QTimer, QPoint

class Toast(QLabel):
    def __init__(self, message, parent=None, duration=2000):
        super().__init__(message, parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(100, 100, 100, 180);
                color: black;
                padding: 16px 16px;
                border-radius: 8px;
                font-size: 32px;
            }
        """)
        self.adjustSize()

        QTimer.singleShot(duration, self.close)

    def show_at(self, position: QPoint):
        self.move(position)
        self.show()