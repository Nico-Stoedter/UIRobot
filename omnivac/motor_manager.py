from motor import Motor
from ini_manager import IniManager
from special_motor import (TeleskopArm, RotTranMotor, RotationTypes,
                            XYLimitedMotors)
from pop_up import PopUp
from RS232 import RS232

import interpreter
import time
import math
import ccd

class MotorManager:
    """Verwaltet Motoren und deren Logik, nutzt RS232 als Transport."""

    def __init__(self, transport: RS232):
        self.transport = transport
        self.ini_manager = IniManager()
        self.motors: dict[int, Motor] = {}
        self.pop_up = PopUp()

        self.x_motor_id = 74
        self.y_motor_id = 75
        self.x_y_motors = XYLimitedMotors(self, self.x_motor_id, self.y_motor_id)

        self.r1_motor_id = 70
        self.r3_motor_id = 71
        self.special_motor = TeleskopArm(self, self.r1_motor_id, self.r3_motor_id)

        self.rot_motor_id = 72
        self.trn_motor_id = 73
        self.rot_tran_motor = RotTranMotor(self, self.rot_motor_id, self.trn_motor_id)

        self.rotation_types = RotationTypes(self)

    # --- Functions for Checking User Input ---

    def range_check(self, motor: "Motor", val: float) -> bool:
        '''Checks if input between min_pos, max_pos ''' 
        if val < motor.min_position or val > motor.max_position:
            return False
        
        return True 
    
    def x_y_movement_check(self, motor: "Motor", input, other_id: int, other_input: str) -> bool:
        '''Checks if x/y movement is in sqrt(x**2 + y**2)'''
        other_motor = self.motors.get(other_id)

        if other_input == "":
            other_motor_steps = other_motor.get_motor_pos()
            other_motor_unit = self.steps_to_unit(other_id, other_motor_steps)
            combined_range = math.sqrt(input**2 + other_motor_unit**2)
        else:
            combined_range = math.sqrt(input**2 + float(other_input)**2)

        if combined_range > motor.max_position + 0.01:
            return True
        else:
            return False
        
    def ccd_check(self, input_position) -> None: # Todo muss noch getestet werden
        '''collison predictin before movement'''
        x_motor = self.motors.get(5)
        y_motor = self.motors.get(6)
        z_motor = self.motors.get(7)

        x_motor_start_steps = x_motor.get_motor_pos()
        y_motor_start_steps = y_motor.get_motor_pos()
        z_motor_start_steps = z_motor.get_motor_pos()

        x_motor_start = self.steps_to_unit(5, x_motor_start_steps)
        y_motor_start = self.steps_to_unit(6, y_motor_start_steps)
        z_motor_start = self.steps_to_unit(7, z_motor_start_steps)

        # Get target positin of x,y,z
        widget_x = self.input_position.get(5)
        widget_y = self.input_position.get(6)
        widget_z = self.input_position.get(7)

        try:
            target_pos_x = float(widget_x.text())
        except ValueError:
            target_pos_x = x_motor_start
                
        try:
            target_pos_y = float(widget_y.text())
        except ValueError:
            target_pos_y = y_motor_start
                
        try:
            target_pos_z = float(widget_z.text())
        except ValueError:
            target_pos_z = z_motor_start

        # Get motor speed
        x_motor_speed = float(x_motor.max_speed)
        y_motor_speed = float(y_motor.max_speed)
        z_motor_speed = float(z_motor.max_speed)

        coll = ccd.calc_collision((x_motor_start, y_motor_start, z_motor_start),
                                    (target_pos_x, target_pos_y, target_pos_z), 
                                    (x_motor_speed, y_motor_speed, z_motor_speed))
                    
        if coll[0]:
            self.pop_up.show_popup(f"Collision with Security Zone: {coll[1]}")
            return 
    
    # --- Function for Motor Communication ---

    def request_motor_feedback(self) -> None:
        '''Broadcasts FBK message'''
        msg  = f'ADR=127;FBK;'
        self.transport.write(msg.encode('utf-8'), True)

    def enable_motors(self) -> None:
        '''Emitts ENA message for all motors'''
        for id in self.motors:
            msg = f'ADR={id};ENA;'
            self.transport.write(msg.encode('utf-8'), True)

    def disable_motors(self) -> None:
        '''Emitts OFF message for all motors'''
        if self.r3_motor_id in self.motors:
            # org positin needs to be safed
            r3_motor = self.motors.get(self.r3_motor_id)
            org_r3 = r3_motor.r3_org_pos
            self.ini_manager.update_org_value(self.r3_motor_id, org_r3)

        for id in self.motors:
            msg = f'ADR={id};OFF;'
            self.transport.write(msg.encode('utf-8'), True)

    def request_motor_position(self, motor_id) -> None:
        '''Ask current motor position'''
        motor = self.motors.get(motor_id)

        if motor != None:
            if motor.encoder:
                msg = f"ADR={motor_id};QEC;"
            else:
                msg = f"ADR={motor_id};POS;"

            self.transport.write(msg.encode('utf-8'), False)

        while self.transport.in_waiting > 0:
            data = self.transport.read_until(b'\xff')

            if data:
                # Data interpretation and updating motor status
                header, controller_id, message_id, data_bytes, terminator = interpreter.get_message(data)
                results = interpreter.interpret_data(header, message_id, data_bytes)
                motor = self.motors.get(controller_id)

                if motor != None:
                    motor.update_status(results)

                if controller_id == self.r3_motor_id and self.special_motor != None:
                    if motor.r3_org_pos == None:
                        motor.r3_org_pos = results.get("rEncoder")
            else:
                print("[MotorManager] WARNING: Received empty data packet")
        else:
            results = {}

        return results

    def stop_motors(self) -> None:
        ''' Stops motor movement'''
        for id, motor in self.motors.items(): # Depending on current rotation STP needs to 1 or -1
            if motor.cur_rotation_dir:
                msg = f'ADR={id};STP-1;'
            elif motor.cur_rotation_dir == None:
                msg = f'ADR={id};STP1;' 
            else:
                msg = f'ADR={id};STP1;'
            self.transport.write(msg.encode('utf-8'), True)

    def send_ORG(self, id, input) -> None:
        input = self.unit_to_steps(id, float(input))
        msg = f'ADR={id};ORG{input};'

        if id == self.r3_motor_id:
            r3_motor = self.motors.get(id)
            r3_motor.r3_org_pos = input

        self.transport.write(msg.encode('utf-8'), True)

    def check_feedback_addresses(self) -> dict[int, Motor]:
        '''Searches for connected addresses'''
        self.motors.clear()
        feedback_addresses = {}
        self.request_motor_feedback()
        time.sleep(0.2)

        while self.transport.in_waiting > 0:
            data = self.transport.read_until(b'\xff')

            if data:
                header, controller_id, message_id, data_bytes, terminator = interpreter.get_message(data)
                results = interpreter.interpret_data(header, message_id, data_bytes)

                if header == 'CC':
                    self.ini_manager.check_existing_ini(controller_id)
                    motor = Motor(controller_id, results)
                    feedback_addresses[controller_id] = motor
                    motor.update_status(results)
                    self.motors.update({controller_id: motor})

        return dict(sorted(feedback_addresses.items()))

    def read_message(self):
        '''Intepreted the answers of the motor'''
        results = {}

        while self.transport.in_waiting > 0:
            data = self.transport.read_until(b'\xff')

            if data:
                header, controller_id, message_id, data_bytes, terminator = interpreter.get_message(data)
                results = interpreter.interpret_data(header, message_id, data_bytes)
                motor = self.motors.get(controller_id)

                if motor != None:
                    motor.update_status(results)
            else:
                print("[MotorManager] WARNING: Received empty data packet")

        return results

    def unit_to_steps(self, motor_id: int, unit: float) -> int:
        '''Converts the given mm/degree to steps'''
        motor = self.motors.get(motor_id)
        encoder = motor.encoder
        pos_factor = motor.position_factor

        if encoder:
            steps = int(( unit / (360 * pos_factor) ) * 2000)
        else:
            steps = int(( unit / (360 * pos_factor) ) * 3200)

        return  steps
    
    def steps_to_unit(self, motor_id: int, steps: float) -> float:
        ''' Connverts steps to mm/degree'''
        motor = self.motors.get(motor_id)
        encoder = motor.encoder
        pos_factor = motor.position_factor

        if encoder:
            unit = float((steps / 2000) * 360 * pos_factor)
        else:
            unit = float((steps / 3200) * 360 * pos_factor)

        return  unit
    
    def move_normal(self, id: int, input: float) -> None:
        '''Regular motor movement without controller'''
        motor = self.motors.get(id)
        spd_rpm = motor.max_speed
        spd_steps = max(-32768, min(int(spd_rpm / 60 * 2000), 32767))
        encoder = motor.encoder
        position_steps = self.unit_to_steps(id, float(input))

        self.set_current_motor_direction(motor, position_steps)

        if motor.dev_type in [3,4]:
            msg = self.rotation_types.right_rotation(motor, input)
            return msg

        if encoder: 
            msg = f'ADR={id};SPD{spd_steps};QEC{position_steps};'
        else:
            msg = f'ADR={id};SPD{spd_steps};POS{position_steps};'

        self.transport.write(msg.encode('utf-8'), True)
    
    def move_motor(self, id: int, input: float) -> None:
        '''Moves motor(id) with QEC(input); command and with in .ini defined speed'''
        position_steps = self.unit_to_steps(id, float(input)) 

        if id == self.r3_motor_id:
            r3_motor = self.motors.get(id)
            r3_motor.r3_org_pos = position_steps
            self.move_normal(id, input)

        elif id == self.r1_motor_id:
            self.special_motor.r1_movement(position_steps)

        elif id in [self.rot_motor_id, self.trn_motor_id]:
            self.rot_tran_motor.rot_tran_movement(id, input, False)

        else:
            self.move_normal(id, input)

    def controller_movement(self, axis_x, axis_y, motor_speeds: dict[int, int]) -> None:
        '''Manages movement with controller'''

        # ---- X/Y EINMALIG behandeln ----
        if 5 in motor_speeds or 6 in motor_speeds:
            spd_x = motor_speeds.get(5)
            spd_y = motor_speeds.get(6)

            self.x_y_controller_movement(spd_x, spd_y)

            # Danach aus dem Dict entfernen
            motor_speeds.pop(5, None)
            motor_speeds.pop(6, None)

        for motor_id, spd in motor_speeds.items():
            msg = ""

            if motor_id == self.r1_motor_id: # R1 movement
                r1_spd = motor_speeds.get(self.r1_motor_id)
                self.special_motor.dual_r1_r3_controller(r1_spd)

                if r1_spd == 0:
                    time.sleep(0.1)
                    r3_motor = self.motors.get(self.r3_motor_id)
                    org_r3 = r3_motor.r3_org_pos
                    msg += f"ADR={self.r3_motor_id};ORG{org_r3};"

                    self.transport.write(msg.encode('utf-8'), True)

            elif motor_id == self.r3_motor_id: #Todo Wenn möglich all das stable count Zeug weg
                r3_spd = motor_speeds.get(self.r3_motor_id)
                self.special_motor.r3_movement(r3_spd)

                if r3_spd == 0:
                    r3_motor = self.motors.get(self.r3_motor_id)

                    last_pos = r3_motor.get_motor_pos()
                    stable_count = 0
                    max_stable = 25  # Anzahl aufeinanderfolgender "keine Änderung", bevor wir abbrechen

                    while True:
                        cur_pos = r3_motor.get_motor_pos()

                        if cur_pos != last_pos:
                            # Encoder hat sich bewegt -> ORG updaten
                            r3_motor.r3_org_pos = cur_pos
                            last_pos = cur_pos
                            stable_count = 0
                        else:
                            # Keine Bewegung
                            stable_count += 1
                            if stable_count >= max_stable:
                                r3_motor.r3_org_pos = cur_pos
                                break  # Encoder stabil -> fertig

            elif motor_id in [self.rot_motor_id, self.trn_motor_id]: # rot/trn movement
                spd = (motor_speeds.get(self.rot_motor_id) 
                        if motor_id == self.rot_motor_id 
                        else motor_speeds.get(self.trn_motor_id))
                self.rot_tran_motor.rot_tran_movement(motor_id, spd, True)  

            elif motor_id in [self.x_motor_id, self.y_motor_id]: # special x/y movement
                spd_x = motor_speeds.get(self.x_motor_id)
                spd_y = motor_speeds.get(self.y_motor_id)
                self.x_y_motors.x_y_controller_movement(axis_x, axis_y, spd_x, spd_y)
            else:
                if motor_id != None:
                    self.standard_controller_movement(motor_id, spd) 

            if msg != "":
                self.transport.write(msg.encode('utf-8'), True)

    def x_y_controller_movement(self, spd_x, spd_y):
        '''Manages movement for regular x/y axis'''
        motor_x = self.motors.get(5)
        motor_y = self.motors.get(6)

        x_min_pos_stp = self.unit_to_steps(5, motor_x.min_position)
        x_max_pos_stp = self.unit_to_steps(5, motor_x.max_position)

        y_min_pos_stp = self.unit_to_steps(6, motor_y.min_position)
        y_max_pos_stp = self.unit_to_steps(6, motor_y.max_position)

        if spd_x < -200:
            x_direction = x_min_pos_stp
        elif spd_x > 200:
            x_direction = x_max_pos_stp
        else:
            x_direction = 0

        if spd_y < -200:
            y_direction = y_min_pos_stp
        elif spd_y > 200:
            y_direction = y_max_pos_stp
        else:
            y_direction = 0

        msg = f"ADR=5;SPD{spd_x};QEC{x_direction};ADR=6;SPD{spd_y};QEC{y_direction};"
        self.transport.write(msg.encode('utf-8'), True)

    def standard_controller_movement(self, motor_id: int, spd: float) -> None: # Todo wie message generiert werden kann man bestimmt verbessern
        '''Handles regular controller movement'''
        motor = self.motors.get(motor_id)
        encoder = motor.encoder
        min_pos = motor.min_position
        max_pos = motor.max_position

        if spd < 0:
            steps_min_pos = self.unit_to_steps(motor_id, min_pos)
            self.set_current_motor_direction(motor, steps_min_pos)

            if encoder:
                msg = f'ADR={motor_id};SPD{spd};QEC{steps_min_pos};'
            else:
                msg = f'ADR={motor_id};SPD{spd};POS{steps_min_pos};'

        elif spd > 0:
            steps_max_pos = self.unit_to_steps(motor_id, max_pos)
            self.set_current_motor_direction(motor, steps_max_pos)

            if encoder:
                msg = f'ADR={motor_id};SPD{spd};QEC{steps_max_pos};'
            else:
                msg = f'ADR={motor_id};SPD{spd};POS{steps_max_pos};'

        else:
            if motor.cur_rotation_dir:
                msg = f'ADR={motor_id};SPD0;STP-1;'
            else:
                msg = f'ADR={motor_id};SPD0;STP1;'
            
        self.transport.write(msg.encode('utf-8'), True)

    def start_config_motor(self, id) -> None:
        motor = self.motors.get(id)
        mac = int(self.ini_manager.get_value(id, "Soft_Moti", "Acceleration_Rate(ms)"))
        mde = int(self.ini_manager.get_value(id, "Soft_Moti", "Deacceleration_Rate(ms)"))
        mms = int(self.ini_manager.get_value(id, "Soft_Moti", "Start_Speed(rpm)"))
        mmd = int(self.ini_manager.get_value(id, "Soft_Moti", "Stop_Speed(rpm)"))
        blc = int(self.ini_manager.get_value(id, "Soft_Moti", "Backlash_Compensation(p)"))
        cur = self.ini_manager.get_value(id, "Hard_Conf", "Phase_Current(A)").replace(".", "")
        acr = int(self.ini_manager.get_value(id, "Hard_Conf", "Current_Reduction(%)"))
        mcs = int(self.ini_manager.get_value(id, "Hard_Conf", "Micro_Stepping"))
        direction = self.ini_manager.get_value(id, "Hard_Conf", "Direction")

        if direction == "0":
            icf = 0
        else:
            icf = 2

        msg = f"ADR={id};ICF{icf};MAC{mac};MDE{mde};MMS{mms};MMD{mmd};BLC{blc};CUR{cur};ACR{acr};MCS{mcs};"

        if motor.dev_type in [3,4]:
            one_round = self.unit_to_steps(id, 360.0)
            msg += f"ORG{one_round};"

        self.transport.write(msg.encode("utf-8"), True)
        self.read_message()

    @staticmethod
    def set_current_motor_direction(motor: "Motor", pos: int) -> None:
        ''' If motor does a left rotation value is TRUE, and FALSE otherwise'''
        if int(pos) <  motor.get_motor_pos():
            motor.cur_rotation_dir = True
        else:
            motor.cur_rotation_dir = False