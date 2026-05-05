from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QObject, Slot, Signal
from serial import SerialException

from src.serial_manager import SerialManager
from src.motor_manager import MotorManager
from src.config_manager import ConfigManager
from src.motor_position_poller import MotorPositionPoller
from src.ui.pop_up import PopUp

class ApplicationManager(QObject):
    """
    Sorgt für das zusammenspiel von allen Managern und der UI
    """
    motors_scan_completed = Signal(list)
    build_motor_page = Signal(object)

    def __init__(self, window):
        super().__init__()
        self.main_window = window
        self.pop_up = PopUp()
        self.config_manager = ConfigManager()

        self.serial_manager = SerialManager()
        self.motor_manager = MotorManager(self.serial_manager, self.config_manager)
        self.motor_position_poller = MotorPositionPoller()

        # --- Signals between UI and Backend

        self.main_window.ui.connect_btn.clicked.connect(self.connect_to_motors)
        self.main_window.ui.enable_all_btn.clicked.connect(self.motor_manager.enable_all)
        self.main_window.ui.enable_all_btn2.clicked.connect(self.motor_manager.enable_all)
        self.main_window.ui.disable_all_btn.clicked.connect(self.motor_manager.disable_all)
        self.main_window.ui.disable_all_btn2.clicked.connect(self.motor_manager.disable_all)
        self.main_window.confirm_btn_created.connect(self.dummy_func) # Wenn Ich UI Refactore: So machen, dass UI Pages vorab erstellt werden, und nur per Signal nötiges erhalten
        

        # --- Signals between MotorManager and ApplikationManager ---

        self.motor_manager.motor_position.connect(self.on_position_update)

        # --- Signal between ApplicationManager and MotorPositionPoller

        self.motors_scan_completed.connect(self.motor_position_poller.set_motor_ids)

        # --- Signale zwischen MotorPositionManager und MotorManager

        self.motor_position_poller.poll_motor.connect(self.motor_manager.get_motor_position)

        # --- Signale für Comport Page ---

        self.serial_manager.exception_received.connect(self.on_exception_received)
        self.motor_manager.scan_completed.connect(self.on_scan_completed)
        self.build_motor_page.connect(self.main_window._setup_motor_page)

        # --- Signals for ConfigManager ---

        self.config_manager.key_error.connect(self.on_key_error_received)
        self.config_manager.integrity_error.connect(self.on_integrity_check_failed)

    def test(self):
        print("Cool")

    @Slot(QPushButton)
    def dummy_func(self, confirm_btn):
        confirm_btn.clicked.connect(self.on_confirm_btn_clicked)

    def connect_to_motors(self):
        """Connect to serial port and scan for motors"""
        serial_settings = self.main_window.get_connection_settings()

        if self.serial_manager.thread and self.serial_manager.thread.isRunning():
            self.serial_manager.thread.wait(100)

        self.motor_manager.motors.clear()  

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
        
    def shutdown(self):
        """Stop background work before the application exits."""
        print("Shutting down application")
        self.motor_manager.disable_all()
        self.motor_position_poller.stop_polling()
        self.serial_manager.close_connection()
        
    def steps_to_unit(self, motor_id, steps) -> float:
        ''' Connverts steps to mm/degree'''
        encoder: str = self.config_manager.get_value(motor_id, 'Hardware_Info', 'Available_Encoder')
        pos_factor = float(self.config_manager.get_value(motor_id, 'Software_Config', 'Gear_Factor'))

        if encoder == "1":
            unit = float((steps / 2000) * 360 * pos_factor)
        else:
            unit = float((steps / 3200) * 360 * pos_factor)

        return unit
    
    def unit_to_steps(self, motor_id: int, unit: float) -> int:
        '''Converts the given mm/degree to steps'''
        encoder: str = self.config_manager.get_value(motor_id, 'Hardware_Info', 'Available_Encoder')
        pos_factor = float(self.config_manager.get_value(motor_id, 'Software_Config', 'Gear_Factor'))

        if encoder:
            steps = int(( unit / (360 * pos_factor) ) * 2000)
        else:
            steps = int(( unit / (360 * pos_factor) ) * 3200)

        return  steps
        
    @Slot()
    def on_scan_completed(self):
        """Handle when motor scanning is completed."""
        print("Motor scan completed")

        # Get motor IDs that were found during scanning
        scanned_motor_ids = list(self.motor_manager.motors.keys())
        print(f"Found {len(scanned_motor_ids)} motors during scan: {scanned_motor_ids}")
        self.build_motor_page.emit(self.motor_manager.motors) # Rows generated = amount of found motors
        self.motors_scan_completed.emit(scanned_motor_ids)

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

    @Slot()
    def on_position_update(self, motor_id, position):
        """Handle individual motor position updates"""
        print(f"Motor {motor_id} position: {position}")
        # Update UI with individual position
        label_dict = self.main_window.label_dict
        unit = self.steps_to_unit(motor_id, position)

        if motor_id in label_dict.keys():
            label_dict.get(motor_id).setText(str(unit))
        else:
            return

    @Slot()
    def on_confirm_btn_clicked(self):
        input_dict = self.main_window.input_position
        real_input_dict = {k: v for k,v in input_dict.items() if len(v.text()) != 0}    # Only not empty input

        for key, value in real_input_dict.items():
            position = value.text()
            unit_pos = self.unit_to_steps(key, float(position))
            self.motor_manager.move_motor(key, unit_pos)
