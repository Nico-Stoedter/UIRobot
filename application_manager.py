from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QObject, Slot, Signal
from serial import SerialException

from src.serial_manager import SerialManager
from src.motor_manager import MotorManager
from src.config_manager import ConfigManager
from src.motor_position_poller import MotorPositionPoller
from src.joystick_manager import JoystickManager
from src.ui.pop_up import PopUp
from src.ui.toast import Toast

class ApplicationManager(QObject):
    """
    Sorgt für das zusammenspiel von allen Managern und der UI
    """
    motors_scan_completed = Signal(list)
    build_motor_page = Signal(object)
    read_axis_motor_pairs = Signal(dict)

    def __init__(self, window):
        super().__init__()
        self.main_window = window
        self.pop_up = PopUp()
        self.toast = Toast(self.main_window)
        self.config_manager = ConfigManager()

        self.serial_manager = SerialManager()
        self.motor_manager = MotorManager(self.serial_manager, self.config_manager)
        self.motor_position_poller = MotorPositionPoller()
        self.joystick_manager = JoystickManager()

        # --- Test ---

        self.joystick_manager.create_pop_up.connect(self.pop_up.show_popup)

        # --- UI Singals ---
        self.main_window.ui.connect_btn.clicked.connect(self.connect_to_motors)
        self.main_window.ui.enable_all_btn.clicked.connect(self.motor_manager.enable_all)
        self.main_window.ui.enable_all_btn2.clicked.connect(self.motor_manager.enable_all)
        self.main_window.ui.disable_all_btn.clicked.connect(self.motor_manager.disable_all)
        self.main_window.ui.disable_all_btn2.clicked.connect(self.motor_manager.disable_all)      
        self.main_window.motor_page_created.connect(self.on_motor_page_created)
        self.main_window.reset_page_created.connect(self.on_reset_page_created) 
        
        self.pop_up.pop_up_created.connect(self.joystick_manager.pop_up_created)
        self.pop_up.pop_up_closed.connect(self.joystick_manager.pop_up_closed)

        # --- MotorManager Signals ---
        self.motor_manager.motor_position.connect(self.on_position_update)
        self.motor_manager.scan_completed.connect(self.on_scan_completed)

        # --- ApplicationManager Signals ---
        self.motors_scan_completed.connect(self.motor_position_poller.set_motor_ids)
        self.build_motor_page.connect(self.main_window._setup_motor_page)
        self.read_axis_motor_pairs.connect(self.joystick_manager.receive_axis_motor_pairs)

        # --- MotorPositionPoller Signals ---
        self.motor_position_poller.poll_motor.connect(self.motor_manager.get_motor_position)

        # --- SerialManager Signals ---
        self.serial_manager.exception_received.connect(self.on_exception_received)

        # --- ConfigManager Signals ---
        self.config_manager.key_error.connect(self.on_key_error_received)
        self.config_manager.integrity_error.connect(self.on_integrity_check_failed)

        # --- JoystickManager Signals
        self.joystick_manager.send_joystick_movement.connect(self.process_joystick_movement)

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
    
    def range_check(self, input_dict: dict) -> bool:
        for motor_id, unit_pos in input_dict.items():
            motor = self.motor_manager.motors.get(motor_id)

            if not (motor.min_pos <= unit_pos <= motor.max_pos):
                self.toast.show_toast(f"Motor {motor_id} Input out of Range")
                return True

        return False
    
    def get_all_joy_axis_motor_pairs(self, motor_ids) -> dict[int, int]:
        axis_motor_dict = {}

        for id in motor_ids:
            motor = self.motor_manager.motors.get(id)
            joy_axis = motor.joy_axis
            axis_motor_dict[joy_axis] = id

        return axis_motor_dict
    
    def truncate(self, value: float, n: int) -> str:
        return f"{value:.{n}f}"
    
    @Slot(tuple)
    def process_joystick_movement(self, movement_data: tuple[int, float]) -> None:
        motor_id = movement_data[0]
        motor = self.motor_manager.motors.get(motor_id)
        joy_deflection = movement_data[1]
        deadzone = motor.joy_deadzone
        spd_pps = motor.spd_pps
        spd_factor = self.joystick_manager.spd_factor   # Is 1 If RB not Pressed 2 Otherwise
        joy_spd = int((spd_pps * joy_deflection) / 2)   # Max half the Config spd if RB not Pressed

        # Deadzone
        if joy_deflection <= deadzone and joy_deflection >= -deadzone:
            self.joystick_manager.moving_motor[motor_id] = False
            self.motor_manager.move_motor_joy(motor_id, 0)
            return
        
        self.joystick_manager.moving_motor[motor_id] = True
        self.motor_manager.move_motor_joy(motor_id, joy_spd)
        
    @Slot()
    def on_scan_completed(self):
        """Handle when motor scanning is completed."""
        print("Motor scan completed")

        # Get motor IDs that were found during scanning
        scanned_motor_ids = list(self.motor_manager.motors.keys())
        axis_motor_pairs = self.get_all_joy_axis_motor_pairs(scanned_motor_ids)

        print(f"Found {len(scanned_motor_ids)} motors during scan: {scanned_motor_ids}")

        self.build_motor_page.emit(self.motor_manager.motors)     
        self.read_axis_motor_pairs.emit(axis_motor_pairs)
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
        """Handle individual motor position updates for Reset and Motor Page"""
        motor = self.motor_manager.motors.get(motor_id)
        unit = motor.unit

        motor_page_labels = self.main_window.label_dict
        reset_page_labels = self.main_window.duplicate_label_dict
        pos_unit = self.steps_to_unit(motor_id, position)
        pos_unit = self.truncate(pos_unit, 2)

        if motor_id in motor_page_labels.keys():
            motor_page_labels.get(motor_id).setText(str(pos_unit) + unit)
            reset_page_labels.get(motor_id).setText(str(pos_unit) + unit)
        else:
            return

    def on_confirm_btn_clicked(self):
        input_dict = {
            motor_id: float(widget.text())
            for motor_id, widget in self.main_window.input_position.items()
            if widget.text().strip()
        }

        if self.range_check(input_dict):
            return

        for motor_id, unit_pos in input_dict.items():
            stp = self.unit_to_steps(motor_id, unit_pos)
            self.motor_manager.move_motor(motor_id, stp)

    def on_reset_btn_clicked(self):
        input_dict = {
            motor_id: float(widget.text())
            for motor_id, widget in self.main_window.input_reset.items()
            if widget.text().strip()
        }

        for motor_id, unit_pos in input_dict.items():
            stp = self.unit_to_steps(motor_id, unit_pos)
            self.motor_manager.reset_position(motor_id, stp)

    @Slot(QPushButton)
    def on_motor_page_created(self, confirm_btn):
        confirm_btn.clicked.connect(self.on_confirm_btn_clicked)
    
    @Slot(QPushButton)
    def on_reset_page_created(self, reset_btn):
        reset_btn.clicked.connect(self.on_reset_btn_clicked)
