import math

from ini_manager import IniManager

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motor import Motor
    from motor_manager import MotorManager

class ConnectedMotors:
    def __init__(self, motor_manager: "MotorManager", r1_device_id, r3_device_id):
        self.manager = motor_manager
        self.ini_manager = IniManager()
        self.r1_device_id = r1_device_id
        self.r3_device_id = r3_device_id
    
    def r1_movement(self, r1_pos: int) -> str:
        r1 = self.manager.motors.get(self.r1_device_id)
        r3 = self.manager.motors.get(self.r3_device_id)
        r1_cur_pos = r1.get_motor_pos()
        r3_cur_pos = r3.get_motor_pos()

        r1_spd_steps = max(-32768, min(int(r1.max_speed / 60 * 2000), 32767))
        r1_rotation_time = (r1_pos - r1_cur_pos) / r1_spd_steps 

        r1_one_round = (360 / (360 * r1.position_factor)) * 2000
        r1_relative_rounds = (r1_pos - r1_cur_pos) / r1_one_round

        r3_pos_steps = r1_relative_rounds * 2000
        r3_spd_stp = r3_pos_steps / r1_rotation_time

        msg1 = f"ADR={self.r1_device_id};SPD{r1_spd_steps};QEC{r1_pos};"
        msg2 = f"ADR{self.r3_device_id};SPD{int(r3_spd_stp)};ORG{int(-r3_pos_steps) + r3_cur_pos};QEC{r3_cur_pos};"

        return msg1 + msg2
    
    def r3_movement(self, spd) -> None:
        '''Sends message for r3 motor and saves new org for dual r1_r3 movement'''
        motor = self.manager.motors.get(self.r3_device_id)
        spd_rpm = motor.max_speed
        spd_stepps = max(-32768, min(int(spd_rpm / 60 * 2000), 32767))
        deadzone = int(spd_stepps * 0.1)

        if spd < -deadzone:
            min_pos = motor.min_position
            steps_min_pos = self.manager.unit_to_steps(self.r3_device_id, min_pos)

            self.manager.set_current_motor_direction(motor, steps_min_pos)

            msg = f'ADR={self.r3_device_id};SPD{spd};QEC{steps_min_pos};'

        elif spd > deadzone:
            max_pos = motor.max_position
            steps_max_pos = self.manager.unit_to_steps(self.r3_device_id, max_pos)

            self.manager.set_current_motor_direction(motor, steps_max_pos)

            msg = f'ADR{self.r3_device_id};SPD{spd};QEC{steps_max_pos};'
        else:
            if motor.cur_rotation_dir:
                msg = f'ADR={self.r3_device_id};SPD0;STP-1;'
            else:
                msg = f'ADR={self.r3_device_id};SPD0;STP1;'
            
        self.manager.transport.write(msg.encode('utf-8'), True)

    def dual_r1_r3_controller(self, spd) -> None:
        '''Sends message for r1 and r3 movements and ORG for r3'''
        r1 = self.manager.motors.get(self.r1_device_id)
        pos_factor = r1.position_factor

        # spd == r1 absolute speed
        r1_spd_rel = int(spd * pos_factor)

        # Calculate deadzone 
        spd_rpm: float = r1.max_speed
        spd_stepps = max(-32768, min(int(spd_rpm / 60 * 2000), 32767))
        deadzone = int(spd_stepps * 0.1)

        if spd < -deadzone and (r1.cur_rotation_dir == None or r1.cur_rotation_dir): 
                min_pos_r1 = r1.min_position
                steps_min_pos_r1 = self.manager.unit_to_steps(self.r1_device_id, min_pos_r1)

                self.manager.set_current_motor_direction(r1, steps_min_pos_r1)

                msg1 = f'ADR={self.r1_device_id};SPD{spd};QEC{steps_min_pos_r1};'
                msg2 = f'ADR={self.r3_device_id};SPD{r1_spd_rel};QEC{steps_min_pos_r1};'

        elif spd > deadzone and (r1.cur_rotation_dir == None or not(r1.cur_rotation_dir)): 
            max_pos_r1 = r1.max_position
            steps_max_pos = self.manager.unit_to_steps(self.r1_device_id, max_pos_r1)

            self.manager.set_current_motor_direction(r1, steps_max_pos)

            msg1 = f'ADR={self.r1_device_id};SPD{spd};QEC{steps_max_pos};'
            msg2 = f'ADR={self.r3_device_id};SPD{r1_spd_rel};QEC{steps_max_pos};'
        else:
            # Stop, if spd in deadzone
            stop_step = "-1" if r1.cur_rotation_dir is True else "1"
            msg1 = f"ADR={self.r1_device_id};SPD0;STP{stop_step};"
            msg2 = f"ADR={self.r3_device_id};SPD0;STP{stop_step};"
            r1.cur_rotation_dir = None  # reset so next move can start either way

        msg = msg1 + msg2

        self.manager.transport.write(msg.encode('utf-8'), True)
    
class RotTranMotor:
    def __init__(self, motor_manager: "MotorManager"):
        self.manager = motor_manager
        self.ini_manager = IniManager()
        self.rot_dev_id = 72
        self.trn_dev_id = 73

    def rot_tran_movement(self, id: int, input: float|int, controller: bool) -> None:
        self.CUIDTRot3R = RotationTypes(self.manager)

        rot_dev = self.manager.motors.get(self.rot_dev_id)
        trn_dev = self.manager.motors.get(self.trn_dev_id)

        rot_pos_stp = rot_dev.get_motor_pos()
        trn_pos_stp = trn_dev.get_motor_pos()

        input_stp = self.manager.unit_to_steps(id, input)

        rot_pos_degree = self.manager.steps_to_unit(72, rot_pos_stp)
        trn_pos_mm = self.manager.steps_to_unit(73, trn_pos_stp)

        trn_dev_ena = trn_dev.motor_status.get("ena")

        one_round_stp = self.manager.unit_to_steps(self.rot_dev_id, 360)
        one_round_unit = self.manager.steps_to_unit(self.rot_dev_id, one_round_stp)

        if controller: # With controller, input should be a spd_stp value
            rot_spd_stp = input if id == 72 else 0
            trn_spd_stp = input if id == 73 else 0 

            if input > 0:   # input know converted to the max/min value of device
                input = rot_dev.max_position if id == 72 else trn_dev.max_position
            else:
                input = rot_dev.min_position if id == 72 else trn_dev.min_position
        else:
            rot_spd_stp = max(-32768, min(int(rot_dev.max_speed / 60 * 2000), 32767))
            trn_spd_stp = max(-32768, min(int(trn_dev.max_speed / 60 * 2000), 32767))

            ### Rot motor gefahrene QEC
            target_stp = input_stp + one_round_stp
            trn_one_round = self.manager.unit_to_steps(self.trn_dev_id, 360)
            real_input = input + 360

            print(real_input, rot_pos_degree)

            if (rot_pos_stp - trn_one_round) <= target_stp:
                offset_degree = (real_input - rot_pos_degree) * trn_dev.position_factor
            else:
                offset_degree = (real_input - (rot_pos_degree - 360)) * trn_dev.position_factor

            offset =  -1 * self.manager.unit_to_steps(73, offset_degree)

            print("OFFSET: ", offset)

        msg = ""

        if rot_dev and trn_dev:
            if (trn_pos_mm < 0.1) and (trn_dev_ena == 1) and (rot_dev.dev_type == 2):
                print("Activates regular Rotation") # rot_dev back to regular rotation
                rot_dev.dev_type = 3
                rot_dev.min_position = 0
                rot_dev.max_position = 720
            if  (trn_pos_mm > 5) and (trn_dev_ena == 1) and (rot_dev.dev_type == 3): # if trn extended allow tolerance rot movement
                print("Acitvates limited Rotation") # rot_dev to limited rotation
                rot_dev.dev_type = 2
                rot_dev.min_position = rot_pos_degree - 1.8 - one_round_unit
                rot_dev.max_position = rot_pos_degree + 1.8 - one_round_unit
            if (id == 72) and (trn_dev_ena == 1) and (rot_dev.dev_type == 3): # trn OFF if rot moves
                print("trn OFF")
                msg += "ADR=73;OFF;"
                trn_dev_ena = 0
            if (id == 73): # translation movement
                if controller:
                    if trn_pos_stp < 5:
                        print("min-max wieder normal")
                        rot_dev.min_position = 0
                        rot_dev.max_position = 360
                else:
                    if input < 0.1:
                        print("min-max wieder normal")
                        rot_dev.min_position = 0
                        rot_dev.max_position = 360

                msg += "ADR=73;ENA;"
                msg += f"ADR=73;SPD{trn_spd_stp};QEC{input_stp};"
            if (id == 72) and (trn_pos_mm < 0.1) and (trn_dev_ena == 0) and (rot_dev.dev_type == 3):
                # regular right rotation movement
                if controller:
                    msg += self.CUIDTRot3R.rotation_type_3_4_controller(rot_dev, rot_spd_stp)
                else:
                    msg += f"ADR=73;ORG{offset};"
                    msg += self.CUIDTRot3R.right_rotation(rot_dev, input)
            if (id == 72) and (trn_dev_ena == 0) and (rot_dev.dev_type == 3) and (rot_spd_stp == 0):
                print("ENA")
                msg += "ADR=73;ENA;ORG0;ADR=72;STP1;"
                trn_dev_ena = 1
            if (id == 72) and (trn_pos_mm > 5) and (trn_dev_ena == 1) and (rot_dev.dev_type == 2):
                # limited rotation movement
                if  rot_dev.min_position > input or rot_dev.max_position < input:
                    return msg
                
                msg += f"ADR=72;SPD{rot_spd_stp};QEC{input_stp + one_round_stp};"

        return msg

class RotationTypes:
    def __init__(self, motor_manager: "MotorManager"):
        self.manager = motor_manager

    def right_rotation(self, device: "Motor", target: float) -> str:# Namen ändern -ToDo
        cur_pos_stp = device.get_motor_pos()
        device_id = device.id
        device_spd_rpm = device.max_speed
        device_spd_stp = max(-32768, min(int(device_spd_rpm / 60 * 2000), 32767))
        target_stp = self.manager.unit_to_steps(device_id, target)

        one_round = self.manager.unit_to_steps(device_id, 360)

        if (cur_pos_stp - one_round) <= target_stp:
            msg = f"ADR={device_id};SPD{device_spd_stp};QEC{target_stp + one_round};"
        else:
            msg = f"ADR={device_id};ORG{cur_pos_stp - one_round};SPD{device_spd_stp};QEC{one_round + target_stp};"

        return msg
    
    def rotation_type_3_4_controller(self, device: "Motor", spd: int) -> str:
        cur_pos_stp = device.get_motor_pos()
        device_id = device.id
        device_spd_stp = spd

        one_round = self.manager.unit_to_steps(device_id, 360)
        org_stp = cur_pos_stp % one_round

        msg = ""

        if spd < 0:
            return msg
        
        msg += f"ADR={device_id};ORG{org_stp};SPD{device_spd_stp};QEC{one_round*100};"

        return msg
    
class XYDevices:
    def __init__(self, motor_manager: "MotorManager", x_device_id, y_device_id):
        self.manager = motor_manager
        self.x_device_id = x_device_id
        self.y_device_id = y_device_id

    def x_y_controller_movement(self, axis_x, axis_y, gradual_spd_x, gradual_spd_y) -> None:
        x_device = self.manager.motors.get(self.x_device_id)
        y_device = self.manager.motors.get(self.y_device_id)
        
        x_pos_steps = x_device.get_motor_pos()
        y_pos_steps = y_device.get_motor_pos()

        x_pos = self.manager.steps_to_unit(self.x_device_id, x_pos_steps)
        y_pos = self.manager.steps_to_unit(self.y_device_id, y_pos_steps)

        # --- Bewegung berechnen ---
        if gradual_spd_x >= gradual_spd_y:
            gradual_spd_y = int(gradual_spd_x * 20)
        else:
            gradual_spd_x = int(gradual_spd_y / 20)

        # --- Kreisbegrenzung ---
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

        max_pos = x_device.max_position

        if predicted_distance > max_pos:
            print("Out of range") # Debug
            return
    
        x_max_mm = x_device.max_position
        y_max_mm = y_device.max_position

        x_max_stp = self.manager.unit_to_steps(self.x_device_id, x_max_mm)
        y_max_stp = self.manager.unit_to_steps(self.y_device_id, y_max_mm)

        x_stp = math.copysign(x_max_stp, axis_x)
        y_stp = math.copysign(y_max_stp, axis_y)

        if axis_x < 0.1 and axis_x > -0.1:
            x_stp = x_pos_steps
        if axis_y < 0.1 and axis_y > -0.1:
            y_stp = y_pos_steps

        msg = f"ADR={self.x_device_id};SPD{gradual_spd_x};QEC{int(x_stp)};"
        msg += f"ADR={self.y_device_id};SPD{gradual_spd_y};QEC{int(y_stp)};"

        self.manager.transport.write(msg.encode('utf-8'), True)

        

