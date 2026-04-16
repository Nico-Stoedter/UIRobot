# omnivac/ui/views/motor_view.py
from typing import TYPE_CHECKING, Dict
from PySide6.QtWidgets import QLineEdit, QLabel, QComboBox
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator

if TYPE_CHECKING:
    from omnivac.ui.generated.sidebar import Ui_MainWindow
    from omnivac.core.motor import Motor

class MotorView:
    """Verwaltet die Motor-Page UI"""
    
    def __init__(self, ui: "Ui_MainWindow"):
        self.ui = ui
        
        # UI-Element Referenzen
        self.input_position: Dict[int, QLineEdit] = {}
        self.label_dict: Dict[int, QLabel] = {}
        self.label_name_dict: Dict[int, QLabel] = {}
        
        # Validator für Eingaben
        regex = QRegularExpression(r"^-?[0-9.]*$")
        self.validator = QRegularExpressionValidator(regex)
    
    def clear(self):
        """Leert alle Widget-Referenzen"""
        self.input_position.clear()
        self.label_dict.clear()
        self.label_name_dict.clear()
    
    def update_position_label(self, motor_id: int, text: str):
        """Aktualisiert das Position-Label für einen Motor"""
        label = self.label_dict.get(motor_id)
        if label:
            label.setText(text)
    
    def get_input_values(self) -> Dict[int, str]:
        """Gibt alle eingegebenen Werte zurück"""
        return {
            motor_id: widget.text() 
            for motor_id, widget in self.input_position.items()
        }
    
    def clear_inputs(self):
        """Leert alle Eingabefelder"""
        for widget in self.input_position.values():
            widget.setText("")