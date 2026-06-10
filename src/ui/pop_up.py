from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Signal, QObject, Slot

class PopUp(QObject):

    pop_up_closed = Signal()
    pop_up_created = Signal()

    def __init__(self):
        super().__init__()
        self.msg_box = None 

    @Slot(list)
    def show_popup(self, messages: list[str]):
        if isinstance(messages, list):
            message = "\n".join(messages)   # jede Zeichenfolge als eigene Zeile
        else:
            message = messages

        if self.msg_box is not None and self.msg_box.isVisible():
            return 
        
        self.pop_up_created.emit()

        self.msg_box = QMessageBox()
        self.msg_box.setWindowTitle("Info Box")
        
        self.msg_box.setText(message)

        self.msg_box.finished.connect(self._on_popup_closed)
        self.msg_box.exec()

    def _on_popup_closed(self):
        self.msg_box = None
        self.pop_up_closed.emit()

    def is_visible(self) -> bool:
        """True if pop-up active"""
        return self.msg_box is not None and self.msg_box.isVisible()