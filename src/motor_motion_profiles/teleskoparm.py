from src.config_manager import ConfigManager

class TeleskopArm: 
    def __init__(self, r1_motor_id, r3_motor_id, parent=None):
        self.manager = parent
        self.ini_manager = ConfigManager()
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

        # --- Construct Message ---
        if spd < 0:
            min_pos = motor.min_position
            steps_min_pos = self.manager.unit_to_steps(self.r3_motor_id, min_pos)

            self.manager.set_current_motor_direction(motor, steps_min_pos)

            msg = f'ADR={self.r3_motor_id};SPD{spd};QEC{steps_min_pos};'

        elif spd > 0:
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

        # --- Construct Message ---
        if spd < 0 and (r1.cur_rotation_dir == None or r1.cur_rotation_dir): 
                min_pos_r1 = r1.min_position
                steps_min_pos_r1 = self.manager.unit_to_steps(self.r1_motor_id, min_pos_r1)

                self.manager.set_current_motor_direction(r1, steps_min_pos_r1)

                msg = f'ADR={self.r1_motor_id};SPD{spd};QEC{steps_min_pos_r1};'
                msg += f'ADR={self.r3_motor_id};SPD{r1_spd_rel};QEC{steps_min_pos_r1};'

        elif spd > 0 and (r1.cur_rotation_dir == None or not(r1.cur_rotation_dir)): 
            max_pos_r1 = r1.max_position
            steps_max_pos = self.manager.unit_to_steps(self.r1_motor_id, max_pos_r1)

            self.manager.set_current_motor_direction(r1, steps_max_pos)

            msg = f'ADR={self.r1_motor_id};SPD{spd};QEC{steps_max_pos};'
            msg += f'ADR={self.r3_motor_id};SPD{r1_spd_rel};QEC{steps_max_pos};'
        else:
            # Stop, if spd = 0
            stop_step = "-1" if r1.cur_rotation_dir is True else "1"
            msg = f"ADR={self.r1_motor_id};SPD0;STP{stop_step};"
            msg += f"ADR={self.r3_motor_id};SPD0;STP{stop_step};"
            r1.cur_rotation_dir = None  # reset so next move can start either way

        self.manager.transport.write(msg.encode('utf-8'), True)