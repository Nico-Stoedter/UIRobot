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

import math

class ApplicationManager(QObject):
    """
    Sorgt für das zusammenspiel von allen Managern und der UI
    """
    motors_scan_completed = Signal(list)
    build_motor_page = Signal(object)       # Object -> dict[]
    read_axis_motor_pairs = Signal(object)  # Object -> dict[int, int]
    motors_settings = Signal()              # Sends the config settings to the motor
    motor_hardware_info = Signal()          # Sends the hardware info to the config file

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

        self.security_requests = {} # dict[motor_id, list[security_txt]]

        # --- Motion Profiles ---
        self.x_motor_id = 74
        self.y_motor_id = 75

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
        self.motor_manager.motor_ena.connect(self.on_motor_enabled)
        self.motor_manager.motor_off.connect(self.on_motor_disabled)
        self.motor_manager.motor_starts_moving.connect(self._on_motor_starts_moving)
        self.motor_manager.motor_finished_moving.connect(self._on_motor_finished_moving)
        self.motor_manager.pop_up_request.connect(self.process_pop_up_request)
        self.motor_manager.hardware_info.connect(self.config_manager.write_hardware_info)

        # --- ApplicationManager Signals ---
        self.motors_scan_completed.connect(self.motor_position_poller.set_motor_ids)
        self.build_motor_page.connect(self.main_window._setup_motor_page)
        self.read_axis_motor_pairs.connect(self.joystick_manager.receive_axis_motor_pairs)
        self.motors_settings.connect(self.motor_manager.set_motor_settings)
        self.motor_hardware_info.connect(self.motor_manager.get_hardware_info)

        # --- MotorPositionPoller Signals ---
        self.motor_position_poller.poll_motor.connect(self.motor_manager.get_motor_position)

        # --- SerialManager Signals ---
        self.serial_manager.exception_received.connect(self.on_exception_received)

        # --- ConfigManager Signals ---
        self.config_manager.key_error.connect(self.on_key_error_received)
        self.config_manager.integrity_error.connect(self.process_pop_up_request)

        # --- JoystickManager Signals
        self.joystick_manager.send_joystick_movement.connect(self.process_joystick_movement)
        self.joystick_manager.layout_changed.connect(self.change_joystick_layout_ui)

    def test(self):
        print("Cool")

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

            if not (motor.min_pos_unit <= unit_pos <= motor.max_pos_unit):
                self.toast.show_toast(f"Motor {motor_id} Input out of Range")
                return True

        return False
    
    def process_x_y_workspace(self, x_joy_deflection, y_joy_deflection):
            x_motor = self.motor_manager.motors.get(self.x_motor_id)
            max_value = x_motor.max_pos_stp
            max_spd = x_motor.spd_pps / 2

            length = math.sqrt(x_joy_deflection**2 + y_joy_deflection**2)

            if length > 1.0:
                x_joy_deflection /= length
                y_joy_deflection /= length
                length = 1.0

            spd = int(length * max_value)

            qec_x = int(x_joy_deflection * max_value)
            qec_y = int(y_joy_deflection * max_value)

            self.motor_manager.move_motor_joy(self.x_motor_id, spd, qec_x)
            self.motor_manager.move_motor_joy(self.y_motor_id, spd, qec_y)
    
    def get_all_joy_axis_motor_pairs(self, motor_ids) -> dict[int, int]:
        axis_motor_dict = {}

        for id in motor_ids:
            motor = self.motor_manager.motors.get(id)
            joy_axis = motor.joy_axis
            axis_motor_dict[joy_axis] = id

        return axis_motor_dict
    
    def truncate(self, value: float, n: int) -> str:
        return f"{value:.{n}f}"
    
    @Slot(bool)
    def change_joystick_layout_ui(self, layout) -> None:
        name_label_dict = self.main_window.label_name_dict

        for motor_id, label in name_label_dict.items():
            motor = self.motor_manager.motors.get(motor_id)
            joystick_axis = motor.joy_axis

            print(motor.joy_axis)
            if layout:
                if joystick_axis > 5:
                    label.setStyleSheet("color: yellow;")
                else:
                    label.setStyleSheet("color: white;")
            else:
                if joystick_axis < 6:
                    label.setStyleSheet("color: yellow;")
                else:
                    label.setStyleSheet("color: white;")

    
    @Slot(int)
    def _on_motor_starts_moving(self, controller_id):
        motor = self.motor_manager.motors.get(controller_id)

        if motor.status["ena"] == 1:
            self.main_window.change_pixmap(controller_id, "blau.png")

    @Slot(tuple)
    def _on_motor_finished_moving(self, tuple: tuple[int, str]) -> None:
        """
        Manages events that should occure when motor finishes moving
        tupel[motor_id, command]
        """
        motor_id = tuple[0]
        command = tuple[1]
        motor = self.motor_manager.motors.get(motor_id)

        if motor.status["ena"] == 1:  
            self.main_window.change_pixmap(motor_id, "gruen.png")

        if motor_id in self.security_requests and command == "qec":
            request = self.security_requests.get(motor_id)
            self.security_requests.pop(motor_id)
            self.motor_manager.stop_all()
            self.pop_up.show_popup(request)
            
    
    @Slot(int)
    def on_motor_enabled(self, controller_id) -> None:
        motor = self.motor_manager.motors.get(controller_id)

        if motor.status["ena"] == 0:
            self.main_window.change_pixmap(controller_id, "gruen.png")

    @Slot(int)
    def on_motor_disabled(self, controller_id) -> None:
        motor = self.motor_manager.motors.get(controller_id)

        if motor.status["ena"] == 1:
            self.main_window.change_pixmap(controller_id, "rot.png")
    
    @Slot(object)
    def process_joystick_movement(self, movement_data: dict[int, float]) -> None:
        """
        Handles and Processes User Joystick Inputs
        """
        input_dict = {}

        # IDs for the XYMotorWorkspace
        x_motor_id = self.x_motor_id    
        y_motor_id = self.y_motor_id

        # Only in Special Cases like in XYMotorWorkspace() movement_data has more than 1 item
        for motor_id, joy_deflection in movement_data.items(): 
            motor = self.motor_manager.motors.get(motor_id)
            deadzone = motor.joy_deadzone
            spd_pps = motor.spd_pps
            joy_spd = int((spd_pps * joy_deflection) / 2)   # Max half the Config spd if RB not Pressed
            max_pos_unit = motor.max_pos_unit
            min_pos_unit = motor.min_pos_unit

            # Deadzone
            if joy_deflection <= deadzone and joy_deflection >= -deadzone:
                self.joystick_manager.moving_motor[motor_id] = False
                self.motor_manager.move_motor_joy(motor_id, 0)
                self._on_motor_finished_moving((motor_id, "spd"))
                continue

            if motor_id in [x_motor_id, y_motor_id]:
                x_movement = movement_data[x_motor_id]
                y_movement = movement_data[y_motor_id]
                self.joystick_manager.moving_motor[x_motor_id] = True
                self.joystick_manager.moving_motor[y_motor_id] = True
                self.process_x_y_workspace(x_movement, y_movement)
                continue
        
            self.joystick_manager.moving_motor[motor_id] = True

            if joy_spd > 0:
                unit = max_pos_unit
            elif joy_spd < 0:
                unit = min_pos_unit

            input_dict[motor_id] = unit
            input_dict = self.security_positions_check(input_dict)
            unit = input_dict.get(motor_id)
            qec = self.unit_to_steps(motor_id, unit)

            self.motor_manager.move_motor_joy(motor_id, joy_spd, qec)
        
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
        self.motors_settings.emit()
        self.motor_hardware_info.emit()
        self.change_joystick_layout_ui(False)   # False because intial layout ist axis 1-5

    @Slot(Exception)
    def on_exception_received(self, exception):
        if isinstance(exception, SerialException):
            self.pop_up.show_popup(["Port möglicherweise besetzt"])

    @Slot(str)
    def on_key_error_received(self, key: str):
        self.pop_up.show_popup([f"{key} not found. Ini might be wrong formated"])

    @Slot(list)
    def process_pop_up_request(self, message: list[str]) -> None:
        self.pop_up.show_popup(message)

    @Slot()
    def on_position_update(self, motor_id, position):
        """Handle individual motor position updates for Reset and Motor Page"""
        motor = self.motor_manager.motors.get(motor_id)
        dev_type = motor.dev_type
        unit = motor.unit

        motor_page_labels = self.main_window.label_dict
        reset_page_labels = self.main_window.duplicate_label_dict
        pos_unit = self.steps_to_unit(motor_id, position)

        if dev_type == 2:
            pos_unit %= 360

        pos_unit = self.truncate(pos_unit, 2)

        if motor_id in motor_page_labels.keys():
            motor_page_labels.get(motor_id).setText(str(pos_unit) + unit)
            reset_page_labels.get(motor_id).setText(str(pos_unit) + unit)
        else:
            return

    def on_confirm_btn_clicked(self):
        """
        Handles and Processes the User Input
        """
        # Get all not empty input fields
        input_dict = {
            motor_id: float(widget.text())
            for motor_id, widget in self.main_window.input_position.items()
            if widget.text().strip()
        }

        if self.range_check(input_dict):
            return
        
        input_dict = self.security_positions_check(input_dict)

        stp_input_dict = {} # dict[motor_id: int, stp: int]

        for motor_id, unit_pos in input_dict.items():
            stp = self.unit_to_steps(motor_id, unit_pos)
            stp_input_dict[motor_id] = stp

        self.motor_manager.move_motor(stp_input_dict)

    def security_positions_check(self, input_dict) -> dict[int, float]:
        """ 
        Returns a dict mapping motor_id to the target position (float) that lies immediately 
        before the next configured security point along the motor's current travel direction
        """
        new_input_dict = input_dict.copy()

        for motor_id, target in input_dict.items():
            motor = self.motor_manager.motors.get(motor_id)
            dev_type = motor.dev_type
            cur_pos_stp = motor.status["rEncoder"]
            start = self.steps_to_unit(motor_id, cur_pos_stp)
            direction = True if target >= start else False
            security_pos: dict[tuple[float, bool], str] = motor.security_pos
            
            candidates = [pos for (pos, dir), _ in security_pos.items() if dir == direction]

            if dev_type in [1,2]:
                tol = 2     # Degree
            else:
                tol = 0.2   # mm
            
            on_path_candidates = [pos for pos in candidates if self.on_path(start, pos, target, tol)]

            if on_path_candidates:
                # Wähle den Kandidaten mit minimaler Entfernung vom Start
                next = min(on_path_candidates, key=lambda pos: abs(pos - start))
                new_input_dict[motor_id] = next
                security_txt = security_pos.get((next, direction))
                self.security_requests[motor_id] = [security_txt]
                
        return new_input_dict
    
    def on_path(self, start, pos, target, tol=0.0) -> bool:
        if start <= target:
            return (start + tol) <= pos <= target
        else:
            return target <= pos <= (start - tol)

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
