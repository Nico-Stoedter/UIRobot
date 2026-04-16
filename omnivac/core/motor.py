from omnivac.config.ini_manager import IniManager

from typing import TYPE_CHECKING, Dict

class Motor():
    def __init__(self, id, status):
        self.ini_manager = IniManager() 
        self._id: int = id
        self.cur_rotation_dir = None

        self._dev_type = self.ini_manager.get_value(id, 'Soft_Basic', 'Device_Type') # ( 0 - Linear, 1 - Rotation, 2 - Rotation 360, 3 - Rotation 360 Right, 4 - Rotation 360 Left )
        self._max_speed = self.ini_manager.get_value(id, 'Soft_Basic', 'Max_Speed(rpm)')
        self._max_position = self.ini_manager.get_value(id, 'Soft_Basic', 'Max_Position')
        self._min_position = self.ini_manager.get_value(id, 'Soft_Basic', 'Min_Position')
        self._position_factor = self.ini_manager.get_value(id, 'Soft_Basic', 'Position_Factor')
        self._position_unit = self.ini_manager.get_value(id, 'Soft_Basic', 'Position_Unit')

        self._joystick_axis = self.ini_manager.get_value(id, 'Soft_Joys', 'Joystick_Axis')
        self._deadzone = self.ini_manager.get_value(id, 'Soft_Joys', 'Deadzone')

        self._encoder: bool = self.ini_manager.get_value_bool(id, 'Hard_Info', 'Ava_Encoder')

        if id == 71:
            self._r3_org_pos: int = self.ini_manager.get_value(id, "R3_Values", "ORG")

        self.security_settings: dict[int, list[float|str|bool]] = self.ini_manager.get_security_pos(id)

        self.motor_status={"ava_encoder": self.encoder, "acr": 0, "ena": 0, "direction": 1, "mcs": 16, 
              "ANE": 0, "CHS": 0, "QEI": 0, "QEM": 0, "CM": 0, "AM": 0, "DM": 0,
              "Elock": 0, "CCW": 0, "autoENA": 0,
              "STLIE": 0, "ORGIE": 0, "STPIE": 0, "P4IE": 0,
              "S3IE": 0, "S2IE": 0, "S1IE": 0,
              "accRate": 0, "decRate": 0,
              "maxStartSpeed": 0, "maxStopSpeed": 0,
              "holdingCurrent": 0, "backlash": 0,
              "S34CON": 0, "S12CON": 0, "ATCONH": 0, "ATCONL": 0,
              "sTimeS1": 0,"sTimeS2": 0,"sTimeS3": 0,
              "S1": 0,"S2": 0,"S3": 0,"AnalogIn": 0,
              "sCur": 0, "rCur": 0, 
              "sSpd": 0, "rSpd": 0,
              "sDisplacement": 0, "rDisplacement": 0,
              "encoderRes": 0,
              "sEncoder": 0, "rEncoder": 0
              }
        
        self.motor_status.update(status) #updates the first values after initialization

        self.security_pos_true = self.security_values_true = {
            k: v
            for k, v in self.ini_manager.get_security_pos(id).items()
            if v[2] is True
        }
        self.security_pos_false = {
            k: v
            for k, v in self.ini_manager.get_security_pos(id).items()
            if v[2] is False
        }

    def __repr__(self) -> str: # Nur fürs debuggen hilfreich
        return f'MotorID:{self._id}'
    
    @property
    def id(self) -> int:
        return self._id
    
    @property
    def dev_type(self) -> int:
        return int(self._dev_type)
    
    @property
    def max_speed(self) -> float:
        return float(self._max_speed)
    
    @property
    def max_position(self) -> float:
        return float(self._max_position)
    
    @property
    def min_position(self) -> float:
        return float(self._min_position)
    
    @property
    def position_factor(self) -> float:
        return float(self._position_factor)
    
    @property
    def position_unit(self) -> str:
        return self._position_unit
    
    @property
    def joystick_axis(self) -> int:
        return int(self._joystick_axis)
    
    @property
    def deadzone(self) -> float:
        return float(self._deadzone)
    
    @property
    def encoder(self) -> bool:
        return self._encoder
    
    # Special property only for motor ID 71
    @property
    def r3_org_pos(self) -> int | None:
        return self._r3_org_pos

    @r3_org_pos.setter
    def r3_org_pos(self, new_r3_org: int):
        if self._id != 71:
            raise AttributeError("r3_org_pos is only valid for motor ID 71.")
        self._r3_org_pos = int(new_r3_org)
    
    @dev_type.setter
    def dev_type(self, new_type) -> None:
        self._dev_type = new_type

    @min_position.setter
    def min_position(self, new_pos) -> None:
        self._min_position = new_pos

    @max_position.setter
    def max_position(self, new_pos) -> None:
        self._max_position = new_pos
    
    # vielleicht richtigen getter machen wenn möglich 
    def get_motor_pos(self) -> int:
        '''Gives motor position in steps'''
        return self.motor_status.get("rEncoder")

    # richtigen setter machen
    def update_status(self, status: Dict[str, int]):
        self.motor_status.update(status)
