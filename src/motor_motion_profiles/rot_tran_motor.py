from src.config_manager import ConfigManager

class RotTranMotor:
    def __init__(self, rot_motor_id, trn_motor_id, parent=None):
        self.manager = parent
        self.ini_manager = ConfigManager()
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