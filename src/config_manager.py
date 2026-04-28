from PySide6.QtCore import QObject ,Signal

import configparser 
import os
import sys
import ast

from src.ui.pop_up import PopUp

class ConfigManager(QObject):

    key_error = Signal(str)
    integrity_error = Signal(list)

    def __init__(self):
        super().__init__()
        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable) #Directory as .exe
        else:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Directory as .py

        self.configs_dir = os.path.join(current_dir, "configs")
        self.pop_up = PopUp()

    def get_file_path(self, motor_id: int) -> str:
        '''Finds the file_path for motor_id'''
        filname = f'DevId_{motor_id}.ini'
        file_path = os.path.join(self.configs_dir, filname)

        if not os.path.exists(file_path):
            self.pop_up.show_popup(f"Path for DevId_{motor_id} not found")
            print("[IniManager] File not found:", file_path)
            return
        
        return file_path

    def get_value(self, motor_id: int, section: str, key: str) -> str|None:
        file_path = self.get_file_path(motor_id)

        config = configparser.RawConfigParser()
        config.optionxform = str
        config.read(file_path, encoding='utf-8')

        try:
            return config[section][key]
        except KeyError as k:
            missing_key = str(k)
            self.key_error.emit(missing_key)
        
    def get_preset_positions(self, motor_id) -> dict[str, str]:
        '''Reads the Preset Positions from a .ini and returns a dict[Name, Value]'''
        file_path = self.get_file_path(motor_id)

        config = configparser.RawConfigParser()
        config.optionxform = str
        config.read(file_path, encoding='utf-8')

        try:
            presets = dict(config["Preset_Position"])
        except KeyError as k:
            missing_key = str(k)
            self.key_error.emit(missing_key)
            return {"Error": 0}

        return presets
    
    def get_security_positions(self, motor_id):
        file_path = self.get_file_path(motor_id)

        config = configparser.RawConfigParser()
        config.optionxform = str
        config.read(file_path, encoding='utf-8')

        dict = {}

        for section in config.sections():
            if section.startswith("Security_Positions.Check"):
                value = config.getfloat(section, "Value")
                text  = config.get(section, "Text")
                direction = config.getboolean(section, "Direction")

                dict[(value, direction)] = text

        return dict  

    def get_security_zones(self) -> dict[str, tuple]:
        filname = f'Security_Zones.ini'
        file_path = os.path.join(self.configs_dir, filname)

        if not os.path.exists(file_path):
            self.pop_up.show_popup(f"Path for Security_Zones not found")
            print("[IniManager] File not found:", file_path)
            return
        
        config = configparser.RawConfigParser()
        config.optionxform = str
        config.read(file_path, encoding='utf-8')

        boxes = {}

        for key, value in config["Box"].items():
            boxes[key] = ast.literal_eval(value)

        return boxes    
    
    def check_existing_ini(self, motor_id: int) -> None:
        """Checks if motor_id has a .ini file"""
        ini_path = os.path.join(self.configs_dir, f'DevId_{motor_id}.ini')
    
        if os.path.isfile(ini_path):
            print(f'{ini_path} exists')
            self.ini_integrity_check(motor_id)
        else:
            print(f'[IniManager] No {ini_path} file exists')
            self.dummyConfig(motor_id)

    def dummyConfig(self, motor_id: int) -> None:
        '''Creates .ini file for motor_id param: Integer: motor_id'''

        config = configparser.RawConfigParser()
        config.optionxform = str

        # Sektion: Soft_Basic
        config["Software_Config"] = {
            "Device_Name": f"Axis-{motor_id}",
            "Device_Type": "0",
            "Max_Position": "3600.00",
            "Min_Position": "-3600.00",
            "Gear_Factor": "1",
            "Unit": "°",
            "Joystick_Axis": "1",
            "Deadzone": "0.05",
        }

        config["Hardware_Config"] = {
            "Max_Speed(pps)": "30",
            "Acceleration_Rate(ms)": "50",
            "Deceleration_Rate(ms)": "50",
            "Start_Speed(pps)": "1",
            "Stop_Speed(pps)": "1",
            "Backlash_Compensation": "0",
            "Phase_Current(A)": "2.0",
            "Current_Reduction(%)": "50",
            "Micro_Stepping": "16",
            "Direction": "0",
        }

        config["Hardware_Info"] = {
            "Max_Current(A)": "2.00",
            "Available_Encoder": "1",
            "Available_ClosedLoop": "1",
            "Available_AdvMotion": "1"
        }

        config["Preset_Postion"] = {
            "Home": "0"
        }

        config["Security_Positions"] = {
        }
        file_path = os.path.join(self.configs_dir, f"DevId_{motor_id}.ini")
        with open(file_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile, space_around_delimiters=False)

        print(f"[IniManager] .ini for motor {motor_id} created: {file_path}")
    
    def update_org_value(self, motor_id: int, new_value: int) -> None:
        """Schreibt einen int-Wert in das Feld ORG in [R3_Values]"""
        file_path = self.get_file_path(motor_id)

        # ini neu einlesen
        config = configparser.RawConfigParser()
        config.optionxform = str
        config.read(file_path, encoding='utf-8')

        if "R3_Values" not in config:
            config["R3_Values"] = {}

        config["R3_Values"]["ORG"] = str(new_value)

        # zurückschreiben
        with open(file_path, "w", encoding="utf-8") as configfile:
            config.write(configfile, space_around_delimiters=False)

        print(f"[IniManager] ORG updated to {new_value} in {file_path}")
    
    def ini_integrity_check(self, motor_id: int) -> None:
        """
        Checks if available .ini is in right condition
        emits signal if not
        """
        ini_path = os.path.join(self.configs_dir, f'DevId_{motor_id}.ini')

        config = configparser.ConfigParser()
        config.optionxform = str 
        config.read(ini_path, encoding="utf-8")

        expected_types = {
            "Software_Config": {
                "Device_Name": str,
                "Device_Type": int,
                "Max_Position": float,
                "Min_Position": float,
                "Gear_Factor": float,
                "Unit": str,
                "Joystick_Axis": int,
                "Deadzone": float,
            },
            "Hardware_Config": {
                "Max_Speed(pps)": int,
                "Acceleration_Rate(ms)": float,
                "Deceleration_Rate(ms)": float,
                "Start_Speed(pps)": float,
                "Stop_Speed(pps)": float,
                "Backlash_Compensation": float,
                "Phase_Current(A)": float,
                "Current_Reduction(%)": float,
                "Micro_Stepping": int,
                "Direction": bool,
            },
            "Hardware_Info": {
                "Max_Current(A)": float,
                "Available_Encoder": bool,
                "Available_ClosedLoop": bool,
                "Available_AdvMotion": bool,
            },
            # Preset_Position and Security_Positions will be checked on the spot, because they vary from .ini to .ini 
        }

        errors = []

        for section in expected_types:
            if section not in config:
                errors.append(f"Fehlende Sektion: [{section}]")
                continue

            for key, expected_type in expected_types[section].items():
                if key not in config[section]:
                    errors.append(f"Fehlender Schlüssel: {section}.{key}")
                    continue

                value = config[section][key]

                try:
                    if expected_type == int:
                        int(value)
                    elif expected_type == float:
                        float(value)
                    elif expected_type == bool:
                        value = self.parse_bool(value)
                    elif expected_type == str:
                        pass  # Strings brauchen keine Konvertierung
                    else:
                        errors.append(f"Unbekannter Typ für {section}.{key}")
                except ValueError:
                    errors.append(f"Wrong Type: DevId_{motor_id} {section}.{key}='{value}' expected {expected_type.__name__}")
                except Exception:
                    errors.append(f"Unbekanter .ini Fehler. Überprüfe die .ini nochmal")

        if errors != []:
            self.integrity_error.emit(errors)
    
    def parse_bool(self, value: str) -> bool:
        value = value.strip().lower()
        if value in ("1", "true"):
            return True
        elif value in ("0", "false"):
            return False
        else:
            raise ValueError(f"cannot convert '{value}' to bool; expected 0/1 or True/False")

# --- Zum Testen ---
if __name__ == '__main__':
    print("cool")
