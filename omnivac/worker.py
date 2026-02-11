import math

from PySide6.QtCore import (Signal, Slot,QThread, 
                            QObject)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motor import Motor
    from motor_manager import MotorManager

class Worker(QObject):
    update_signal = Signal(int, str)
    popup_signal = Signal(str)
    stop_motor_signal = Signal(int)
    x_y_popup_sent = False

    def __init__(self, motor_manager: "MotorManager", motors: dict[int, "Motor"]):
        super().__init__()
        self.motor_manager = motor_manager
        self.motors: dict[int, "Motor"] = motors
        self.running = True

        # Set to remember, which motors triggered a pop-up
        self.triggered_motors = set()
        self.last_pos: dict[int, None|float] = {motor_id: None for motor_id in motors}
        self.last_time = 0

    def truncate(self, value: float, n: int) -> str:
        return f"{value:.{n}f}"

    @Slot()
    def run(self):
        '''Starts a thread which manages QEC; requests, security_postion defined in .ini'''
        while self.running:
            for motor_id, motor in self.motors.items():
                self.motor_manager.request_motor_position(motor_id)
                cur_pos = motor.get_motor_pos()
                unit_pos = float(self.truncate(self.motor_manager.steps_to_unit(motor_id, cur_pos), 3))          

                if motor.dev_type in [2,3,4]:
                    unit_pos = round(unit_pos % 360, 3)

                if motor_id in [74,75]: # real-time range check for special x/y 
                    if self.check_x_y_movement(cur_pos, motor_id):
                        if not self.x_y_popup_sent:
                            self.popup_signal.emit("x and y motors out of range")
                            self.stop_motor_signal.emit(74)
                            self.stop_motor_signal.emit(75)
                            self.x_y_popup_sent = True
                    else:
                        self.x_y_popup_sent = False

                if unit_pos == -0.0: # To avoid -0.0 in GUI 
                    unit_pos = 0.0

                unit_pos = self.truncate(self.motor_manager.steps_to_unit(motor_id, cur_pos), 3) 

                text = f"{unit_pos} {motor.position_unit}"

                self.check_security_pos(motor, motor_id, float(unit_pos))

                self.update_signal.emit(motor_id, text)


    def check_x_y_movement(self, cur_pos, motor_id) -> bool:
        '''Checks the special x/y movement in real time and returns a False if boundary crossed'''
        x_motor = self.motors.get(74)
        y_motor = self.motors.get(75)

        x_pos_stp = cur_pos if motor_id == 74 else x_motor.get_motor_pos()
        y_pos_stp = cur_pos if motor_id == 75 else y_motor.get_motor_pos()

        x_pos_mm = self.motor_manager.steps_to_unit(74, x_pos_stp)
        y_pos_mm = self.motor_manager.steps_to_unit(75, y_pos_stp)

        circular_range = math.sqrt(x_pos_mm**2 + y_pos_mm**2)

        if circular_range > x_motor.max_position:
            return True
        
        return False

    def check_security_pos(self, motor: "Motor", motor_id, unit_pos: float) -> None:
        sec_pos_true = motor.security_pos_true
        sec_pos_false = motor.security_pos_false

        last = self.last_pos.get(motor_id)

        # --- Bewegungsrichtung
        if last is None:
            movement_positive = None
        else:
            delta = unit_pos - last
            movement_positive = None if delta == 0 else delta > 0
        
        # --- Security-Dictionary auswählen
        if movement_positive is True:
            sec_dict = sec_pos_true
        elif movement_positive is False:
            sec_dict = sec_pos_false
        else:
            sec_dict = {}

        motor_rpm = motor.max_speed
        motor_spd = max(-32768, min(int(motor_rpm / 60 * 2000), 32767))
        motor_gear = motor.position_factor
        tolerance_steps = motor_spd * 0.2  # 0.2 -> thread_rate + aprox. execute time + aprox. jitter
        tolerance = max(2.0, (tolerance_steps * motor_gear * 360 / 2000))

        in_tolerance = False
        for pos, txt, dir_flag in sec_dict.values():
            if abs(unit_pos - pos) < tolerance:
                in_tolerance = True
                # Pop-up if motor not triggered and direction correct
                if (motor_id not in self.triggered_motors) and ((dir_flag and movement_positive) or (not dir_flag and not movement_positive)):
                    self.stop_motor_signal.emit(motor_id)
                    self.popup_signal.emit(txt)
                    self.triggered_motors.add(motor_id)
        
        # If motor outside of tolerance, reset triggered motor
        if not in_tolerance and motor_id in self.triggered_motors and movement_positive != None:
            self.triggered_motors.remove(motor_id)

        self.last_pos[motor_id] = unit_pos

    def stop(self):
        self.running = False # Signal to GUI

    def get_security_pos(self, motor) -> list[float]:
        '''Gets all Security Position from the motor .ini'''
        security_setting: dict[int, list[float, str, bool]] = motor.security_settings
        security_value_list: list[float] = []

        if security_setting == {}:
            return []

        for value in security_setting.values(): 
            security_value_list.append(value[0])

        return security_value_list
    
    def get_security_text(self, motor) -> list[str]:
        '''Gets the text displayed for its Security Positions from the .ini'''
        security_setting: dict[int, list[float, str, bool]] = motor.security_settings
        security_text_list: list[float] = []

        if security_setting == {}:
            return []
        
        for value in security_setting.values(): 
            security_text_list.append(value[1])

        return security_text_list
    
    def get_security_dir(self, motor) -> list[str]:
        '''Gets the movement direction in which the Security Position message should be displayed'''
        security_setting: dict[int, list[float, str, bool]] = motor.security_settings
        security_dir_list: list[float] = []

        if security_setting == {}:
            return []
        
        for value in security_setting.values(): 
            security_dir_list.append(value[2])

        return security_dir_list
    