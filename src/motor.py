from PySide6.QtCore import QObject

class Motor(QObject):
    def __init__(self, controller_id, serial_manager, config_manager=None):
        super().__init__()
        self.device_id = controller_id
        self.serial_manager = serial_manager
        self.config_manager = config_manager
        self.config_manager.check_existing_ini(self.device_id)
        
        self.device_name = self.config_manager.get_value(self.device_id, 'Software_Config', 'Device_Name')
        self.max_pos = self.config_manager.get_value(self.device_id, 'Software_Config', 'Max_Position')
        self.min_pos = self.config_manager.get_value(self.device_id, 'Software_Config', 'Max_Position')
        self.unit = self.config_manager.get_value(self.device_id, 'Software_Config', 'Unit')
        self.spd_pps = self.config_manager.get_value(self.device_id, 'Hardware_Config', 'Max_Speed(pps)')

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