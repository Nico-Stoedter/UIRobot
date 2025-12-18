import math

from ini_manager import IniManager

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motor import Motor
    from motor_manager import MotorManager

class TeleskopArm: 
    def __init__(self, motor_manager: "MotorManager", r1_motor_id, r3_motor_id):
        self.manager = motor_manager
        self.ini_manager = IniManager()
        self.r1_motor_id = r1_motor_id
        self.r3_motor_id = r3_motor_id
    
    def r1_movement(self, r1_pos: int) -> None:
        ''' Retruns message for regular r1 movement'''
        r1 = self.manager.motors.get(self.r1_motor_id)
        r3 = self.manager.motors.get(self.r3_motor_id)
        r1_cur_pos = r1.get_motor_pos()
        r3_cur_pos = r3.get_motor_pos()

        # --- Calculation of Corresponding r3 Movement ---
        r1_spd_steps = max(-32768, min(int(r1.max_speed / 60 * 2000), 32767))
        r1_rotation_time = (r1_pos - r1_cur_pos) / r1_spd_steps 

        r1_one_round = (360 / (360 * r1.position_factor)) * 2000
        r1_relative_rounds = (r1_pos - r1_cur_pos) / r1_one_round

        r3_pos_steps = r1_relative_rounds * 2000
        r3_spd_stp = r3_pos_steps / r1_rotation_time

        msg = f"ADR={self.r1_motor_id};SPD{r1_spd_steps};QEC{r1_pos};"
        msg += f"ADR={self.r3_motor_id};SPD{int(r3_spd_stp)};ORG{int(-r3_pos_steps) + r3_cur_pos};QEC{r3_cur_pos};"

        self.manager.transport.write(msg.encode('utf-8'), True)
    
    def r3_movement(self, spd) -> None:
        '''Sends message for r3 motor and saves new org for dual r1_r3 movement'''
        motor = self.manager.motors.get(self.r3_motor_id)
        spd_rpm = motor.max_speed

        # --- Calculating deadzone --- #ToDo checken, ob sowas überhaupt nötig ist
        spd_stepps = max(-32768, min(int(spd_rpm / 60 * 2000), 32767))
        deadzone = int(spd_stepps * 0.1)

        # --- Construct Message ---
        if spd < -deadzone:
            min_pos = motor.min_position
            steps_min_pos = self.manager.unit_to_steps(self.r3_motor_id, min_pos)

            self.manager.set_current_motor_direction(motor, steps_min_pos)

            msg = f'ADR={self.r3_motor_id};SPD{spd};QEC{steps_min_pos};'

        elif spd > deadzone:
            max_pos = motor.max_position
            steps_max_pos = self.manager.unit_to_steps(self.r3_motor_id, max_pos)

            self.manager.set_current_motor_direction(motor, steps_max_pos)

            msg = f'ADR{self.r3_motor_id};SPD{spd};QEC{steps_max_pos};'
        else:
            if motor.cur_rotation_dir:
                msg = f'ADR={self.r3_motor_id};SPD0;STP-1;'
            else:
                msg = f'ADR={self.r3_motor_id};SPD0;STP1;'
            
        self.manager.transport.write(msg.encode('utf-8'), True)

    def dual_r1_r3_controller(self, spd) -> None:
        '''Writes message for r1 and r3 movements and ORG for r3'''
        r1 = self.manager.motors.get(self.r1_motor_id)
        pos_factor = r1.position_factor

        # spd == r1 absolute speed
        r1_spd_rel = int(spd * pos_factor)

        # --- Calculate deadzone --- 
        spd_rpm: float = r1.max_speed
        spd_stepps = max(-32768, min(int(spd_rpm / 60 * 2000), 32767))
        deadzone = int(spd_stepps * 0.1)

        # --- Construct Message ---
        if spd < -deadzone and (r1.cur_rotation_dir == None or r1.cur_rotation_dir): 
                min_pos_r1 = r1.min_position
                steps_min_pos_r1 = self.manager.unit_to_steps(self.r1_motor_id, min_pos_r1)

                self.manager.set_current_motor_direction(r1, steps_min_pos_r1)

                msg = f'ADR={self.r1_motor_id};SPD{spd};QEC{steps_min_pos_r1};'
                msg += f'ADR={self.r3_motor_id};SPD{r1_spd_rel};QEC{steps_min_pos_r1};'

        elif spd > deadzone and (r1.cur_rotation_dir == None or not(r1.cur_rotation_dir)): 
            max_pos_r1 = r1.max_position
            steps_max_pos = self.manager.unit_to_steps(self.r1_motor_id, max_pos_r1)

            self.manager.set_current_motor_direction(r1, steps_max_pos)

            msg = f'ADR={self.r1_motor_id};SPD{spd};QEC{steps_max_pos};'
            msg += f'ADR={self.r3_motor_id};SPD{r1_spd_rel};QEC{steps_max_pos};'
        else:
            # Stop, if spd in deadzone
            stop_step = "-1" if r1.cur_rotation_dir is True else "1"
            msg = f"ADR={self.r1_motor_id};SPD0;STP{stop_step};"
            msg += f"ADR={self.r3_motor_id};SPD0;STP{stop_step};"
            r1.cur_rotation_dir = None  # reset so next move can start either way

        self.manager.transport.write(msg.encode('utf-8'), True)
    
class RotTranMotor:
    def __init__(self, motor_manager: "MotorManager", rot_motor_id, trn_motor_id):
        self.manager = motor_manager
        self.ini_manager = IniManager()
        self.rot_mtr_id = rot_motor_id # Is 72 (if nothing has changed)
        self.trn_mtr_id = trn_motor_id # Is 73 (if nothing has changed)
        self.rot_movement_type = "None" # None -> Nothing; limited -> current positon with 1.8 correction; regular -> full 360

    def rot_tran_movement(self, id: int, input: float|int, controller: bool) -> None:
        '''Creates the message for rot/trn movement for manual and controller'''
        self.CUIDTRot3R = RotationTypes(self.manager)

        rot_mtr = self.manager.motors.get(self.rot_mtr_id)
        trn_mtr = self.manager.motors.get(self.trn_mtr_id)

        rot_pos_stp = rot_mtr.get_motor_pos()
        trn_pos_stp = trn_mtr.get_motor_pos()

        input_stp_regular = self.manager.unit_to_steps(id, input)

        rot_pos_degree = self.manager.steps_to_unit(self.rot_mtr_id, rot_pos_stp)
        trn_pos_mm = self.manager.steps_to_unit(self.trn_mtr_id, trn_pos_stp)

        trn_mtr_ena = trn_mtr.motor_status.get("ena")

        one_round_stp = self.manager.unit_to_steps(self.rot_mtr_id, 360)
        one_round_unit = self.manager.steps_to_unit(self.rot_mtr_id, one_round_stp)

        if controller: # With controller, input is a spd_stp value
            rot_spd_stp = input if id == self.rot_mtr_id else 0
            trn_spd_stp = input if id == self.trn_mtr_id else 0 

            if input > 0:   # input now converted to the max/min value of motor
                input_unit_joystick = rot_mtr.max_position if id == self.rot_mtr_id else trn_mtr.max_position
            else:
                input_unit_joystick = rot_mtr.min_position if id == self.rot_mtr_id else trn_mtr.min_position
        else:
            rot_spd_stp = max(-32768, min(int(rot_mtr.max_speed / 60 * 2000), 32767))
            trn_spd_stp = max(-32768, min(int(trn_mtr.max_speed / 60 * 2000), 32767))

            # I work with values from 0° - 720° for type 3/4 rotation to avoid negativ values 
            target_stp = input_stp_regular + one_round_stp
            trn_one_round = self.manager.unit_to_steps(self.trn_mtr_id, 360)
            real_input = input + 360

            if (rot_pos_stp - trn_one_round) <= target_stp:
                offset_degree = (real_input - rot_pos_degree) * trn_mtr.position_factor
            else:
                offset_degree = (real_input - (rot_pos_degree - 360)) * trn_mtr.position_factor

            # Offset is the ORG value for trn_mtr during the regular type 3/4
            offset =  -1 * self.manager.unit_to_steps(self.trn_mtr_id, offset_degree)

        msg = ""

        if rot_mtr and trn_mtr:
            if (trn_pos_mm < 0.1) and (rot_mtr.dev_type == 2):
                # rot_mtr back to regular rotation mode
                print("rot normal")
                rot_mtr.dev_type = 3
                rot_mtr.min_position = 0
                rot_mtr.max_position = 720
            if  (trn_pos_mm >= 5) and (trn_mtr_ena == 1) and (rot_mtr.dev_type == 3):
                # rot_mtr to limited rotation mode
                print("rot limited")
                rot_mtr.dev_type = 2
                rot_mtr.min_position = rot_pos_degree - 1.8 - one_round_unit
                rot_mtr.max_position = rot_pos_degree + 1.8 - one_round_unit
            if (id == self.rot_mtr_id) and (trn_mtr_ena == 1) and (rot_mtr.dev_type == 3): 
                # trn_mtr OFF for regular rotation
                print("trn OFF")
                msg += f"ADR={self.trn_mtr_id};OFF;"
                trn_mtr_ena = 0
            if (id == self.trn_mtr_id): 
                # --- trn_mtr movement ---
                if controller:
                    qec = self.manager.unit_to_steps(self.trn_mtr_id, input_unit_joystick)
                    if trn_pos_stp < 5:
                        print("min-max wieder normal")
                        rot_mtr.min_position = 0
                        rot_mtr.max_position = 360
                else:
                    qec = input_stp_regular
                    if input < 0.1: 
                        print("min-max wieder normal")
                        rot_mtr.min_position = 0
                        rot_mtr.max_position = 360      

                msg += f"ADR={self.trn_mtr_id};ENA;"
                msg += f"SPD{trn_spd_stp};QEC{qec};" 
            if (id == self.rot_mtr_id) and (trn_pos_mm < 0.1) and (trn_mtr_ena == 0) and (rot_mtr.dev_type == 3):
                # --- Regular rot_mtr Type 3/4 Movement ---
                if controller:
                    msg += self.CUIDTRot3R.rotation_type_3_4_controller(rot_mtr, rot_spd_stp)
                else:
                    msg += f"ADR={self.trn_mtr_id};ORG{offset};"
                    msg += self.CUIDTRot3R.type_3_4_rotation(rot_mtr, input)
            if ((id == self.rot_mtr_id) and (trn_pos_mm < 0.1) and (rot_mtr.dev_type == 3) and (rot_spd_stp == 0)):
                # --- Regular rot_mtr Type 3/4 Movement with Controller ---
                msg += f"ADR={self.trn_mtr_id};ENA;ORG0;ADR={self.rot_mtr_id};STP1;"
                trn_mtr_ena = 1
            if (id == self.rot_mtr_id) and (trn_pos_mm >= 5) and (trn_mtr_ena == 1) and (rot_mtr.dev_type == 2):
                # --- Limited rot_mtr Rotation Movement with and without Controller---
                if controller:
                    input_unit = rot_mtr.max_position if rot_spd_stp > 0 else rot_mtr.min_position
                    print(input_unit)
                    input_stp_joystick = self.manager.unit_to_steps(self.rot_mtr_id, input_unit)
                    msg += f"ADR={self.rot_mtr_id};SPD{rot_spd_stp};QEC{input_stp_joystick + one_round_stp};"
                else:
                    if not(self.manager.range_check(rot_mtr, input)):
                        return
                    msg += f"ADR={self.rot_mtr_id};SPD{rot_spd_stp};QEC{input_stp_regular + one_round_stp};"

        self.manager.transport.write(msg.encode('utf-8'), True)

class RotationTypes: #ToDo Kommentare einfügen
    def __init__(self, motor_manager: "MotorManager"):
        self.manager = motor_manager

    def type_3_4_rotation(self, motor: "Motor", target: float) -> str: # Namen ändern -ToDo
        '''Returns a message for a type 3/4 rotation. Functin does a regular type 3 rotation 
        and to enable type 4 rotation change direction in .ini file'''
        cur_pos_stp = motor.get_motor_pos()
        motor_id = motor.id
        motor_spd_rpm = motor.max_speed
        motor_spd_stp = max(-32768, min(int(motor_spd_rpm / 60 * 2000), 32767))
        target_stp = self.manager.unit_to_steps(motor_id, target)

        one_round = self.manager.unit_to_steps(motor_id, 360)

        # I work with values from 0° - 720° and modulo for type 3/4 rotation to avoid negativ values
        if (cur_pos_stp - one_round) <= target_stp:
            msg = f"ADR={motor_id};SPD{motor_spd_stp};QEC{target_stp + one_round};"
        else:
            msg = f"ADR={motor_id};ORG{cur_pos_stp - one_round};SPD{motor_spd_stp};QEC{one_round + target_stp};"

        return msg
    
    def rotation_type_3_4_controller(self, motor: "Motor", spd: int) -> str:
        '''Returns message for type 3/4 rotation with controller'''
        cur_pos_stp = motor.get_motor_pos()
        motor_id = motor.id
        motor_spd_stp = spd

        one_round = self.manager.unit_to_steps(motor_id, 360)
        org_stp = cur_pos_stp % one_round

        msg = ""

        if spd < 0:
            return msg
        
        msg += f"ADR={motor_id};ORG{org_stp};SPD{motor_spd_stp};QEC{one_round*100};"

        return msg
    
class XYLimitedMotors: #ToDo Kommentare einfügen; ausfürhlich testen
    def __init__(self, motor_manager: "MotorManager", x_motor_id, y_motor_id):
        self.manager = motor_manager
        self.x_motor_id = x_motor_id
        self.y_motor_id = y_motor_id

    def x_y_controller_movement(self, axis_x, axis_y, gradual_spd_x, gradual_spd_y) -> None: # ToDo Gründlich checken
        '''Writes a message for special X/Y controller movemet'''
        x_motor = self.manager.motors.get(self.x_motor_id)
        y_motor = self.manager.motors.get(self.y_motor_id)
        
        x_pos_steps = x_motor.get_motor_pos()
        y_pos_steps = y_motor.get_motor_pos()

        x_pos = self.manager.steps_to_unit(self.x_motor_id, x_pos_steps)
        y_pos = self.manager.steps_to_unit(self.y_motor_id, y_pos_steps)

        # --- Need to match spd if gearfactor is different ---
        if gradual_spd_x >= gradual_spd_y:
            gradual_spd_y = int(gradual_spd_x * 20)
        else:
            gradual_spd_x = int(gradual_spd_y / 20)

        # --- Circular Motion ---
        # Does a simple predicition to avoid crossing limits
        if axis_x > 0:
            predicted_x_pos = x_pos + 0.1
        elif axis_x < 0:
            predicted_x_pos = x_pos - 0.1
        else:
            predicted_x_pos = x_pos

        if axis_y > 0:
            predicted_y_pos = y_pos + 0.1
        elif axis_y < 0:
            predicted_y_pos = y_pos - 0.1
        else:
            predicted_y_pos = y_pos

        predicted_distance = math.sqrt(predicted_x_pos**2 + predicted_y_pos**2)

        max_pos = x_motor.max_position

        if predicted_distance > max_pos:
            print("Out of range") # Debug
            return
    
        x_max_mm = x_motor.max_position
        y_max_mm = y_motor.max_position

        x_max_stp = self.manager.unit_to_steps(self.x_motor_id, x_max_mm)
        y_max_stp = self.manager.unit_to_steps(self.y_motor_id, y_max_mm)

        x_stp = math.copysign(x_max_stp, axis_x)
        y_stp = math.copysign(y_max_stp, axis_y)

        if axis_x < 0.1 and axis_x > -0.1:
            x_stp = x_pos_steps
        if axis_y < 0.1 and axis_y > -0.1:
            y_stp = y_pos_steps

        # --- Construct Message ---
        msg = f"ADR={self.x_motor_id};SPD{gradual_spd_x};QEC{int(x_stp)};"
        msg += f"ADR={self.y_motor_id};SPD{gradual_spd_y};QEC{int(y_stp)};"

        self.manager.transport.write(msg.encode('utf-8'), True)

        

