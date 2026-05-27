from PySide6.QtCore import QObject

class Motor(QObject):
    def __init__(self, motor_id, serial_manager, config_manager=None):
        super().__init__()
        self.motor_id = motor_id
        self.serial_manager = serial_manager
        self.config_manager = config_manager
        self.config_manager.check_existing_ini(self.motor_id)
        
        self.device_name = self.config_manager.get_value(self.motor_id, 'Software_Config', 'Device_Name')
        self.dev_type = int(self.config_manager.get_value(self.motor_id, 'Software_Config', 'Device_Type'))
        self.max_pos_unit = float(self.config_manager.get_value(self.motor_id, 'Software_Config', 'Max_Position'))
        self.min_pos_unit = float(self.config_manager.get_value(self.motor_id, 'Software_Config', 'Min_Position'))
        self.max_pos_stp = self.unit_to_steps(self.motor_id, self.max_pos_unit)
        self.min_pos_stp = self.unit_to_steps(self.motor_id, self.min_pos_unit)
        self.unit = self.config_manager.get_value(self.motor_id, 'Software_Config', 'Unit')
        self.joy_axis = int(self.config_manager.get_value(self.motor_id, 'Software_Config', 'Joystick_Axis'))
        self.joy_deadzone = float(self.config_manager.get_value(self.motor_id, 'Software_Config', 'Deadzone'))

        self.spd_pps = int(self.config_manager.get_value(self.motor_id, 'Hardware_Config', 'Max_Speed(pps)'))
        self.acc_rate_ms = int(self.config_manager.get_value(self.motor_id, 'Hardware_Config', 'Acceleration_Rate(ms)'))
        self.dec_rate_ms = int(self.config_manager.get_value(self.motor_id, 'Hardware_Config', 'Deceleration_Rate(ms)'))
        self.start_spd_pps = int(self.config_manager.get_value(self.motor_id, 'Hardware_Config', 'Start_Speed(pps)'))
        self.stop_spd_pps = int(self.config_manager.get_value(self.motor_id, 'Hardware_Config', 'Stop_Speed(pps)'))
        self.backlash_comp = int(self.config_manager.get_value(self.motor_id, 'Hardware_Config', 'Backlash_Compensation'))
        self.phase_current_a = float(self.config_manager.get_value(self.motor_id, 'Hardware_Config', 'Phase_Current(A)'))
        self.current_reduction_pct = int(self.config_manager.get_value(self.motor_id, 'Hardware_Config', 'Current_Reduction(%)'))
        self.micro_stepping = int(self.config_manager.get_value(self.motor_id, 'Hardware_Config', 'Micro_Stepping'))
        self.direction = int(self.config_manager.get_value(self.motor_id, 'Hardware_Config', 'Direction'))

        self.security_pos = self.config_manager.get_security_positions(motor_id)

        self.status = {
            "acr": 0, "ena": 0, "direction": 1, "mcs": 16,
            "ANE": 0, "CHS": 0, "QEI": 0, "QEM": 0, "CM": 0, "AM": 0, "DM": 0,
            "Elock": 0, "CCW": 0, "autoENA": 0,
            "STLIE": 0, "ORGIE": 0, "STPIE": 0, "P4IE": 0,
            "S3IE": 0, "S2IE": 0, "S1IE": 0,
            "accRate": 0, "decRate": 0,
            "maxStartSpeed": 0, "maxStopSpeed": 0,
            "holdingCurrent": 0, "backlash": 0,
            "S34CON": 0, "S12CON": 0, "ATCONH": 0, "ATCONL": 0,
            "sTimeS1": 0, "sTimeS2": 0, "sTimeS3": 0,
            "S1": 0, "S2": 0, "S3": 0, "AnalogIn": 0,
            "sCur": 0, "rCur": 0,
            "sSpd": 0, "rSpd": 0,
            "sDisplacement": 0, 
            "rDisplacement": 0,
            "encoderRes": 0,
            "sEncoder": 0, 
            "rEncoder": 0,
        }

    def handle_status_update(self, update) -> None:
        self.status.update(update)

    def unit_to_steps(self, motor_id: int, unit: float) -> int:
        '''Converts the given mm/degree to steps'''
        encoder: str = self.config_manager.get_value(motor_id, 'Hardware_Info', 'Available_Encoder')
        pos_factor = float(self.config_manager.get_value(motor_id, 'Software_Config', 'Gear_Factor'))

        if encoder:
            steps = int(( unit / (360 * pos_factor) ) * 2000)
        else:
            steps = int(( unit / (360 * pos_factor) ) * 3200)

        return  steps