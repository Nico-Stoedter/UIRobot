import configparser 
import os
import sys
import ast

from pop_up import PopUp

class IniManager():

    def __init__(self):
        if getattr(sys, 'frozen', False):
            # Wenn gebündelte EXE, Parent-Ordner von sys.executable
            current_dir = os.path.dirname(sys.executable)
        else:
            # Wenn normales Python-Skript, Parent-Ordner von __file__
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.configs_dir = os.path.join(current_dir, "configs")
        self.pop_up = PopUp()  

    ### Hilfsfunktionen ###

    def get_file_path(self, motor_id: int) -> str:
        '''Finds the file_path for motor_id'''
        filname = f'DevId_{motor_id}.ini'
        file_path = os.path.join(self.configs_dir, filname)

        if not os.path.exists(file_path):
            self.pop_up.show_popup(f"Path for DevId_{motor_id} not found")
            print("[IniManager] File not found:", file_path)
            return
        
        return file_path
        
    ### Function to handle .ini files ###

    def get_value(self, motor_id: int, section: str, name: str) -> str|None:
        file_path = self.get_file_path(motor_id)

        config = configparser.RawConfigParser()
        config.optionxform = str
        config.read(file_path, encoding='utf-8')

        if section not in config:
            print(f"[IniManager] Section [{section}] not found in {file_path}")
            self.pop_up.show_popup(f"Ini File Error: {section} doesn't exist in {file_path}")
            return None

        if name not in config[section]:
            print(f"[IniManager] Key '{name}' not found in section [{section}] in {file_path}")
            self.pop_up.show_popup(f"Ini File Error: {name} not found in {section} {file_path}")
            return None

        return config[section][name]
    
    def get_value_bool(self, motor_id: int, section: str, name: str) -> str|None:
        file_path = self.get_file_path(motor_id)

        config = configparser.RawConfigParser()
        config.optionxform = str
        config.read(file_path, encoding='utf-8')

        if section not in config:
            print(f"[IniManager] Section [{section}] not found in {file_path}")
            self.pop_up.show_popup(f"Ini File Error: {section} doesn't exist in {file_path}")
            return None

        if name not in config[section]:
            print(f"[IniManager] Key '{name}' not found in section [{section}] in {file_path}")
            self.pop_up.show_popup(f"Ini File Error: {name} not found in {section} {file_path}")
            return None
        
        try:
            return config.getboolean(section, name)
        except ValueError:
            print(f"[IniManager] Key '{name}' in section [{section}] is not a valid boolean")
            self.pop_up.show_popup(f"Ini File Error: {name} in {section} is not a boolean in {file_path}")
            return None
    
    def check_existing_ini(self, motor_id: int) -> None:
        """Checks if motor_id has a .ini file"""
        ini_path = os.path.join(self.configs_dir, f'DevId_{motor_id}.ini')
    
        if os.path.isfile(ini_path):
            print(f'{ini_path} exists')
            self.ini_integrity_check(ini_path)
        else:
            print(f'[IniManager] No {ini_path} file exists')
            self.dummyConfig(motor_id)

    def dummyConfig(self, motor_id: int) -> None:
        '''Creates .ini file for motor_id param: Integer: motor_id'''

        config = configparser.RawConfigParser()
        config.optionxform = str

        # Sektion: Soft_Basic
        config["Soft_Basic"] = {
            "Device_Name": f"Axis-{motor_id}",
            "Device_Type": '0',
            "Max_Speed(rpm)": "100",
            "Max_Position": "3600.00",
            "Min_Position": "-3600.00",
            "Position_Factor": "1.00",
            "Position_Unit": "°", 
        }

        # Sektion: Soft_Joys
        config["Soft_Joys"] = {
            "Joystick_Axis": "0",
            "Deadzone": "0.05",
        }

        # Sektion: Soft_Moti
        config["Soft_Moti"] = {
            "Acceleration_Rate(ms)": "1000",
            "Deacceleration_Rate(ms)": "1000",
            "Start_Speed(rpm)": "1",
            "Stop_Speed(rpm)": "1",
            "Backlash_Compensation(p)": "0"
        }

        # Sektion: Hard_Conf
        config["Hard_Conf"] = {
            "Phase_Current(A)": "2.0",
            "Current_Reduction(%)": "50",
            "Micro_Stepping": "16",
            "Direction": "0"
        }

        # Sektion: Hard_Info
        config["Hard_Info"] = {
            "Max_Current(A)": "2.00",
            "Ava_Encoder": "1",
            "Ava_CloseLoop": "1",
            "Ava_AdvMottion": "1",
        }

        # Sektion: Preset_Position
        config["Preset_Position"] = {
            "No": "1",
            "Name1": "Home",
            "Value1": "0"
        }
        # Sektion: Security Position
        config["Security_Positions"] = {
        }
        file_path = os.path.join(self.configs_dir, f"DevId_{motor_id}.ini")
        with open(file_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile, space_around_delimiters=False)

        print(f"[IniManager] .ini for motor {motor_id} created: {file_path}")
    
    def get_preset_positions_from_motor(self, motor_id) -> dict[str, str]:
            file_path = self.get_file_path(motor_id)

            config = configparser.RawConfigParser()
            config.optionxform = str
            config.read(file_path, encoding='utf-8')

            section = config['Preset_Position']
            presets = {}

            for key, value in section.items():
                if key.startswith('Name'):
                    index = int(key[4:])
                    value_key = f"Value{index}"
                    if value_key in section:
                        preset_name = value
                        preset_value = section[value_key]
                        presets[preset_name] = preset_value

            return presets
    
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

    def get_security_pos(self, motor_id) -> dict[int, list[float | str | bool]]:
        file_path = self.get_file_path(motor_id)

        config = configparser.ConfigParser()
        config.optionxform = str  # Groß-/Kleinschreibung beibehalten
        config.read(file_path, encoding='utf-8')

        if 'Security_Positions' not in config:
            return {}
        
        section = config['Security_Positions']
        presets = {}

        for key, value in section.items():
            if key.startswith('Value'):
                index = int(key[5:])  # extracts index from key, e.g. Value1 -> 1
                text_key = f"Text{index}"
                direction_key = f"Direction{index}"

                if text_key in section and direction_key in section:
                    try:
                        security_value = float(value)
                        security_text = section[text_key]
                        security_direction = config.getboolean('Security_Positions', direction_key)
                        presets[index] = [security_value, security_text, security_direction]
                    except ValueError:
                        self.pop_up.show_popup("Ini File Error: Value in [Security_Position] might be wrong")
                        print(f"Wrong Value in {key}: {value}")
                        return {}
                else:
                    self.pop_up.show_popup("Ini File Error: [Security_Position] not correct formatted")
                    return {}

        return presets
    
    def ini_integrity_check(self, path: str):
        """
        Prüft, ob Werte im INI-File die richtigen Datentypen haben.
        Gibt eine Liste von Fehlern zurück.
        """
        config = configparser.ConfigParser()
        config.optionxform = str  # Groß-/Kleinschreibung beibehalten
        config.read(path, encoding="utf-8")

        # Erwartete Datentypen je Sektion und Schlüssel
        expected_types = {
            "Soft_Basic": {
                "Device_Name": str,
                "Device_Type": int,
                "Max_Speed(rpm)": float,
                "Max_Position": float,
                "Min_Position": float,
                "Position_Factor": float,
                "Position_Unit": str,
            },
            "Soft_Joys": {
                "Joystick_Axis": int,
                "Deadzone": float,
            },
            "Soft_Moti": {
                "Acceleration_Rate(ms)": float,
                "Deacceleration_Rate(ms)": float,
                "Start_Speed(rpm)": float,
                "Stop_Speed(rpm)": float,
                "Backlash_Compensation(p)": float,
            },
            "Hard_Conf": {
                "Phase_Current(A)": float,
                "Current_Reduction(%)": float,
                "Micro_Stepping": int,
                "Direction": int,
            },
            "Hard_Info": {
                "Max_Current(A)": float,
                "Ava_Encoder": int,
                "Ava_CloseLoop": int,
                "Ava_AdvMottion": int,
            },
            # Preset_Position and Security_Positions will be checked on the spot, because they vary from .ini to .ini 
        }

        errors = []

        # Section check
        for section in expected_types:
            if section not in config:
                errors.append(f"Fehlende Sektion: [{section}]")
                continue

            # Key + Datatype check
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
                    elif expected_type == str:
                        pass  # Strings brauchen keine Konvertierung
                    else:
                        errors.append(f"Unbekannter Typ für {section}.{key}")
                except ValueError:
                    errors.append(f"Falsches Format: {section}.{key}='{value}' erwartet {expected_type.__name__}")
                except Exception:
                    errors.append(f"Unbekanter .ini Fehler. Überprüfe die .ini nochmal")

        for error in errors:
            self.pop_up.show_popup(f"{error}")

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

if __name__ == '__main__':
    ini_manager = IniManager()
    boxes = ini_manager.get_security_zones()
    print(boxes)


