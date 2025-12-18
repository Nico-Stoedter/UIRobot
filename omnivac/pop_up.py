from PySide6.QtWidgets import (QMessageBox, QLabel, QWidget,
                               QVBoxLayout)

from PySide6.QtCore import Qt

class PopUp:
    def __init__(self):
        self.msg_box = None  

    def show_popup(self, message: str):
        # Only display pop-up if no other exist
        if self.msg_box is not None and self.msg_box.isVisible():
            return 

        self.msg_box = QMessageBox()
        self.msg_box.setWindowTitle("Info Box")
        
        # Own layout for pop-up
        text_widget = QWidget()
        v_layout = QVBoxLayout(text_widget)
        v_layout.setContentsMargins(50, 20, 50, 20)  
        v_layout.setSpacing(10)

        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        v_layout.addWidget(label)

        self.msg_box.layout().addWidget(text_widget, 0, 1, 1, 2)

        self.msg_box.finished.connect(self._on_popup_closed)
        self.msg_box.exec()

    def _on_popup_closed(self):
        self.msg_box = None

    def is_visible(self) -> bool:
        """True if pop-up active"""
        return self.msg_box is not None and self.msg_box.isVisible()