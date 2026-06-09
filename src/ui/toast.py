from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtWidgets import QLabel

class Toast(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
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

    def show_at(self, position: QPoint):
        self.move(position)
        self.show()

    def show_toast(self, text: str, duration=4000) -> None:
        self.setText(text)
        self.adjustSize()

        margin = 20
        parent = self.parentWidget()

        parent_rect = parent.rect()
        x = parent_rect.width() - self.width() - margin
        y = parent_rect.height() - self.height() - margin
        self.move(parent.mapToGlobal(QPoint(x, y)))
        self.show()

        QTimer.singleShot(duration, self.hide)