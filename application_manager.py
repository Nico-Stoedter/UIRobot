from PySide6.QtCore import QObject, Slot, Signal
from serial import SerialException

from src.serial_manager import SerialManager
from src.motor_manager import MotorManager
from src.config_manager import ConfigManager
from src.ui.pop_up import PopUp

class ApplicationManager(QObject):
    """
    Sorgt für das zusammenspiel von allen Managern und der UI
    """

    build_motor_page = Signal(object)

    def __init__(self, window):
        super().__init__()
        self.main_window = window
        self.pop_up = PopUp()
        self.config_manager = ConfigManager()

        self.serial_manager = SerialManager()
        self.motor_manager = MotorManager(self.serial_manager, self.config_manager)

        # --- Signale für Comport Page ---

        self.main_window.ui.connect_btn.clicked.connect(self.connect_to_motors)
        self.serial_manager.exception_received.connect(self.on_exception_received)
        self.motor_manager.scan_completed.connect(self.on_scan_completed)
        self.build_motor_page.connect(self.main_window._setup_motor_page)

        # --- Signals for ConfigManager ---

        self.config_manager.key_error.connect(self.on_key_error_received)
        self.config_manager.integrity_error.connect(self.on_integrity_check_failed)

    def connect_to_motors(self):
        """Connect to serial port and scan for motors"""
        serial_settings = self.main_window.get_connection_settings()

        # Kurz warten, bis der Thread sicher fertig ist,
        # oder timeout‑sicher machen
        if self.serial_manager.thread and self.serial_manager.thread.isRunning():
            self.serial_manager.thread.wait(100)

        # Connect to serial port
        success, message = self.serial_manager.open_connection(
            serial_settings['port'],
            serial_settings['baud']
        )

        if success:
            print(f"Serial connection successful: {message}")
            # Start motor scanning
            self.motor_manager.scan_motors()
            return True
        else:
            return False
        
    @Slot()
    def on_scan_completed(self):
        """Handle when motor scanning is completed."""
        print("Motor scan completed")

        # Get motor IDs that were found during scanning
        scanned_motor_ids = list(self.motor_manager.motors.keys())
        print(f"Found {len(scanned_motor_ids)} motors during scan: {scanned_motor_ids}")
        self.build_motor_page.emit(self.motor_manager.motors) # Rows generated = amount of found motors

    @Slot(Exception)
    def on_exception_received(self, exception):
        if isinstance(exception, SerialException):
            self.pop_up.show_popup(["Port möglicherweise besetzt"])

    @Slot(str)
    def on_key_error_received(self, key: str):
        self.pop_up.show_popup([f"{key} not found. Ini might be wrong formated"])

    @Slot(list)
    def on_integrity_check_failed(self, errors: list[str]):
        self.pop_up.show_popup(errors)

        