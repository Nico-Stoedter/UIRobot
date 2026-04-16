# omnivac/ui/views/connection_view.py
from typing import TYPE_CHECKING
from PySide6.QtCore import QTimer

if TYPE_CHECKING:
    from omnivac.ui.generated.sidebar import Ui_MainWindow

class ConnectionView:
    """Verwaltet die Connection-Page UI"""
    
    def __init__(self, ui: "Ui_MainWindow"):
        self.ui = ui
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialisiert die UI-Komponenten"""
        from omnivac.hardware.comports_manager import getActivePorts
        
        # ComboBoxen befüllen
        self.ui.combo_port.addItems(getActivePorts())
        self.ui.combo_baud.addItems(['9600', '14400', '19200', '38400', '57600', '115200'])
        self.ui.combo_byte.addItems(['8', '7', '6', '5'])
        self.ui.combo_parity.addItems(["None", 'Odd', 'Even', 'Mark', 'Space'])
        self.ui.combo_stop.addItems(['1', '1.5', '2'])
    
    def get_connection_settings(self) -> dict:
        """Gibt die aktuellen Connection-Einstellungen zurück"""
        return {
            'port': self.ui.combo_port.currentText(),
            'baud': self.ui.combo_baud.currentText(),
            'byte': self.ui.combo_byte.currentText(),
            'parity': self.ui.combo_parity.currentText(),
            'stop': self.ui.combo_stop.currentText()
        }
    
    def disable_connect_button_temporarily(self, milliseconds: int = 3000):
        """Deaktiviert den Connect-Button temporär"""
        self.ui.btn_connect.setEnabled(False)
        QTimer.singleShot(milliseconds, lambda: self.ui.btn_connect.setEnabled(True))