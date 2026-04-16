# omnivac/ui/views/reset_view.py
from typing import TYPE_CHECKING, Dict
from PySide6.QtWidgets import QLineEdit, QLabel

if TYPE_CHECKING:
    from omnivac.ui.generated.sidebar import Ui_MainWindow

class ResetView:
    """Verwaltet die Reset-Page UI"""
    
    def __init__(self, ui: "Ui_MainWindow"):
        self.ui = ui
        
        # UI-Element Referenzen
        self.input_reset: Dict[int, QLineEdit] = {}
        self.duplicate_label_dict: Dict[int, list[QLabel]] = {}
    
    def clear(self):
        """Leert alle Widget-Referenzen"""
        self.input_reset.clear()
        self.duplicate_label_dict.clear()
    
    def get_reset_values(self) -> Dict[int, str]:
        """Gibt alle eingegebenen Reset-Werte zurück"""
        return {
            motor_id: widget.text() 
            for motor_id, widget in self.input_reset.items()
            if widget.text() != ""
        }
    
    def clear_inputs(self):
        """Leert alle Eingabefelder"""
        for widget in self.input_reset.values():
            widget.setText("")
    
    def update_position_labels(self, motor_id: int, text: str):
        """Aktualisiert die duplizierten Position-Labels"""
        duplicate_labels = self.duplicate_label_dict.get(motor_id, [])
        for label in duplicate_labels:
            label.setText(text)